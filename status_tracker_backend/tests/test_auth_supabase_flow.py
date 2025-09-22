import json
from typing import Any, Dict
import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app(monkeypatch, tmp_path):
    """
    Create app with a temp SQLite DB and test config. We set minimal env vars required for JWT.
    Supabase calls are mocked in tests via monkeypatch.
    """
    # Ensure required JWT secret exists for token creation
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("CORS_ORIGINS", "*")
    # Set dummy Supabase envs so code paths relying on env presence can run, but external calls are mocked.
    monkeypatch.setenv("SUPABASE_URL", "https://dummy.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "dummy-service-key")
    # Use a temporary SQLite DB
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    app = create_app()
    app.config.update(
        TESTING=True,
    )
    with app.app_context():
        db.create_all()
    yield app
    # No explicit teardown needed; tmp_path is ephemeral


@pytest.fixture
def client(app):
    return app.test_client()


def _make_response(data: Dict[str, Any], status: int = 200):
    """
    Helper to return a simple object mimicking requests.Response minimal interface used by our code.
    We only use status_code, json(), and text in supabase_auth.
    """
    class _Resp:
        def __init__(self, payload, status_code):
            self._payload = payload
            self.status_code = status_code
            # Create a plain text for .text access when raising
            self.text = json.dumps(payload)

        def json(self):
            return self._payload

    return _Resp(data, status)


def test_signup_success(client, monkeypatch):
    """
    Test successful signup flow: backend maps Supabase user object to minimal response.
    """
    from app import supabase_auth

    def mock_post(url, headers=None, data=None, timeout=None):
        assert url.endswith("/auth/v1/signup")
        body = json.loads(data or "{}")
        assert "email" in body and "password" in body
        # Return shape as Supabase would (simplified)
        return _make_response(
            {
                "user": {
                    "id": "c0ffee-babe-1234-5678",
                    "email": body["email"],
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z",
                },
                "session": None,
            },
            status=200,
        )

    monkeypatch.setattr(supabase_auth.requests, "post", mock_post)

    resp = client.post(
        "/api/auth/signup",
        json={"email": "alice@example.com", "name": "Alice", "password": "Passw0rd!"},
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["email"] == "alice@example.com"
    assert data["name"] == "Alice"
    assert data["is_active"] is True
    assert data["is_admin"] is False
    # ID is a UUID string from Supabase; our schema keeps it as dump-only int locally, but route returns mapping object
    assert isinstance(data.get("id"), str)


def test_signup_failure_maps_error(client, monkeypatch):
    """
    Test signup error mapping: backend should return 400 with error_description/msg if Supabase fails.
    """
    from app import supabase_auth

    def mock_post(url, headers=None, data=None, timeout=None):
        return _make_response({"error_description": "User already registered"}, status=400)

    monkeypatch.setattr(supabase_auth.requests, "post", mock_post)

    resp = client.post(
        "/api/auth/signup",
        json={"email": "exists@example.com", "name": "Ex", "password": "Passw0rd!"},
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["status"] == "Bad Request"


def test_login_success_and_access_protected_routes(client, monkeypatch):
    """
    Test login flow with Supabase mock, verify app JWT is issued and can call a protected route.
    We use /api/users/me which requires JWT and will 404 if no local user record. That still verifies JWT is accepted.
    """
    from app import supabase_auth

    def mock_post(url, headers=None, data=None, timeout=None):
        assert "grant_type=password" in url
        body = json.loads(data or "{}")
        assert body["email"] == "bob@example.com"
        # Return a typical session response
        return _make_response(
            {
                "access_token": "supa-access",
                "refresh_token": "supa-refresh",
                "user": {"id": "deadbeef-uuid", "email": body["email"]},
            },
            status=200,
        )

    monkeypatch.setattr(supabase_auth.requests, "post", mock_post)

    # Login
    resp = client.post("/api/auth/login", json={"email": "bob@example.com", "password": "secret"})
    assert resp.status_code == 200
    tokens = resp.get_json()
    assert "access_token" in tokens and "refresh_token" in tokens
    jwt = tokens["access_token"]
    assert isinstance(jwt, str) and len(jwt) > 20

    # Call a protected endpoint with the JWT to ensure it's accepted.
    r2 = client.get("/api/users/me", headers={"Authorization": f"Bearer {jwt}"})
    # It may return 404 because there is no local user persisted; this still proves JWT is accepted and route executes.
    assert r2.status_code in (200, 404)


def test_login_missing_fields_422(client):
    resp = client.post("/api/auth/login", json={"email": ""})
    assert resp.status_code == 422
    data = resp.get_json()
    assert data["status"] == "Unprocessable Entity"


def test_login_invalid_credentials_maps_401(client, monkeypatch):
    from app import supabase_auth

    def mock_post(url, headers=None, data=None, timeout=None):
        # Simulate Supabase invalid credentials
        return _make_response({"error_description": "Invalid login credentials"}, status=401)

    monkeypatch.setattr(supabase_auth.requests, "post", mock_post)

    resp = client.post("/api/auth/login", json={"email": "nope@example.com", "password": "bad"})
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["status"] == "Unauthorized"


def test_refresh_token_flow(client, monkeypatch):
    """
    Test refresh endpoint using app refresh token. We log in to get refresh token (Supabase mocked),
    then call /api/auth/refresh with the refresh token and expect a new access token.
    """
    from app import supabase_auth

    def mock_post(url, headers=None, data=None, timeout=None):
        # For login only
        if "grant_type=password" in url:
            return _make_response(
                {
                    "access_token": "supa-access",
                    "refresh_token": "supa-refresh",
                    "user": {"id": "u-1234", "email": "carol@example.com"},
                },
                status=200,
            )
        # Unexpected call
        return _make_response({}, status=500)

    monkeypatch.setattr(supabase_auth.requests, "post", mock_post)

    # Login to obtain app tokens
    resp = client.post("/api/auth/login", json={"email": "carol@example.com", "password": "secret"})
    assert resp.status_code == 200
    tokens = resp.get_json()
    refresh = tokens["refresh_token"]

    # Refresh app token
    r2 = client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {refresh}"})
    assert r2.status_code == 200
    data = r2.get_json()
    assert data["access_token"]
    assert data["refresh_token"] is None


def test_logout_revokes_app_token_and_calls_supabase_logout(client, monkeypatch):
    """
    Test logout route: ensure JWT is revoked and that Supabase logout is called when header present.
    """
    from app import supabase_auth

    # Mock login
    def mock_post(url, headers=None, data=None, timeout=None):
        if "grant_type=password" in url:
            return _make_response(
                {
                    "access_token": "supa-access",
                    "refresh_token": "supa-refresh",
                    "user": {"id": "u-logout", "email": "dave@example.com"},
                },
                status=200,
            )
        return _make_response({}, status=500)

    monkeypatch.setattr(supabase_auth.requests, "post", mock_post)

    # Mock supabase logout call
    called = {"logout_called": False}

    def mock_logout(url, headers=None, timeout=None):
        # Must be /auth/v1/logout and use user's access token
        assert url.endswith("/auth/v1/logout")
        assert headers and "Authorization" in headers and headers["Authorization"].startswith("Bearer ")
        called["logout_called"] = True
        return _make_response({}, status=204)

    monkeypatch.setattr(supabase_auth.requests, "post", mock_logout, raising=False)  # last assignment wins

    # Login to get access token
    resp = client.post("/api/auth/login", json={"email": "dave@example.com", "password": "secret"})
    assert resp.status_code == 200
    tokens = resp.get_json()
    access = tokens["access_token"]

    # Logout with app JWT and provide X-Supabase-Token to revoke Supabase session
    r2 = client.post(
        "/api/auth/logout",
        headers={
            "Authorization": f"Bearer {access}",
            "X-Supabase-Token": "supa-access",  # this should be passed to supabase_auth.logout
        },
    )
    assert r2.status_code == 200
    assert called["logout_called"] is True

    # Verify app token is revoked by attempting to call protected endpoint with same token
    r3 = client.get("/api/users/me", headers={"Authorization": f"Bearer {access}"})
    # Should be 401 because token was revoked
    assert r3.status_code == 401
