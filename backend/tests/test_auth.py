"""
Tests for authentication endpoints: /api/auth/*

Covers:
- POST /api/auth/register  - successful registration
- POST /api/auth/login     - successful login and wrong password
- GET  /api/auth/me        - get current user info
- POST /api/auth/refresh   - refresh token
"""
import uuid
import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

import pytest
from sqlalchemy import text


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------

class TestRegister:
    """Registration endpoint tests."""

    @patch("app.services.email_service.get_email_service")
    def test_register_success(self, mock_email_svc, client, db):
        """Successful registration creates user, tenant, and user_tenant rows."""
        # Mock the email service so it doesn't actually send
        mock_svc = mock_email_svc.return_value
        mock_svc.send_verification_email = AsyncMock()

        response = client.post("/api/auth/register", json={
            "email": "newuser@example.com",
            "name": "New User",
            "password": "StrongPass1",
            "tenant_name": "My Org",
        })

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["message"] is not None
        assert "user_id" in data
        assert "tenant_id" in data

        # Verify user was persisted.
        # The ORM stores UUID as 32-char hex on SQLite, so convert the
        # dashed UUID from the JSON response for the raw SQL lookup.
        uid_hex = uuid.UUID(data["user_id"]).hex
        row = db.execute(
            text("SELECT email FROM users WHERE id = :uid"),
            {"uid": uid_hex},
        ).fetchone()
        assert row is not None
        assert row[0] == "newuser@example.com"

    @patch("app.services.email_service.get_email_service")
    def test_register_duplicate_email(self, mock_email_svc, client, db, test_user):
        """Registration with an already-registered email returns 400."""
        mock_svc = mock_email_svc.return_value
        mock_svc.send_verification_email = AsyncMock()

        response = client.post("/api/auth/register", json={
            "email": test_user["email"],  # already exists
            "name": "Another User",
            "password": "StrongPass1",
        })

        assert response.status_code == 400

    def test_register_weak_password(self, client):
        """Registration with a weak password is rejected."""
        response = client.post("/api/auth/register", json={
            "email": "weakpw@example.com",
            "name": "Weak PW",
            "password": "short",  # too short, no uppercase, no digit
        })

        # Pydantic validation or custom validator will reject it
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------

class TestLogin:
    """Login endpoint tests."""

    def test_login_success(self, client, db, test_user):
        """Login with correct credentials returns tokens and user info."""
        response = client.post("/api/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"],
        })

        assert response.status_code == 200, response.text
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800
        assert data["user"]["email"] == test_user["email"]
        assert len(data["tenants"]) >= 1

    def test_login_wrong_password(self, client, db, test_user):
        """Login with wrong password returns 401."""
        response = client.post("/api/auth/login", json={
            "email": test_user["email"],
            "password": "WrongPassword123",
        })

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Login with non-existent email returns 401."""
        response = client.post("/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "SomePassword1",
        })

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------

class TestMe:
    """Current user endpoint tests."""

    def test_me_authenticated(self, client, db, test_user, auth_headers):
        """Authenticated request returns current user info."""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["name"] == test_user["name"]
        assert "current_tenant" in data

    def test_me_unauthenticated(self, client):
        """Request without token returns 401 or 403."""
        response = client.get("/api/auth/me")

        assert response.status_code in (401, 403)

    def test_me_invalid_token(self, client):
        """Request with invalid token returns 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token-string"},
        )

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/auth/refresh
# ---------------------------------------------------------------------------

class TestRefreshToken:
    """Token refresh endpoint tests."""

    def test_refresh_success(self, client, db, test_user):
        """After logging in, the refresh token can be used to get new tokens."""
        # First, login to get a refresh token
        login_resp = client.post("/api/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"],
        })
        assert login_resp.status_code == 200
        refresh_token = login_resp.json()["refresh_token"]

        # Now refresh
        refresh_resp = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token,
        })

        assert refresh_resp.status_code == 200, refresh_resp.text
        data = refresh_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_invalid_token(self, client):
        """Refresh with an invalid token returns 401."""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "totally-invalid-token",
        })

        assert response.status_code == 401
