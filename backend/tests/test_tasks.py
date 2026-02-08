"""
Tests for task CRUD endpoints: /api/tasks/*

Covers:
- POST   /api/tasks            - create task
- GET    /api/tasks            - list tasks
- GET    /api/tasks/{id}       - get single task
- PUT    /api/tasks/{id}       - update task
- DELETE /api/tasks/{id}       - delete task
- POST   /api/tasks/{id}/trigger - trigger task run
"""
import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import text


# ---------------------------------------------------------------------------
# Helper: create a task via the API and return the response data
# ---------------------------------------------------------------------------

def _create_task(client, auth_headers, **overrides):
    """Create a task through the API. Returns the response JSON."""
    payload = {
        "name": overrides.get("name", "Test Monitor Task"),
        "description": overrides.get("description", "A test task description"),
        "schedule_cron": overrides.get("schedule_cron", "0 0 * * *"),
        "models": overrides.get("models", ["openai/gpt-4o", "anthropic/claude-3-sonnet"]),
        "keywords": overrides.get("keywords", ["brand monitoring", "AI search"]),
    }
    resp = client.post("/api/tasks", json=payload, headers=auth_headers)
    return resp


# ---------------------------------------------------------------------------
# POST /api/tasks
# ---------------------------------------------------------------------------

class TestCreateTask:
    """Task creation endpoint tests."""

    def test_create_task_success(self, client, db, test_user, auth_headers):
        """Creating a task with valid data returns 200 and task details."""
        resp = _create_task(client, auth_headers)

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["name"] == "Test Monitor Task"
        assert data["schedule_cron"] == "0 0 * * *"
        assert data["is_active"] is True
        assert "openai/gpt-4o" in data["models"]
        assert "brand monitoring" in data["keywords"]
        assert data["tenant_id"] == test_user["tenant_id"]

    def test_create_task_without_auth(self, client):
        """Creating a task without authentication returns 401/403."""
        resp = client.post("/api/tasks", json={
            "name": "Unauthorized Task",
            "models": ["openai/gpt-4o"],
            "keywords": ["test"],
        })
        assert resp.status_code in (401, 403)

    def test_create_task_missing_fields(self, client, db, test_user, auth_headers):
        """Creating a task without required fields returns 422."""
        resp = client.post("/api/tasks", json={
            "name": "Incomplete Task",
            # missing models and keywords
        }, headers=auth_headers)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/tasks
# ---------------------------------------------------------------------------

