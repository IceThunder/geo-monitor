"""
Tests for alert management endpoints: /api/alerts/*

Covers:
- GET    /api/alerts              - list alerts (with filtering)
- PUT    /api/alerts/{id}/read    - mark single alert as read
- PUT    /api/alerts/read-all     - mark all alerts as read
- GET    /api/alerts/unread-count - get unread alert count
- POST   /api/alerts/webhooks/test - test webhook connectivity

The alerts router uses ``get_current_tenant_id`` from ``app.core.security``
which chains through ``get_current_user`` (requires JWT in non-development
mode).  For simplicity we override the ``get_current_tenant_id`` dependency
to return the test tenant_id directly, side-stepping the full auth chain.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, AsyncMock

import pytest
from sqlalchemy import text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _insert_alert(db, tenant_id, **overrides):
    """Insert an AlertRecord row directly and return its id."""
    alert_id = overrides.get("id", str(uuid.uuid4()))
    task_id = overrides.get("task_id", None)
    alert_type = overrides.get("alert_type", "accuracy_low")
    alert_message = overrides.get("alert_message", "Accuracy dropped below threshold")
    metric_name = overrides.get("metric_name", "accuracy_score")
    metric_value = overrides.get("metric_value", 3.5)
    threshold_value = overrides.get("threshold_value", 6.0)
    is_read = overrides.get("is_read", False)
    is_resolved = overrides.get("is_resolved", False)
    now = overrides.get("created_at", datetime.utcnow().isoformat())

    db.execute(text(
        "INSERT INTO alert_records "
        "(id, tenant_id, task_id, alert_type, alert_message, "
        " metric_name, metric_value, threshold_value, is_read, is_resolved, created_at) "
        "VALUES (:id, :tid, :task_id, :atype, :amsg, :mname, :mval, :tval, :is_read, :is_resolved, :ca)"
    ), {
        "id": alert_id,
        "tid": tenant_id,
        "task_id": task_id,
        "atype": alert_type,
        "amsg": alert_message,
        "mname": metric_name,
        "mval": metric_value,
        "tval": threshold_value,
        "is_read": is_read,
        "is_resolved": is_resolved,
        "ca": now,
    })
    db.commit()
    return alert_id


def _insert_task(db, tenant_id, **overrides):
    """Insert a MonitorTask row and return its id."""
    task_id = overrides.get("id", str(uuid.uuid4()))
    name = overrides.get("name", "Test Task")
    now = datetime.utcnow().isoformat()

    db.execute(text(
        "INSERT INTO monitor_tasks (id, tenant_id, name, schedule_cron, is_active, created_at, updated_at) "
        "VALUES (:id, :tid, :name, :cron, 1, :ca, :ua)"
    ), {
        "id": task_id,
        "tid": tenant_id,
        "name": name,
        "cron": "0 0 * * *",
        "ca": now,
        "ua": now,
    })
    db.commit()
    return task_id


# ---------------------------------------------------------------------------
# Fixture: client with get_current_tenant_id overridden
# ---------------------------------------------------------------------------

@pytest.fixture()
def alerts_client(db, test_user):
    """
    A TestClient where ``get_current_tenant_id`` is overridden to return
    the test_user's tenant_id without requiring a real JWT.  This avoids
    the ``get_current_user`` -> ``OptionalBearer`` -> ``TenantMember`` chain
    which is not the focus of alerts tests.
    """
    from app.main import app
    from app.models.database import get_db
    from app.core.security import get_current_tenant_id

    tenant_id = test_user["tenant_id"]

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    def _override_get_current_tenant_id():
        return tenant_id

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_tenant_id] = _override_get_current_tenant_id

    with patch("app.main.init_db"), \
         patch("app.main.close_db"), \
         patch("app.main.init_redis"), \
         patch("app.main.close_redis"):
        from fastapi.testclient import TestClient
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    app.dependency_overrides.clear()


# ===========================================================================
# GET /api/alerts  -- list alerts
# ===========================================================================

class TestListAlerts:
    """Tests for the list-alerts endpoint."""

    def test_list_alerts_empty(self, alerts_client, db, test_user):
        """When no alerts exist, returns empty data and zero unread."""
        resp = alerts_client.get("/api/alerts")

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["data"] == []
        assert body["unread_count"] == 0

    def test_list_alerts_returns_data(self, alerts_client, db, test_user):
        """Inserted alerts appear in the response."""
        tid = test_user["tenant_id"]
        _insert_alert(db, tid, alert_type="accuracy_low", alert_message="Low accuracy A")
        _insert_alert(db, tid, alert_type="sentiment_low", alert_message="Low sentiment B")

        resp = alerts_client.get("/api/alerts")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 2
        assert body["unread_count"] == 2
        messages = {a["alert_message"] for a in body["data"]}
        assert "Low accuracy A" in messages
        assert "Low sentiment B" in messages

    def test_list_alerts_filter_by_is_read(self, alerts_client, db, test_user):
        """Filtering by is_read=true only returns read alerts."""
        tid = test_user["tenant_id"]
        _insert_alert(db, tid, is_read=False, alert_message="Unread alert")
        _insert_alert(db, tid, is_read=True, alert_message="Read alert")

        # Only unread
        resp = alerts_client.get("/api/alerts?is_read=false")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["alert_message"] == "Unread alert"

        # Only read
        resp = alerts_client.get("/api/alerts?is_read=true")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["alert_message"] == "Read alert"

    def test_list_alerts_filter_by_alert_type(self, alerts_client, db, test_user):
        """Filtering by alert_type narrows results."""
        tid = test_user["tenant_id"]
        _insert_alert(db, tid, alert_type="accuracy_low")
        _insert_alert(db, tid, alert_type="sov_low")
        _insert_alert(db, tid, alert_type="accuracy_low")

        resp = alerts_client.get("/api/alerts?alert_type=sov_low")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["alert_type"] == "sov_low"

    def test_list_alerts_pagination(self, alerts_client, db, test_user):
        """Limit and offset control pagination."""
        tid = test_user["tenant_id"]
        for i in range(5):
            _insert_alert(db, tid, alert_message=f"Alert {i}")

        resp = alerts_client.get("/api/alerts?limit=2&offset=0")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

        resp = alerts_client.get("/api/alerts?limit=2&offset=3")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_list_alerts_tenant_isolation(self, alerts_client, db, test_user):
        """Alerts from other tenants are not visible."""
        other_tenant_id = str(uuid.uuid4())
        tid = test_user["tenant_id"]

        _insert_alert(db, tid, alert_message="My alert")
        _insert_alert(db, other_tenant_id, alert_message="Other tenant alert")

        resp = alerts_client.get("/api/alerts")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["alert_message"] == "My alert"

    def test_list_alerts_includes_task_name(self, alerts_client, db, test_user):
        """When alert has a task_id, the response includes task_name."""
        tid = test_user["tenant_id"]
        task_id = _insert_task(db, tid, name="Brand Monitor Alpha")
        _insert_alert(db, tid, task_id=task_id, alert_message="With task")

        resp = alerts_client.get("/api/alerts")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["task_name"] == "Brand Monitor Alpha"
        assert data[0]["task_id"] == task_id

    def test_list_alerts_no_task_name_when_no_task(self, alerts_client, db, test_user):
        """When alert has no task_id, task_name is null."""
        tid = test_user["tenant_id"]
        _insert_alert(db, tid, task_id=None, alert_message="No task alert")

        resp = alerts_client.get("/api/alerts")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["task_name"] is None

    def test_list_alerts_response_fields(self, alerts_client, db, test_user):
        """Every AlertResponse field is present and correctly typed."""
        tid = test_user["tenant_id"]
        alert_id = _insert_alert(
            db, tid,
            alert_type="accuracy_low",
            alert_message="Score below threshold",
            metric_name="accuracy_score",
            metric_value=3.5,
            threshold_value=6.0,
            is_read=False,
            is_resolved=False,
        )

        resp = alerts_client.get("/api/alerts")
        assert resp.status_code == 200

        item = resp.json()["data"][0]
        assert item["id"] == alert_id
        assert item["tenant_id"] == tid
        assert item["alert_type"] == "accuracy_low"
        assert item["alert_message"] == "Score below threshold"
        assert item["metric_name"] == "accuracy_score"
        assert isinstance(item["metric_value"], (int, float))
        assert isinstance(item["threshold_value"], (int, float))
        assert item["is_read"] is False
        assert item["is_resolved"] is False
        assert "created_at" in item


# ===========================================================================
# PUT /api/alerts/{id}/read  -- mark single alert as read
# ===========================================================================

class TestMarkAlertRead:
    """Tests for the mark-alert-read endpoint."""

    def test_mark_alert_read_success(self, alerts_client, db, test_user):
        """Marking an existing unread alert returns success=True."""
        tid = test_user["tenant_id"]
        alert_id = _insert_alert(db, tid, is_read=False)

        resp = alerts_client.put(f"/api/alerts/{alert_id}/read")

        assert resp.status_code == 200, resp.text
        assert resp.json()["success"] is True

        # Verify the alert is now read
        list_resp = alerts_client.get("/api/alerts?is_read=true")
        assert any(a["id"] == alert_id for a in list_resp.json()["data"])

    def test_mark_alert_read_not_found(self, alerts_client, db, test_user):
        """Marking a non-existent alert returns success=False."""
        fake_id = str(uuid.uuid4())
        resp = alerts_client.put(f"/api/alerts/{fake_id}/read")

        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_mark_alert_read_other_tenant(self, alerts_client, db, test_user):
        """Cannot mark an alert belonging to another tenant."""
        other_tenant_id = str(uuid.uuid4())
        alert_id = _insert_alert(db, other_tenant_id)

        resp = alerts_client.put(f"/api/alerts/{alert_id}/read")

        # Should return success=False because tenant filter excludes it
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_mark_already_read_alert(self, alerts_client, db, test_user):
        """Marking an already-read alert still returns success=True."""
        tid = test_user["tenant_id"]
        alert_id = _insert_alert(db, tid, is_read=True)

        resp = alerts_client.put(f"/api/alerts/{alert_id}/read")

        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_mark_read_decrements_unread_count(self, alerts_client, db, test_user):
        """After marking an alert as read, unread_count drops by one."""
        tid = test_user["tenant_id"]
        alert_id = _insert_alert(db, tid, is_read=False)
        _insert_alert(db, tid, is_read=False)

        # Before: 2 unread
        resp = alerts_client.get("/api/alerts")
        assert resp.json()["unread_count"] == 2

        # Mark one as read
        alerts_client.put(f"/api/alerts/{alert_id}/read")

        # After: 1 unread
        resp = alerts_client.get("/api/alerts")
        assert resp.json()["unread_count"] == 1


# ===========================================================================
# PUT /api/alerts/read-all  -- mark all alerts as read
# ===========================================================================

class TestMarkAllAlertsRead:
    """Tests for the mark-all-alerts-read endpoint."""

    def test_mark_all_read_success(self, alerts_client, db, test_user):
        """Marking all alerts as read sets every alert's is_read to True."""
        tid = test_user["tenant_id"]
        _insert_alert(db, tid, is_read=False)
        _insert_alert(db, tid, is_read=False)
        _insert_alert(db, tid, is_read=True)

        resp = alerts_client.put("/api/alerts/read-all")

        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # All should now be read
        list_resp = alerts_client.get("/api/alerts?is_read=false")
        assert len(list_resp.json()["data"]) == 0

    def test_mark_all_read_empty(self, alerts_client, db, test_user):
        """Marking all read when no alerts exist still returns success."""
        resp = alerts_client.put("/api/alerts/read-all")

        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_mark_all_read_tenant_isolation(self, alerts_client, db, test_user):
        """mark-all-read only affects the current tenant's alerts."""
        tid = test_user["tenant_id"]
        other_tid = str(uuid.uuid4())
        _insert_alert(db, tid, is_read=False, alert_message="Mine")
        other_alert_id = _insert_alert(db, other_tid, is_read=False, alert_message="Other")

        alerts_client.put("/api/alerts/read-all")

        # Other tenant's alert should still be unread
        result = db.execute(text(
            "SELECT is_read FROM alert_records WHERE id = :id"
        ), {"id": other_alert_id})
        row = result.fetchone()
        assert row is not None
        assert row[0] == 0  # SQLite: 0 = False


