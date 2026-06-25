"""
tests/test_health.py
Unit tests for app/health.py — the /health readiness/liveness endpoint.

Covers:
  - dependency probes succeed and fail (psycopg2 / redis mocked, no live services)
  - the route always returns 200 (liveness) and reports per-dependency status
"""

from unittest.mock import MagicMock, patch

from app import create_app
from app.health import _check_database, _check_cache


class TestDependencyProbes:

    @patch("psycopg2.connect")
    def test_database_ok(self, mock_connect):
        # Wire up the `with conn.cursor() as cur:` context manager.
        cur = MagicMock()
        mock_connect.return_value.cursor.return_value.__enter__.return_value = cur
        assert _check_database() is True
        cur.execute.assert_called_once_with("SELECT 1")

    @patch("psycopg2.connect", side_effect=Exception("connection refused"))
    def test_database_failure_is_swallowed(self, mock_connect):
        assert _check_database() is False

    @patch("redis.from_url")
    def test_cache_ok(self, mock_from_url):
        mock_from_url.return_value.ping.return_value = True
        assert _check_cache() is True

    @patch("redis.from_url", side_effect=Exception("no route to host"))
    def test_cache_failure_is_swallowed(self, mock_from_url):
        assert _check_cache() is False


class TestHealthRoute:

    def _client(self):
        return create_app().test_client()

    @patch("app.health._check_cache", return_value=True)
    @patch("app.health._check_database", return_value=True)
    def test_all_ok(self, _db, _cache):
        r = self._client().get("/health")
        assert r.status_code == 200
        assert r.get_json() == {"status": "ok", "database": "ok", "cache": "ok"}

    @patch("app.health._check_cache", return_value=False)
    @patch("app.health._check_database", return_value=False)
    def test_degraded_still_returns_200(self, _db, _cache):
        # Liveness: app is up, so 200 even when both dependencies are down.
        r = self._client().get("/health")
        assert r.status_code == 200
        body = r.get_json()
        assert body["status"] == "degraded"
        assert body["database"] == "error"
        assert body["cache"] == "error"

    @patch("app.health._check_cache", return_value=False)
    @patch("app.health._check_database", return_value=True)
    def test_partial_degraded(self, _db, _cache):
        r = self._client().get("/health")
        assert r.status_code == 200
        body = r.get_json()
        assert body["database"] == "ok"
        assert body["cache"] == "error"
        assert body["status"] == "degraded"
