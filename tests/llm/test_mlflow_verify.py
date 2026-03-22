"""Tests for verify_mlflow() domain function."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.config import MLflowConfig
from mcp_coder.llm.mlflow_db_utils import TrackingStats
from mcp_coder.llm.mlflow_logger import verify_mlflow


class TestVerifyMlflowNotInstalled:
    """Tests when MLflow is not importable."""

    def test_mlflow_not_installed(self) -> None:
        """When MLflow not importable, return informational result."""
        with patch(
            "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=False
        ):
            result = verify_mlflow()
        assert result["installed"]["ok"] is False
        assert result["installed"]["value"] == "not installed"
        assert result["overall_ok"] is True  # informational, not a failure


class TestVerifyMlflowDisabled:
    """Tests when MLflow is installed but disabled."""

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_mlflow_installed_but_disabled(
        self, _mock_avail: MagicMock, mock_config: MagicMock
    ) -> None:
        mock_config.return_value = MLflowConfig(enabled=False)
        result = verify_mlflow()
        assert result["installed"]["ok"] is True
        assert result["enabled"]["ok"] is False
        assert result["enabled"]["value"] == "disabled"
        assert result["overall_ok"] is True


class TestVerifyMlflowSqlite:
    """Tests for SQLite tracking URI checks."""

    @patch("mcp_coder.llm.mlflow_logger.query_sqlite_tracking")
    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_mlflow_enabled_sqlite_valid(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        mock_query: MagicMock,
        tmp_path: Path,
    ) -> None:
        db_path = tmp_path / "mlflow.db"
        db_path.touch()
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri=f"sqlite:///{db_path}",
            experiment_name="test-exp",
        )
        mock_query.return_value = TrackingStats(
            run_count=0,
            last_run_time=None,
            test_prompt_logged=False,
        )
        result = verify_mlflow()
        assert result["tracking_uri"]["ok"] is True
        assert "file exists" in result["tracking_uri"]["value"]

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_mlflow_enabled_sqlite_missing_db(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        db_path = tmp_path / "nonexistent.db"
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri=f"sqlite:///{db_path}",
            experiment_name="test-exp",
        )
        result = verify_mlflow()
        assert result["tracking_uri"]["ok"] is False
        assert "NOT found" in result["tracking_uri"]["value"]
        assert result["overall_ok"] is False


class TestVerifyMlflowInvalidUri:
    """Tests for invalid URI validation."""

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_mlflow_enabled_invalid_uri(
        self, _mock_avail: MagicMock, mock_config: MagicMock
    ) -> None:
        """validate_tracking_uri raises ValueError for sqlite:// (missing third /)."""
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri="sqlite://bad",
            experiment_name="test-exp",
        )
        result = verify_mlflow()
        assert result["tracking_uri"]["ok"] is False
        assert "error" in result["tracking_uri"]
        assert result["overall_ok"] is False


class TestVerifyMlflowHttp:
    """Tests for HTTP tracking URI checks."""

    @patch("mcp_coder.llm.mlflow_logger._probe_mlflow_connection")
    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_mlflow_enabled_http_reachable(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        mock_probe: MagicMock,
    ) -> None:
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri="http://localhost:5000",
            experiment_name="test-exp",
        )
        mock_probe.return_value = (
            {"ok": True, "value": "tracking server reachable"},
            {"ok": True, "value": '"test-exp" (exists)'},
        )
        result = verify_mlflow()
        assert result["tracking_uri"]["ok"] is True
        assert result["connection"]["ok"] is True
        assert result["experiment"]["ok"] is True
        assert result["overall_ok"] is True

    @patch("mcp_coder.llm.mlflow_logger._probe_mlflow_connection")
    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_mlflow_enabled_http_unreachable(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        mock_probe: MagicMock,
    ) -> None:
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri="http://localhost:5000",
            experiment_name="test-exp",
        )
        mock_probe.return_value = (
            {"ok": False, "value": "unreachable: Connection refused"},
            {"ok": False, "value": '"test-exp" (could not check)'},
        )
        result = verify_mlflow()
        assert result["connection"]["ok"] is False
        assert result["overall_ok"] is False