class TestListTasks:
    """Task listing endpoint tests."""

    def test_list_tasks_empty(self, client, db, test_user, auth_headers):
        """Listing tasks when none exist returns empty data array."""
        resp = client.get("/api/tasks", headers=auth_headers)

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["data"] == []
        assert data["total"] == 0

    def test_list_tasks_with_data(self, client, db, test_user, auth_headers):
        """Listing tasks returns the tasks we created."""
        # Create two tasks
        _create_task(client, auth_headers, name="Task One")
        _create_task(client, auth_headers, name="Task Two")

        resp = client.get("/api/tasks", headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        names = [t["name"] for t in data["data"]]
        assert "Task One" in names
        assert "Task Two" in names

    def test_list_tasks_search_filter(self, client, db, test_user, auth_headers):
        """Search query parameter filters tasks by name."""
        _create_task(client, auth_headers, name="Alpha Monitor")
        _create_task(client, auth_headers, name="Beta Monitor")

        resp = client.get("/api/tasks?search=Alpha", headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["data"][0]["name"] == "Alpha Monitor"

    def test_list_tasks_pagination(self, client, db, test_user, auth_headers):
        """Pagination parameters work correctly."""
        for i in range(5):
            _create_task(client, auth_headers, name=f"Paginated {i}")

        resp = client.get("/api/tasks?page=1&limit=2", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 2
        assert data["total"] == 5


# ---------------------------------------------------------------------------
# GET /api/tasks/{id}
# ---------------------------------------------------------------------------

class TestGetTask:
    """Single task retrieval tests."""

    def test_get_task_success(self, client, db, test_user, auth_headers):
        """Retrieving an existing task returns its full details."""
        create_resp = _create_task(client, auth_headers)
        task_id = create_resp.json()["id"]

        resp = client.get(f"/api/tasks/{task_id}", headers=auth_headers)

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == task_id
        assert data["name"] == "Test Monitor Task"
        assert len(data["models"]) == 2
        assert len(data["keywords"]) == 2

    def test_get_task_not_found(self, client, db, test_user, auth_headers):
        """Retrieving a non-existent task returns 404."""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/tasks/{fake_id}", headers=auth_headers)

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/tasks/{id}
# ---------------------------------------------------------------------------

class TestUpdateTask:
    """Task update endpoint tests."""

    def test_update_task_name(self, client, db, test_user, auth_headers):
        """Updating a task's name persists the change."""
        create_resp = _create_task(client, auth_headers)
        task_id = create_resp.json()["id"]

        resp = client.put(f"/api/tasks/{task_id}", json={
            "name": "Updated Task Name",
        }, headers=auth_headers)

        assert resp.status_code == 200, resp.text
        assert resp.json()["name"] == "Updated Task Name"

    def test_update_task_keywords(self, client, db, test_user, auth_headers):
        """Updating keywords replaces the existing set."""
        create_resp = _create_task(client, auth_headers)
        task_id = create_resp.json()["id"]

        resp = client.put(f"/api/tasks/{task_id}", json={
            "keywords": ["new keyword one", "new keyword two"],
        }, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert set(data["keywords"]) == {"new keyword one", "new keyword two"}

    def test_update_task_models(self, client, db, test_user, auth_headers):
        """Updating models replaces the existing set."""
        create_resp = _create_task(client, auth_headers)
        task_id = create_resp.json()["id"]

        resp = client.put(f"/api/tasks/{task_id}", json={
            "models": ["google/gemini-pro"],
        }, headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json()["models"] == ["google/gemini-pro"]

    def test_update_task_not_found(self, client, db, test_user, auth_headers):
        """Updating a non-existent task returns 404."""
        fake_id = str(uuid.uuid4())
        resp = client.put(f"/api/tasks/{fake_id}", json={
            "name": "Ghost",
        }, headers=auth_headers)

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/tasks/{id}
# ---------------------------------------------------------------------------

class TestDeleteTask:
    """Task deletion endpoint tests."""

    def test_delete_task_success(self, client, db, test_user, auth_headers):
        """Deleting an existing task returns success and removes it."""
        create_resp = _create_task(client, auth_headers)
        task_id = create_resp.json()["id"]

        resp = client.delete(f"/api/tasks/{task_id}", headers=auth_headers)

        assert resp.status_code == 200, resp.text

        # Verify task no longer retrievable
        get_resp = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_task_not_found(self, client, db, test_user, auth_headers):
        """Deleting a non-existent task returns 404."""
        fake_id = str(uuid.uuid4())
        resp = client.delete(f"/api/tasks/{fake_id}", headers=auth_headers)

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/tasks/{id}/trigger
# ---------------------------------------------------------------------------

class TestTriggerTask:
    """Task trigger endpoint tests."""

    @patch("app.api.protected_tasks.schedule_task")
    def test_trigger_task_success(self, mock_schedule, client, db, test_user, auth_headers):
        """Triggering an active task creates a pending run."""
        run_id = uuid.uuid4()
        mock_schedule.return_value = run_id

        create_resp = _create_task(client, auth_headers)
        task_id = create_resp.json()["id"]

        resp = client.post(f"/api/tasks/{task_id}/trigger", headers=auth_headers)

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["status"] == "pending"
        assert data["run_id"] == str(run_id)
        mock_schedule.assert_called_once()

    @patch("app.api.protected_tasks.schedule_task")
    def test_trigger_inactive_task(self, mock_schedule, client, db, test_user, auth_headers):
        """Triggering an inactive task returns an error."""
        create_resp = _create_task(client, auth_headers)
        task_id = create_resp.json()["id"]

        # Deactivate the task
        client.put(f"/api/tasks/{task_id}", json={
            "is_active": False,
        }, headers=auth_headers)

        resp = client.post(f"/api/tasks/{task_id}/trigger", headers=auth_headers)

        assert resp.status_code == 422
        mock_schedule.assert_not_called()

    def test_trigger_task_not_found(self, client, db, test_user, auth_headers):
        """Triggering a non-existent task returns 404."""
        fake_id = str(uuid.uuid4())
        resp = client.post(f"/api/tasks/{fake_id}/trigger", headers=auth_headers)

        assert resp.status_code == 404
