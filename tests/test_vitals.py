"""
tests/test_vitals.py
Unit tests for app/vitals.py.

Coverage categories:
  - happy path        record_vitals success, threshold lookups
  - edge              age boundaries, empty trend results
  - error/should-fail unknown vital_type -> KeyError, value=None -> TypeError
  - security note     negative values are accepted WITHOUT validation; these
                      tests document that intentional gap rather than fix it.
"""

from unittest.mock import patch

import pytest

from app.vitals import (
    record_vitals,
    get_patient_vitals,
    calculate_alert_threshold,
    get_vital_trend,
    _execute_read,
    _execute_write,
)


class TestRecordVitals:

    @patch("app.vitals._execute_write", return_value="reading_001")
    @patch("app.vitals._execute_read", return_value=[])
    def test_happy_path(self, mock_read, mock_write):
        result = record_vitals("p001", "heart_rate", 72.0, "nurse_01")
        assert result["success"] is True
        assert result["reading_id"] == "reading_001"
        assert result["alert"] is False

    @patch("app.vitals._execute_write", return_value="reading_002")
    @patch("app.vitals._execute_read", return_value=[])
    def test_high_heart_rate_triggers_alert(self, mock_read, mock_write):
        result = record_vitals("p001", "heart_rate", 160.0, "nurse_01")
        assert result["alert"] is True

    @patch("app.vitals._execute_write", return_value="reading_003")
    def test_negative_value_accepted_without_validation(self, mock_write):
        # Documents the intentional gap: no range validation. A negative heart
        # rate is physically impossible but the service accepts it.
        result = record_vitals("p001", "heart_rate", -50.0, "nurse_01")
        assert result["success"] is True

    @patch("app.vitals._execute_write", return_value="reading_004")
    def test_unknown_vital_type_accepted(self, mock_write):
        # Unknown type means _check_alert_threshold hits a KeyError it swallows,
        # so no alert fires and the write still succeeds.
        result = record_vitals("p001", "made_up_type", 99.0, "nurse_01")
        assert result["success"] is True
        assert result["alert"] is False

    @patch("app.vitals._execute_write", return_value="reading_005")
    def test_none_value_raises(self, mock_write):
        # SHOULD-FAIL case: value=None reaches a numeric comparison and crashes.
        with pytest.raises(TypeError):
            record_vitals("p001", "heart_rate", None, "nurse_01")


class TestGetPatientVitals:

    @patch("app.vitals._execute_read", return_value=[{"id": 1}])
    def test_filtered_by_type(self, mock_read):
        rows = get_patient_vitals("p001", "heart_rate")
        assert rows == [{"id": 1}]

    @patch("app.vitals._execute_read", return_value=[])
    def test_no_type_filter(self, mock_read):
        rows = get_patient_vitals("p001")
        assert rows == []


class TestCalculateAlertThreshold:

    def test_adult_heart_rate(self):
        t = calculate_alert_threshold("heart_rate", 45)
        assert t["low"] == 60
        assert t["high"] == 100

    def test_elderly_adjustment(self):
        t = calculate_alert_threshold("heart_rate", 70)
        assert t["high"] == 105   # +5
        assert t["low"] == 57     # -3

    def test_paediatric_adjustment(self):
        t = calculate_alert_threshold("heart_rate", 10)
        assert t["high"] == 110   # +10
        assert t["low"] == 55     # -5

    def test_newborn_uses_paediatric_branch(self):
        t = calculate_alert_threshold("spo2", 0)
        assert t["high"] == 110   # 100 + 10
        assert t["low"] == 90     # 95 - 5

    def test_condition_adjustment(self):
        t = calculate_alert_threshold("heart_rate", 45, has_condition=True)
        assert t["high"] == 110   # 100 + 10

    def test_unknown_vital_type_raises(self):
        # SHOULD-FAIL case: unhandled edge — KeyError on unknown type.
        with pytest.raises(KeyError):
            calculate_alert_threshold("made_up_type", 45)


class TestGetVitalTrend:

    @patch("app.vitals._execute_read",
           return_value=[{"min_val": 60, "max_val": 110, "avg_val": 80}])
    def test_trend_with_rows(self, mock_read):
        trend = get_vital_trend("p001", "heart_rate", 24)
        assert trend == {"min": 60, "max": 110, "avg": 80}

    @patch("app.vitals._execute_read", return_value=[])
    def test_trend_empty(self, mock_read):
        trend = get_vital_trend("p001", "heart_rate", 24)
        assert trend == {"min": None, "max": None, "avg": None}


class TestStubs:
    """Cover the DB stub helpers so coverage reflects the real call paths."""

    def test_execute_read_returns_list(self):
        assert _execute_read("SELECT 1") == []

    def test_execute_write_returns_id(self):
        rid = _execute_write("INSERT ...")
        assert rid.startswith("reading_")
