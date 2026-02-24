"""Tests for MLflow logger with graceful fallback."""

import json
import tempfile
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_coder.config.mlflow_config import MLflowConfig
from mcp_coder.llm.mlflow_logger import (
    MLflowLogger,
    get_mlflow_logger,
    is_mlflow_available,
)


class TestIsMLflowAvailable:
    """Test MLflow availability detection."""

    def test_mlflow_available_cached(self) -> None:
        """Test that availability check is cached."""
        # Reset the global cache
        import mcp_coder.llm.mlflow_logger

        mcp_coder.llm.mlflow_logger._mlflow_available = None

        with patch("mcp_coder.llm.mlflow_logger.logger") as mock_logger:
            # First call should try import
            with patch("builtins.__import__") as mock_import:
                mock_import.return_value = True
                result1 = is_mlflow_available()
                assert result1 is True
                mock_logger.debug.assert_called_with("MLflow is available")

            # Second call should use cached value (no import attempt)
            mock_import.reset_mock()
            mock_logger.reset_mock()
            result2 = is_mlflow_available()
            assert result2 is True
            mock_import.assert_not_called()

    def test_mlflow_not_available(self) -> None:
        """Test handling when MLflow is not installed."""
        # Reset the global cache
        import mcp_coder.llm.mlflow_logger

        mcp_coder.llm.mlflow_logger._mlflow_available = None

        with patch("mcp_coder.llm.mlflow_logger.logger") as mock_logger:
            with patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'mlflow'"),
            ):
                result = is_mlflow_available()
                assert result is False
                mock_logger.debug.assert_called_with("MLflow is not installed")


