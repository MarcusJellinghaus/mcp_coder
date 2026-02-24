"""Tests for MLflow configuration loading."""

import os
from typing import Any
from unittest.mock import patch

import pytest

from mcp_coder.config.mlflow_config import MLflowConfig, load_mlflow_config


class TestMLflowConfig:
    """Test MLflowConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = MLflowConfig()
        assert config.enabled is False
        assert config.tracking_uri is None
        assert config.experiment_name == "claude-conversations"

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = MLflowConfig(
            enabled=True,
            tracking_uri="file:///tmp/mlruns",
            experiment_name="test-experiment",
        )
        assert config.enabled is True
        assert config.tracking_uri == "file:///tmp/mlruns"
        assert config.experiment_name == "test-experiment"


class TestLoadMLflowConfig:
    """Test load_mlflow_config function."""

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    def test_disabled_by_default(self, mock_get_config: Any) -> None:
        """Test that MLflow is disabled by default."""
        mock_get_config.return_value = {
            ("mlflow", "enabled"): None,
            ("mlflow", "tracking_uri"): None,
            ("mlflow", "experiment_name"): None,
        }

        config = load_mlflow_config()
        assert config.enabled is False
        assert config.tracking_uri is None
        assert config.experiment_name == "claude-conversations"

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    def test_enabled_true_string(self, mock_get_config: Any) -> None:
        """Test enabling MLflow with 'true' string."""
        mock_get_config.return_value = {
            ("mlflow", "enabled"): "true",
            ("mlflow", "tracking_uri"): "file:///tmp/mlruns",
            ("mlflow", "experiment_name"): "test-exp",
        }

        config = load_mlflow_config()
        assert config.enabled is True
        assert config.tracking_uri == "file:///tmp/mlruns"
        assert config.experiment_name == "test-exp"

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    def test_enabled_variations(self, mock_get_config: Any) -> None:
        """Test various ways to enable MLflow."""
        enabled_values = ["true", "True", "1", "yes", "YES", "on", "ON", "enabled"]

        for value in enabled_values:
            mock_get_config.return_value = {
                ("mlflow", "enabled"): value,
                ("mlflow", "tracking_uri"): None,
                ("mlflow", "experiment_name"): None,
            }

            config = load_mlflow_config()
            assert config.enabled is True, f"'{value}' should enable MLflow"

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    def test_disabled_variations(self, mock_get_config: Any) -> None:
        """Test various ways MLflow stays disabled."""
        disabled_values = ["false", "False", "0", "no", "off", "disabled", "invalid"]

        for value in disabled_values:
            mock_get_config.return_value = {
                ("mlflow", "enabled"): value,
                ("mlflow", "tracking_uri"): None,
                ("mlflow", "experiment_name"): None,
            }

            config = load_mlflow_config()
            assert config.enabled is False, f"'{value}' should disable MLflow"

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    def test_default_experiment_name(self, mock_get_config: Any) -> None:
        """Test default experiment name when not configured."""
        mock_get_config.return_value = {
            ("mlflow", "enabled"): "true",
            ("mlflow", "tracking_uri"): None,
            ("mlflow", "experiment_name"): None,
        }

        config = load_mlflow_config()
        assert config.experiment_name == "claude-conversations"

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    def test_empty_experiment_name(self, mock_get_config: Any) -> None:
        """Test empty experiment name falls back to default."""
        mock_get_config.return_value = {
            ("mlflow", "enabled"): "true",
            ("mlflow", "tracking_uri"): None,
            ("mlflow", "experiment_name"): "",
        }

        config = load_mlflow_config()
        assert config.experiment_name == "claude-conversations"

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    def test_environment_variable_precedence(self, mock_get_config: Any) -> None:
        """Test that environment variables take precedence."""
        # This test verifies that get_config_values is called with the right env vars
        mock_get_config.return_value = {
            ("mlflow", "enabled"): "true",
            ("mlflow", "tracking_uri"): "http://localhost:5000",
            ("mlflow", "experiment_name"): "env-experiment",
        }

        config = load_mlflow_config()

        # Verify get_config_values was called with correct parameters
        mock_get_config.assert_called_once_with(
            [
                ("mlflow", "enabled", None),
                ("mlflow", "tracking_uri", "MLFLOW_TRACKING_URI"),
                ("mlflow", "experiment_name", "MLFLOW_EXPERIMENT_NAME"),
            ]
        )

        assert config.enabled is True
        assert config.tracking_uri == "http://localhost:5000"
        assert config.experiment_name == "env-experiment"

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    @patch("mcp_coder.config.mlflow_config.logger")
    def test_debug_logging_enabled(
        self, mock_logger: Any, mock_get_config: Any
    ) -> None:
        """Test debug logging when MLflow is enabled."""
        mock_get_config.return_value = {
            ("mlflow", "enabled"): "true",
            ("mlflow", "tracking_uri"): "file:///tmp/test",
            ("mlflow", "experiment_name"): "test-exp",
        }

        load_mlflow_config()

        mock_logger.debug.assert_called_once_with(
            "MLflow enabled: tracking_uri=file:///tmp/test, experiment_name=test-exp"
        )

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    @patch("mcp_coder.config.mlflow_config.logger")
    def test_debug_logging_disabled(
        self, mock_logger: Any, mock_get_config: Any
    ) -> None:
        """Test debug logging when MLflow is disabled."""
        mock_get_config.return_value = {
            ("mlflow", "enabled"): "false",
            ("mlflow", "tracking_uri"): None,
            ("mlflow", "experiment_name"): None,
        }

        load_mlflow_config()

        mock_logger.debug.assert_called_once_with("MLflow disabled in configuration")
