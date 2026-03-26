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

    config: MLflowConfig

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
            _ = MLflowLogger(self.config)
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
                _ = MLflowLogger(self.config)

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
                    _ = MLflowLogger(self.config)

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

                _ = logger.start_run()

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
        """Test logging complete conversation at step 0."""
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

                            # Step 0: stable params logged once
                            mock_params.assert_called_once()
                            params = mock_params.call_args[0][0]
                            assert params == {
                                "model": "claude-3",
                                "provider": "claude",
                                "working_directory": "/tmp",
                            }

                            # Metrics logged with step=0
                            mock_metrics.assert_called_once()
                            call_args = mock_metrics.call_args
                            metrics = call_args[0][0]
                            assert "prompt_length" in metrics
                            assert "duration_ms" in metrics
                            assert "cost_usd" in metrics
                            assert call_args[1]["step"] == 0

                            # 3 artifacts: all_params, prompt, conversation
                            assert mock_artifact.call_count == 3
                            artifact_names = [
                                c[0][1] for c in mock_artifact.call_args_list
                            ]
                            assert "step_0_all_params.json" in artifact_names
                            assert "step_0_prompt.txt" in artifact_names
                            assert "step_0_conversation.json" in artifact_names

                            # Step advanced to 1
                            assert logger.current_step() == 1

    def test_log_conversation_step1_skips_params(self) -> None:
        """Test log_conversation at step 1 skips params, uses step_1_ prefixes."""
        mock_mlflow = MagicMock()

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.active_run_id = "test-run"
                logger._run_step_count["test-run"] = 1  # simulate step 1

                prompt = "Follow-up question"
                response_data = {
                    "provider": "claude",
                    "duration_ms": 800,
                    "cost_usd": 0.005,
                    "raw_response": {},
                }
                metadata = {"model": "claude-3", "working_directory": "/tmp"}

                with patch.object(logger, "log_params") as mock_params:
                    with patch.object(logger, "log_metrics") as mock_metrics:
                        with patch.object(logger, "log_artifact") as mock_artifact:
                            logger.log_conversation(prompt, response_data, metadata)

                            # Step 1: NO params logged
                            mock_params.assert_not_called()

                            # Metrics logged with step=1
                            mock_metrics.assert_called_once()
                            assert mock_metrics.call_args[1]["step"] == 1

                            # Artifacts prefixed step_1_
                            artifact_names = [
                                c[0][1] for c in mock_artifact.call_args_list
                            ]
                            assert "step_1_all_params.json" in artifact_names
                            assert "step_1_prompt.txt" in artifact_names
                            assert "step_1_conversation.json" in artifact_names

                            # Step advanced to 2
                            assert logger.current_step() == 2

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


class TestStepTracking:
    """Test step tracking infrastructure in MLflowLogger."""

    config: MLflowConfig

    def setup_method(self) -> None:
        """Setup for each test."""
        self.config = MLflowConfig(
            enabled=True, tracking_uri="file:///tmp/test", experiment_name="test-exp"
        )

    def test_current_step_returns_zero_when_no_active_run(self) -> None:
        """current_step() returns 0 when no run is active."""
        mock_mlflow = MagicMock()
        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                assert logger.active_run_id is None
                assert logger.current_step() == 0

    def test_current_step_returns_zero_for_new_run(self) -> None:
        """current_step() returns 0 for a freshly started run."""
        mock_mlflow = MagicMock()
        mock_run = Mock()
        mock_run.info.run_id = "run-new"
        mock_mlflow.start_run.return_value = mock_run

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.start_run(run_name="test")
                assert logger.current_step() == 0

    def test_current_step_increments_after_advance(self) -> None:
        """After _advance_step(), current_step() returns 1."""
        mock_mlflow = MagicMock()
        mock_run = Mock()
        mock_run.info.run_id = "run-adv"
        mock_mlflow.start_run.return_value = mock_run

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.start_run(run_name="test")
                assert logger.current_step() == 0
                logger._advance_step()
                assert logger.current_step() == 1

    def test_step_persists_across_end_and_resume(self) -> None:
        """Step count persists when a run is ended and resumed via session_id."""
        mock_mlflow = MagicMock()
        mock_run = Mock()
        mock_run.info.run_id = "run-persist"
        mock_mlflow.start_run.return_value = mock_run

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.start_run(run_name="test")
                logger._advance_step()
                assert logger.current_step() == 1

                # End with session_id to preserve step count
                logger.end_run("FINISHED", session_id="sid-persist")

                # Resume
                logger.start_run(session_id="sid-persist")
                assert logger.current_step() == 1

    def test_new_run_starts_at_step_zero(self) -> None:
        """A brand new run (different session) starts at step 0."""
        mock_mlflow = MagicMock()
        mock_run1 = Mock()
        mock_run1.info.run_id = "run-old"
        mock_run2 = Mock()
        mock_run2.info.run_id = "run-new"
        mock_mlflow.start_run.side_effect = [mock_run1, mock_run2]

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.start_run(run_name="first")
                logger._advance_step()
                logger._advance_step()
                assert logger.current_step() == 2
                logger.end_run("FINISHED")  # no session_id → cleans up

                # New run starts at 0
                logger.start_run(run_name="second")
                assert logger.current_step() == 0

    def test_end_run_without_session_cleans_step_count(self) -> None:
        """Ending a run without session_id removes the step count entry."""
        mock_mlflow = MagicMock()
        mock_run = Mock()
        mock_run.info.run_id = "run-clean"
        mock_mlflow.start_run.return_value = mock_run

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.start_run(run_name="test")
                logger._advance_step()
                assert "run-clean" in logger._run_step_count

                logger.end_run("FINISHED", session_id=None)
                assert "run-clean" not in logger._run_step_count


