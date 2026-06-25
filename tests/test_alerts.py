"""
tests/test_alerts.py
Unit tests for app/alerts.py.

Covers active-alert retrieval (ward-scoped and global), acknowledgement,
and escalation (found / not-found). The known issues (no ward-boundary
authorization, PII in the SMS body) are intentional and asserted as-is.
"""

from unittest.mock import patch

from app.alerts import (
    get_active_alerts,
    acknowledge_alert,
    escalate_alert,
)


class TestGetActiveAlerts:

    @patch("app.alerts._execute_read", return_value=[{"id": "a1"}])
    def test_ward_scoped(self, mock_read):
        assert get_active_alerts("ward_3") == [{"id": "a1"}]

    @patch("app.alerts._execute_read", return_value=[])
    def test_global(self, mock_read):
        assert get_active_alerts() == []


class TestAcknowledgeAlert:

    @patch("app.alerts._execute_write")
    def test_acknowledge(self, mock_write):
        result = acknowledge_alert("a1", "staff_001")
        assert result == {"success": True, "alert_id": "a1"}
        mock_write.assert_called_once()


class TestEscalateAlert:

    @patch("app.alerts._send_sms")
    def test_escalate_found(self, mock_sms):
        # Default _get_alert stub returns a dict, so escalation proceeds.
        result = escalate_alert("a1", "patient unresponsive")
        assert result == {"success": True}
        mock_sms.assert_called_once()

    @patch("app.alerts._get_alert", return_value=None)
    def test_escalate_not_found(self, mock_get):
        result = escalate_alert("missing", "reason")
        assert result == {"success": False, "error": "Not found"}
