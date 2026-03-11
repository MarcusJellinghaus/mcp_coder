"""Tests for verify_mlflow() domain function."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.config import MLflowConfig
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
        self, mock_avail: MagicMock, mock_config: MagicMock
    ) -> None:
        mock_config.return_value = MLflowConfig(enabled=False)
        result = verify_mlflow()
        assert result["installed"]["ok"] is True
        assert result["enabled"]["ok"] is False
        assert result["enabled"]["value"] == "disabled"
        assert result["overall_ok"] is True


class TestVerifyMlflowSqlite:
    """Tests for SQLite tracking URI checks."""

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_mlflow_enabled_sqlite_valid(
        self,
        mock_avail: MagicMock,
        mock_config: MagicMock,
        tmp_path: pytest.TempPathFactory,
    ) -> None:
        db_path = tmp_path / "mlflow.db"  # type: ignore[operator]
        db_path.touch()
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri=f"sqlite:///{db_path}",
            experiment_name="test-exp",
        )
        result = verify_mlflow()
        assert result["tracking_uri"]["ok"] is True
        assert "file exists" in result["tracking_uri"]["value"]

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_mlflow_enabled_sqlite_missing_db(
        self,
        mock_avail: MagicMock,
        mock_config: MagicMock,
        tmp_path: pytest.TempPathFactory,
    ) -> None:
        db_path = tmp_path / "nonexistent.db"  # type: ignore[operator]
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
        self, mock_avail: MagicMock, mock_config: MagicMock
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
        mock_avail: MagicMock,
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
        mock_avail: MagicMock,
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
        mock_avail: MagicMock,
        mock_config: MagicMock,
        tmp_path: pytest.TempPathFactory,
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
        mock_avail: MagicMock,
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
        mock_avail: MagicMock,
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
        mock_avail: MagicMock,
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
        mock_avail: MagicMock,
        mock_config: MagicMock,
        tmp_path: pytest.TempPathFactory,
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
        mock_avail: MagicMock,
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
        mock_avail: MagicMock,
        mock_config: MagicMock,
        tmp_path: pytest.TempPathFactory,
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
