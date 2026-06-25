"""
tests/test_auth.py
Unit tests for app/auth.py.

Covers authentication (login success/failure), token validation, and the
require_role authorization decorator — including the wrong-role (403) and
no-token (401) failure paths. These assert CURRENT behavior; the known
weaknesses (MD5, no token expiry) are intentional teaching issues, not fixed.
"""

from app.auth import login, validate_token, require_role


class _Req:
    """Minimal stand-in for a Flask request with a headers mapping."""

    def __init__(self, token=""):
        self.headers = {"X-Auth-Token": token} if token else {}


class TestLogin:

    def test_login_success_returns_token(self):
        # _db_get_user stubs a user whose password is "nurse123".
        token = login("nurse_amy", "nurse123")
        assert token is not None
        session = validate_token(token)
        assert session["user_id"] == "staff_001"
        assert session["role"] == "nurse"
        assert "ts" in session

    def test_login_wrong_password_returns_none(self):
        assert login("nurse_amy", "wrong-password") is None

    def test_validate_unknown_token_returns_none(self):
        assert validate_token("not-a-real-token") is None


class TestRequireRole:

    def _protected(self):
        @require_role("nurse")
        def view(request):
            return {"ok": True, "staff": request.staff_id}, 200
        return view

    def test_no_token_unauthorized(self):
        body, status = self._protected()(_Req())
        assert status == 401
        assert body == {"error": "Unauthorized"}

    def test_valid_nurse_allowed(self):
        token = login("nurse_amy", "nurse123")
        body, status = self._protected()(_Req(token))
        assert status == 200
        assert body["ok"] is True
        assert body["staff"] == "staff_001"

    def test_wrong_role_forbidden(self):
        # nurse token against a doctor-only view -> 403.
        token = login("nurse_amy", "nurse123")

        @require_role("doctor")
        def doctor_only(request):
            return {"ok": True}, 200

        body, status = doctor_only(_Req(token))
        assert status == 403
        assert body == {"error": "Forbidden"}