# ===========================================================================
# GET /api/alerts/unread-count  -- get unread alert count
# ===========================================================================

class TestUnreadCount:
    """Tests for the unread-count endpoint."""

    def test_unread_count_zero(self, alerts_client, db, test_user):
        """Returns zero when no alerts exist."""
        resp = alerts_client.get("/api/alerts/unread-count")

        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 0

    def test_unread_count_accurate(self, alerts_client, db, test_user):
        """Returns correct count of unread alerts."""
        tid = test_user["tenant_id"]
        _insert_alert(db, tid, is_read=False)
        _insert_alert(db, tid, is_read=False)
        _insert_alert(db, tid, is_read=True)

        resp = alerts_client.get("/api/alerts/unread-count")

        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 2

    def test_unread_count_tenant_isolation(self, alerts_client, db, test_user):
        """Only counts unread alerts for the current tenant."""
        tid = test_user["tenant_id"]
        other_tid = str(uuid.uuid4())
        _insert_alert(db, tid, is_read=False)
        _insert_alert(db, other_tid, is_read=False)

        resp = alerts_client.get("/api/alerts/unread-count")

        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 1


# ===========================================================================
# POST /api/alerts/webhooks/test  -- test webhook connectivity
# ===========================================================================

class TestWebhookTest:
    """Tests for the webhook test endpoint."""

    @patch("app.api.alerts.test_webhook", new_callable=AsyncMock)
    def test_webhook_success(self, mock_test_webhook, alerts_client):
        """Successful webhook test returns success=True with timing."""
        mock_test_webhook.return_value = (True, 150, 200)

        resp = alerts_client.post("/api/alerts/webhooks/test", json={
            "webhook_url": "https://hooks.example.com/webhook",
        })

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["response_time_ms"] == 150
        assert body["response_status"] == 200
        mock_test_webhook.assert_called_once_with("https://hooks.example.com/webhook")

    @patch("app.api.alerts.test_webhook", new_callable=AsyncMock)
    def test_webhook_failure(self, mock_test_webhook, alerts_client):
        """Failed webhook test returns success=False."""
        mock_test_webhook.return_value = (False, 5000, None)

        resp = alerts_client.post("/api/alerts/webhooks/test", json={
            "webhook_url": "https://unreachable.example.com/hook",
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["response_time_ms"] == 5000
        assert body["response_status"] is None

    @patch("app.api.alerts.test_webhook", new_callable=AsyncMock)
    def test_webhook_server_error(self, mock_test_webhook, alerts_client):
        """Webhook returning 5xx is reported as failure."""
        mock_test_webhook.return_value = (False, 300, 500)

        resp = alerts_client.post("/api/alerts/webhooks/test", json={
            "webhook_url": "https://broken.example.com/hook",
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["response_status"] == 500

    def test_webhook_missing_url(self, alerts_client):
        """Omitting webhook_url returns 422 validation error."""
        resp = alerts_client.post("/api/alerts/webhooks/test", json={})

        assert resp.status_code == 422