class TestLogMetricsWithStep:
    """Test log_metrics with step parameter."""

    config: MLflowConfig

    def setup_method(self) -> None:
        """Setup for each test."""
        self.config = MLflowConfig(
            enabled=True, tracking_uri="file:///tmp/test", experiment_name="test-exp"
        )

    def test_log_metrics_with_step_uses_log_metric(self) -> None:
        """When step is provided, each metric is logged via mlflow.log_metric(key, value, step=step)."""
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
                }
                logger.log_metrics(metrics, step=3)

                # Should NOT call log_metrics (batch)
                mock_mlflow.log_metrics.assert_not_called()
                # Should call log_metric per metric with step
                assert mock_mlflow.log_metric.call_count == 2
                calls = {
                    c[0][0]: (c[0][1], c[1]["step"])
                    for c in mock_mlflow.log_metric.call_args_list
                }
                assert calls["duration_ms"] == (1500.0, 3)
                assert calls["cost_usd"] == (0.01, 3)


class TestSessionMapBehavior:
    """Test LRU session map behavior in MLflowLogger."""

    config: MLflowConfig

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
        """Test log_conversation_artifacts at step 0 logs stable params+artifacts, no metrics."""
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

                            # Step 0: stable params only
                            mock_params.assert_called_once()
                            params = mock_params.call_args[0][0]
                            assert params == {
                                "model": "claude-3",
                                "provider": "claude",
                                "working_directory": "/tmp",
                            }

                            # 3 artifacts: all_params, prompt, conversation
                            assert mock_artifact.call_count == 3
                            artifact_names = [
                                c[0][1] for c in mock_artifact.call_args_list
                            ]
                            assert "step_0_all_params.json" in artifact_names
                            assert "step_0_prompt.txt" in artifact_names
                            assert "step_0_conversation.json" in artifact_names

                            # No metrics
                            mock_metrics.assert_not_called()

                            # Step advanced to 1
                            assert logger.current_step() == 1

    def test_log_conversation_artifacts_step1_skips_params(self) -> None:
        """Test log_conversation_artifacts at step 1 skips params."""
        mock_mlflow = MagicMock()
        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                logger = MLflowLogger(self.config)
                logger.active_run_id = "run-x"
                logger._run_step_count["run-x"] = 1  # simulate step 1

                response_data = {"provider": "claude"}
                metadata = {"model": "claude-3", "working_directory": "/tmp"}

                with patch.object(logger, "log_params") as mock_params:
                    with patch.object(logger, "log_metrics") as mock_metrics:
                        with patch.object(logger, "log_artifact") as mock_artifact:
                            logger.log_conversation_artifacts(
                                "prompt text", response_data, metadata
                            )

                            # Step 1: NO params
                            mock_params.assert_not_called()

                            # Artifacts prefixed step_1_
                            artifact_names = [
                                c[0][1] for c in mock_artifact.call_args_list
                            ]
                            assert "step_1_all_params.json" in artifact_names
                            assert "step_1_prompt.txt" in artifact_names
                            assert "step_1_conversation.json" in artifact_names

                            mock_metrics.assert_not_called()

                            # Step advanced to 2
                            assert logger.current_step() == 2

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

    def test_multi_prompt_session_no_param_conflict(self) -> None:
        """Regression test for #593: multi-prompt session must not re-log params."""
        mock_mlflow = MagicMock()
        mock_run = Mock()
        mock_run.info.run_id = "run-593"
        mock_mlflow.start_run.return_value = mock_run

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                lgr = MLflowLogger(self.config)

                # --- Prompt 1 ---
                lgr.start_run(run_name="multi")
                with (
                    patch.object(lgr, "log_params") as p1,
                    patch.object(lgr, "log_metrics") as m1,
                    patch.object(lgr, "log_artifact"),
                ):
                    lgr.log_conversation(
                        "prompt A",
                        {"provider": "claude", "duration_ms": 100, "cost_usd": 0.01},
                        {"model": "claude-3", "working_directory": "/tmp"},
                    )
                    p1.assert_called_once()  # step 0 → params logged
                    m1.assert_called_once()
                    assert m1.call_args[1]["step"] == 0

                lgr.end_run("FINISHED", session_id="s1")

                # --- Prompt 2 (resumed session) ---
                lgr.start_run(session_id="s1")
                with (
                    patch.object(lgr, "log_params") as p2,
                    patch.object(lgr, "log_metrics") as m2,
                    patch.object(lgr, "log_artifact"),
                ):
                    lgr.log_conversation(
                        "prompt B",
                        {"provider": "claude", "duration_ms": 200, "cost_usd": 0.02},
                        {"model": "claude-3", "working_directory": "/tmp"},
                    )
                    p2.assert_not_called()  # step 1 → NO params (no conflict)
                    m2.assert_called_once()
                    assert m2.call_args[1]["step"] == 1

                lgr.end_run("FINISHED", session_id="s1")