class TestVerifyMlflowFileUri:
    """Tests for file:// URI checks."""

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_file_uri_exists(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri=f"file:///{tmp_path}",
            experiment_name="test-exp",
        )
        result = verify_mlflow()
        assert result["tracking_uri"]["ok"] is True
        assert "exists" in result["tracking_uri"]["value"]

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_file_uri_not_exists(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri="file:///nonexistent/path/to/mlruns",
            experiment_name="test-exp",
        )
        result = verify_mlflow()
        assert result["tracking_uri"]["ok"] is False
        assert "NOT found" in result["tracking_uri"]["value"]


class TestVerifyMlflowExperiment:
    """Tests for experiment existence checks via HTTP probe."""

    @patch("mcp_coder.llm.mlflow_logger._probe_mlflow_connection")
    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_experiment_exists(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        mock_probe: MagicMock,
    ) -> None:
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri="http://localhost:5000",
            experiment_name="my-experiment",
        )
        mock_probe.return_value = (
            {"ok": True, "value": "tracking server reachable"},
            {"ok": True, "value": '"my-experiment" (exists)'},
        )
        result = verify_mlflow()
        assert result["experiment"]["ok"] is True
        assert '"my-experiment" (exists)' in result["experiment"]["value"]

    @patch("mcp_coder.llm.mlflow_logger._probe_mlflow_connection")
    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_experiment_not_found(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        mock_probe: MagicMock,
    ) -> None:
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri="http://localhost:5000",
            experiment_name="missing-exp",
        )
        mock_probe.return_value = (
            {"ok": True, "value": "tracking server reachable"},
            {"ok": False, "value": '"missing-exp" (not found)'},
        )
        result = verify_mlflow()
        assert result["experiment"]["ok"] is False
        assert result["overall_ok"] is False


class TestVerifyMlflowArtifactLocation:
    """Tests for artifact location checks."""

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_artifact_location_writable(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri=f"file:///{tmp_path}",
            experiment_name="test-exp",
            artifact_location=str(tmp_path),
        )
        result = verify_mlflow()
        assert result["artifact_location"]["ok"] is True
        assert "writable" in result["artifact_location"]["value"]

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_artifact_location_not_exists(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri="file:///nonexistent/path/to/mlruns",
            experiment_name="test-exp",
            artifact_location="/nonexistent/artifact/path",
        )
        result = verify_mlflow()
        assert result["artifact_location"]["ok"] is False
        assert "NOT found" in result["artifact_location"]["value"]

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_artifact_location_not_configured(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri=f"file:///{tmp_path}",
            experiment_name="test-exp",
            artifact_location=None,
        )
        result = verify_mlflow()
        assert result["artifact_location"]["ok"] is True
        assert "not configured" in result["artifact_location"]["value"]