class TestMLflowLogger:
    """Test MLflowLogger class."""

    def setup_method(self) -> None:
        """Setup for each test."""
        self.config = MLflowConfig(
            enabled=True, tracking_uri="file:///tmp/test", experiment_name="test-exp"
        )

    def test_init_disabled_config(self) -> None:
        """Test initialization with disabled config."""
        config = MLflowConfig(enabled=False)
        logger = MLflowLogger(config)
        assert logger.config.enabled is False
        assert logger.active_run_id is None

    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=False)
    def test_init_mlflow_unavailable(self, mock_available: Any) -> None:
        """Test initialization when MLflow is not available."""
        logger = MLflowLogger(self.config)
        assert logger.active_run_id is None
        # Config should remain enabled (availability is checked per operation)

    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_init_mlflow_available(self, mock_available: Any) -> None:
        """Test initialization when MLflow is available."""
        with patch(
            "mcp_coder.llm.mlflow_logger.MLflowLogger._initialize_mlflow"
        ) as mock_init:
            logger = MLflowLogger(self.config)
            mock_init.assert_called_once()

    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_init_mlflow_initialization_fails(self, mock_available: Any) -> None:
        """Test handling when MLflow initialization fails."""
        with patch(
            "mcp_coder.llm.mlflow_logger.MLflowLogger._initialize_mlflow"
        ) as mock_init:
            mock_init.side_effect = Exception("MLflow init failed")
            with patch("mcp_coder.llm.mlflow_logger.logger") as mock_logger:
                logger = MLflowLogger(self.config)
                assert (
                    logger.config.enabled is False
                )  # Should be disabled due to failure
                mock_logger.warning.assert_called_with(
                    "Failed to initialize MLflow: MLflow init failed"
                )

    def test_initialize_mlflow(self) -> None:
        """Test MLflow initialization."""
        mock_mlflow = MagicMock()

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)

                # Verify MLflow setup calls
                mock_mlflow.set_tracking_uri.assert_called_once_with("file:///tmp/test")
                mock_mlflow.set_experiment.assert_called_once_with("test-exp")

    def test_initialize_mlflow_experiment_fails(self) -> None:
        """Test handling when experiment creation fails."""
        mock_mlflow = MagicMock()
        mock_mlflow.set_experiment.side_effect = Exception("Experiment error")

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                with patch("mcp_coder.llm.mlflow_logger.logger") as mock_logger:
                    logger = MLflowLogger(self.config)

                    mock_logger.warning.assert_called_with(
                        "Failed to set MLflow experiment 'test-exp': Experiment error"
                    )

    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=False)
    def test_start_run_mlflow_disabled(self, mock_available: Any) -> None:
        """Test start_run when MLflow is disabled."""
        logger = MLflowLogger(self.config)
        result = logger.start_run()
        assert result is None

    def test_start_run_success(self) -> None:
        """Test successful run start."""
        mock_mlflow = MagicMock()
        mock_run = Mock()
        mock_run.info.run_id = "test-run-123"
        mock_mlflow.start_run.return_value = mock_run

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)

                result = logger.start_run(run_name="test-run", tags={"key": "value"})

                assert result == "test-run-123"
                assert logger.active_run_id == "test-run-123"
                mock_mlflow.start_run.assert_called_once_with(run_name="test-run")

                expected_tags = {
                    "mlflow.source.name": "mcp-coder",
                    "conversation.timestamp": Mock(),  # We'll check this separately
                    "key": "value",
                }
                call_args = mock_mlflow.set_tags.call_args[0][0]
                assert call_args["mlflow.source.name"] == "mcp-coder"
                assert call_args["key"] == "value"
                assert "conversation.timestamp" in call_args

    def test_start_run_auto_name(self) -> None:
        """Test automatic run name generation."""
        mock_mlflow = MagicMock()
        mock_run = Mock()
        mock_run.info.run_id = "test-run-123"
        mock_mlflow.start_run.return_value = mock_run

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)

                result = logger.start_run()

                # Check that a name was generated
                call_args = mock_mlflow.start_run.call_args
                assert call_args[1]["run_name"].startswith("conversation_")

    def test_log_params(self) -> None:
        """Test logging parameters."""
        mock_mlflow = MagicMock()

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.active_run_id = "test-run"

                params = {"model": "claude-3", "temperature": 0.7, "none_value": None}
                logger.log_params(params)

                expected_params = {"model": "claude-3", "temperature": "0.7"}
                mock_mlflow.log_params.assert_called_once_with(expected_params)

    def test_log_metrics(self) -> None:
        """Test logging metrics."""
        mock_mlflow = MagicMock()

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.active_run_id = "test-run"

                metrics: dict[str, Any] = {
                    "duration_ms": 1500,
                    "cost_usd": 0.01,
                    "invalid": "not_numeric",
                }
                logger.log_metrics(metrics)

                expected_metrics = {"duration_ms": 1500.0, "cost_usd": 0.01}
                mock_mlflow.log_metrics.assert_called_once_with(expected_metrics)

    def test_log_artifact(self) -> None:
        """Test logging artifacts."""
        mock_mlflow = MagicMock()

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.active_run_id = "test-run"

                content = "Test artifact content"
                logger.log_artifact(content, "test.txt")

                # Verify log_artifact was called with temp file
                mock_mlflow.log_artifact.assert_called_once()
                call_args = mock_mlflow.log_artifact.call_args
                assert call_args[0][1] == "conversation_data"  # artifact_path

    def test_log_conversation(self) -> None:
        """Test logging complete conversation."""
        mock_mlflow = MagicMock()

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.active_run_id = "test-run"

                prompt = "What is Python?"
                response_data = {
                    "provider": "claude",
                    "duration_ms": 1500,
                    "cost_usd": 0.01,
                    "raw_response": {
                        "session_info": {
                            "usage": {"input_tokens": 10, "output_tokens": 50}
                        }
                    },
                }
                metadata = {"model": "claude-3", "working_directory": "/tmp"}

                with patch.object(logger, "log_params") as mock_params:
                    with patch.object(logger, "log_metrics") as mock_metrics:
                        with patch.object(logger, "log_artifact") as mock_artifact:
                            logger.log_conversation(prompt, response_data, metadata)

                            # Verify parameters were logged
                            mock_params.assert_called_once()
                            params = mock_params.call_args[0][0]
                            assert params["model"] == "claude-3"
                            assert params["provider"] == "claude"
                            assert params["prompt_length"] == len(prompt)

                            # Verify metrics were logged
                            assert (
                                mock_metrics.call_count == 2
                            )  # Main metrics + usage metrics

                            # Verify artifacts were logged
                            assert (
                                mock_artifact.call_count == 2
                            )  # Prompt + conversation JSON

    def test_end_run(self) -> None:
        """Test ending a run."""
        mock_mlflow = MagicMock()

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.active_run_id = "test-run"

                logger.end_run("FINISHED")

                mock_mlflow.end_run.assert_called_once_with(status="FINISHED")
                assert logger.active_run_id is None

    def test_error_handling_graceful_fallback(self) -> None:
        """Test that all operations handle errors gracefully."""
        mock_mlflow = MagicMock()
        mock_mlflow.start_run.side_effect = Exception("MLflow error")

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                with patch("mcp_coder.llm.mlflow_logger.logger") as mock_logger:
                    logger = MLflowLogger(self.config)

                    # All operations should fail gracefully
                    result = logger.start_run()
                    assert result is None

                    logger.log_params({"key": "value"})
                    logger.log_metrics({"metric": 1.0})
                    logger.log_artifact("content", "file.txt")
                    logger.end_run()

                    # Should log warnings but not crash
                    assert mock_logger.warning.called or mock_logger.debug.called


class TestGlobalLogger:
    """Test global logger functionality."""

    def test_get_mlflow_logger_singleton(self) -> None:
        """Test that get_mlflow_logger returns same instance."""
        # Reset global logger
        import mcp_coder.llm.mlflow_logger

        mcp_coder.llm.mlflow_logger._global_logger = None

        logger1 = get_mlflow_logger()
        logger2 = get_mlflow_logger()
        assert logger1 is logger2

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    def test_get_mlflow_logger_loads_config(self, mock_load_config: Any) -> None:
        """Test that global logger loads configuration."""
        # Reset global logger
        import mcp_coder.llm.mlflow_logger

        mcp_coder.llm.mlflow_logger._global_logger = None

        mock_config = MLflowConfig(enabled=True)
        mock_load_config.return_value = mock_config

        logger = get_mlflow_logger()
        mock_load_config.assert_called_once()
        assert logger.config == mock_config
