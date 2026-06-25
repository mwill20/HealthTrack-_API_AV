"""
tests/test_routes.py
Integration tests for app/routes.py via the Flask test client.

Covers the auth gate (401 without a valid token) and the success path (with
auth mocked) for each blueprint route, plus the app factory wiring. Service
functions are mocked — these tests exercise HTTP routing and the auth check,
not the DB stubs (covered in the service-level test modules).
"""

from unittest.mock import patch

import pytest

from app import create_app


@pytest.fixture
def client():
    return create_app().test_client()


# A token value that our patched validate_token will treat as valid.
VALID = {"user_id": "staff_001", "role": "nurse"}
HDR = {"X-Auth-Token": "good-token"}


class TestVitalsRoutes:

    def test_post_vital_requires_auth(self, client):
        r = client.post("/vitals/p001", json={"vital_type": "heart_rate", "value": 72})
        assert r.status_code == 401

    @patch("app.routes.record_vitals",
           return_value={"success": True, "reading_id": "r1", "alert": False})
    @patch("app.routes.validate_token", return_value=VALID)
    def test_post_vital_success(self, _vt, _rec, client):
        r = client.post("/vitals/p001",
                         headers=HDR,
                         json={"vital_type": "heart_rate", "value": 72})
        assert r.status_code == 201
        assert r.get_json()["success"] is True

    def test_get_vitals_requires_auth(self, client):
        assert client.get("/vitals/p001").status_code == 401

    @patch("app.routes.get_patient_vitals", return_value=[{"id": 1}])
    @patch("app.routes.validate_token", return_value=VALID)
    def test_get_vitals_success(self, _vt, _get, client):
        r = client.get("/vitals/p001?type=heart_rate", headers=HDR)
        assert r.status_code == 200
        assert r.get_json() == [{"id": 1}]

    @patch("app.routes.get_vital_trend", return_value={"min": 60, "max": 100, "avg": 80})
    def test_vital_trend_no_auth_required(self, _trend, client):
        r = client.get("/vitals/p001/trend?type=heart_rate&hours=12")
        assert r.status_code == 200
        assert r.get_json()["avg"] == 80


class TestAlertsRoutes:

    @patch("app.routes.get_active_alerts", return_value=[{"id": "a1"}])
    def test_list_alerts(self, _list, client):
        r = client.get("/alerts/?ward=ward_3")
        assert r.status_code == 200
        assert r.get_json() == [{"id": "a1"}]

    def test_acknowledge_requires_auth(self, client):
        assert client.post("/alerts/a1/acknowledge").status_code == 401

    @patch("app.routes.acknowledge_alert", return_value={"success": True, "alert_id": "a1"})
    @patch("app.routes.validate_token", return_value=VALID)
    def test_acknowledge_success(self, _vt, _ack, client):
        r = client.post("/alerts/a1/acknowledge", headers=HDR)
        assert r.status_code == 200
        assert r.get_json()["success"] is True

    @patch("app.routes.escalate_alert", return_value={"success": True})
    def test_escalate(self, _esc, client):
        r = client.post("/alerts/a1/escalate", json={"reason": "unresponsive"})
        assert r.status_code == 200
        assert r.get_json()["success"] is True


class TestAppFactory:

    @patch("app.health._check_cache", return_value=True)
    @patch("app.health._check_database", return_value=True)
    def test_health_blueprint_registered(self, _db, _cache, client):
        # create_app should wire the health blueprint at /health.
        assert client.get("/health").status_code == 200