class TestVerifyMlflowTrackingData:
    """Tests for the tracking_data result key."""

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_tracking_data_skipped_when_disabled(
        self, _mock_avail: MagicMock, mock_config: MagicMock
    ) -> None:
        """Disabled branch includes tracking_data with ok=None."""
        mock_config.return_value = MLflowConfig(enabled=False)
        result = verify_mlflow()
        assert result["tracking_data"]["ok"] is None
        assert "skipped" in result["tracking_data"]["value"]

    @patch("mcp_coder.llm.mlflow_logger.query_sqlite_tracking")
    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_tracking_data_sqlite_no_since(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        mock_query: MagicMock,
        tmp_path: Path,
    ) -> None:
        """SQLite, file exists, since=None → ok=True, no prompt mention."""
        db = tmp_path / "mlflow.db"
        db.touch()
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri=f"sqlite:///{db}",
            experiment_name="my-exp",
        )
        mock_query.return_value = TrackingStats(
            run_count=42,
            last_run_time=datetime(2026, 3, 20, 14, 30, tzinfo=timezone.utc),
            test_prompt_logged=False,
        )
        result = verify_mlflow()
        assert result["tracking_data"]["ok"] is True
        assert "42 runs" in result["tracking_data"]["value"]
        assert "prompt" not in result["tracking_data"]["value"]

    @patch("mcp_coder.llm.mlflow_logger.query_sqlite_tracking")
    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_tracking_data_sqlite_prompt_logged(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        mock_query: MagicMock,
        tmp_path: Path,
    ) -> None:
        """SQLite, since provided, prompt logged → ok=True."""
        db = tmp_path / "mlflow.db"
        db.touch()
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri=f"sqlite:///{db}",
            experiment_name="my-exp",
        )
        mock_query.return_value = TrackingStats(
            run_count=5,
            last_run_time=datetime(2026, 3, 20, 14, 30, tzinfo=timezone.utc),
            test_prompt_logged=True,
        )
        since = datetime(2026, 3, 20, 14, 0, tzinfo=timezone.utc)
        result = verify_mlflow(since=since)
        assert result["tracking_data"]["ok"] is True
        assert "test prompt logged" in result["tracking_data"]["value"]
        assert result["overall_ok"] is True

    @patch("mcp_coder.llm.mlflow_logger.query_sqlite_tracking")
    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_tracking_data_sqlite_prompt_not_logged(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        mock_query: MagicMock,
        tmp_path: Path,
    ) -> None:
        """SQLite, since provided, prompt NOT logged → ok=False, overall_ok=False."""
        db = tmp_path / "mlflow.db"
        db.touch()
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri=f"sqlite:///{db}",
            experiment_name="my-exp",
        )
        mock_query.return_value = TrackingStats(
            run_count=3,
            last_run_time=datetime(2026, 3, 20, 14, 30, tzinfo=timezone.utc),
            test_prompt_logged=False,
        )
        since = datetime(2026, 3, 20, 14, 0, tzinfo=timezone.utc)
        result = verify_mlflow(since=since)
        assert result["tracking_data"]["ok"] is False
        assert "test prompt NOT logged" in result["tracking_data"]["value"]
        assert result["overall_ok"] is False

    @patch("mcp_coder.llm.mlflow_logger._probe_mlflow_connection")
    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_tracking_data_not_present_for_http(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        mock_probe: MagicMock,
    ) -> None:
        """HTTP backend → no tracking_data key in result."""
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri="http://localhost:5000",
            experiment_name="test-exp",
        )
        mock_probe.return_value = (
            {"ok": True, "value": "tracking server reachable"},
            {"ok": True, "value": '"test-exp" (exists)'},
        )
        result = verify_mlflow()
        assert "tracking_data" not in result

    @patch("mcp_coder.llm.mlflow_logger.query_sqlite_tracking")
    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_tracking_data_sqlite_query_error(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        mock_query: MagicMock,
        tmp_path: Path,
    ) -> None:
        """SQLite query failure → tracking_data ok=False with error message."""
        db = tmp_path / "mlflow.db"
        db.touch()
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri=f"sqlite:///{db}",
            experiment_name="my-exp",
        )
        mock_query.side_effect = sqlite3.OperationalError("database is locked")
        result = verify_mlflow()
        assert result["tracking_data"]["ok"] is False
        assert "query failed" in result["tracking_data"]["value"]
        assert "database is locked" in result["tracking_data"]["value"]
        assert result["overall_ok"] is False

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_tracking_data_not_present_when_db_missing(
        self,
        _mock_avail: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """SQLite URI but file missing (tracking_uri ok=False) → no tracking_data."""
        db = tmp_path / "nonexistent.db"
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri=f"sqlite:///{db}",
            experiment_name="test-exp",
        )
        result = verify_mlflow()
        assert result["tracking_uri"]["ok"] is False
        assert "tracking_data" not in result
