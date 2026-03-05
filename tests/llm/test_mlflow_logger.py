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
    def test_init_mlflow_unavailable(self, _mock_available: Any) -> None:
        """Test initialization when MLflow is not available."""
        logger = MLflowLogger(self.config)
        assert logger.active_run_id is None
        # Config should remain enabled (availability is checked per operation)

    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_init_mlflow_available(self, _mock_available: Any) -> None:
        """Test initialization when MLflow is available."""
        with patch(
            "mcp_coder.llm.mlflow_logger.MLflowLogger._initialize_mlflow"
        ) as mock_init:
            logger = MLflowLogger(self.config)
            mock_init.assert_called_once()

    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_init_mlflow_initialization_fails(self, _mock_available: Any) -> None:
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
    def test_start_run_mlflow_disabled(self, _mock_available: Any) -> None:
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

                # Verify tags were set correctly
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


class TestSessionMapBehavior:
    """Test LRU session map behavior in MLflowLogger."""

    def setup_method(self) -> None:
        """Setup for each test."""
        self.config = MLflowConfig(
            enabled=True, tracking_uri="file:///tmp/test", experiment_name="test-exp"
        )

    def test_has_session_returns_false_for_unknown_session(self) -> None:
        """Test that has_session returns False for an unknown session."""
        mock_mlflow = MagicMock()
        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                assert logger.has_session("nonexistent") is False

    def test_end_run_stores_session_mapping(self) -> None:
        """Test that end_run with session_id stores the session→run mapping."""
        mock_mlflow = MagicMock()
        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.active_run_id = "run-abc"

                logger.end_run("FINISHED", session_id="sid-1")

                assert logger.has_session("sid-1") is True
                assert "sid-1" in logger._session_run_map
                assert logger._session_run_map["sid-1"] == "run-abc"
                assert logger.active_run_id is None

    def test_start_run_resumes_existing_session(self) -> None:
        """Test that start_run resumes an existing run when session_id is known."""
        mock_mlflow = MagicMock()
        mock_run = Mock()
        mock_run.info.run_id = "run-abc"
        mock_mlflow.start_run.return_value = mock_run

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger._session_run_map["sid-1"] = "run-abc"

                result = logger.start_run(session_id="sid-1")

                assert result == "run-abc"
                mock_mlflow.start_run.assert_called_once_with(run_id="run-abc")

    def test_log_conversation_artifacts_logs_params_and_artifacts_not_metrics(
        self,
    ) -> None:
        """Test log_conversation_artifacts logs params+artifacts but not metrics."""
        mock_mlflow = MagicMock()
        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.active_run_id = "run-x"

                response_data = {"provider": "claude", "duration_ms": 1500}
                metadata = {
                    "model": "claude-3",
                    "working_directory": "/tmp",
                    "branch_name": "main",
                    "step_name": "test",
                }

                with patch.object(logger, "log_params") as mock_params:
                    with patch.object(logger, "log_metrics") as mock_metrics:
                        with patch.object(logger, "log_artifact") as mock_artifact:
                            logger.log_conversation_artifacts(
                                "prompt text", response_data, metadata
                            )

                            mock_params.assert_called_once()
                            params = mock_params.call_args[0][0]
                            assert "model" in params
                            assert "provider" in params
                            assert "prompt_length" in params
                            assert mock_artifact.call_count == 2
                            mock_metrics.assert_not_called()

    def test_lru_eviction_on_101st_entry(self) -> None:
        """Test that the 101st entry evicts the least recently used entry."""
        mock_mlflow = MagicMock()
        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                for i in range(100):
                    logger._session_run_map[f"sid-{i}"] = f"run-{i}"

                logger.active_run_id = "run-100"
                logger.end_run("FINISHED", session_id="sid-100")

                assert "sid-0" not in logger._session_run_map
                assert logger.has_session("sid-100") is True
                assert len(logger._session_run_map) == 100

    def test_end_run_without_session_id_skips_mapping(self) -> None:
        """Test that end_run without session_id doesn't store anything in the map."""
        mock_mlflow = MagicMock()
        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.active_run_id = "run-xyz"

                logger.end_run("FINISHED", session_id=None)

                assert len(logger._session_run_map) == 0
                assert logger.active_run_id is None
