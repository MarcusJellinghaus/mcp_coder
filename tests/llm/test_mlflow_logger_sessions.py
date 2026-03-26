"""Tests for MLflow logger step tracking and session map behavior.

Extracted from test_mlflow_logger.py to keep files under 750 lines.
Covers TestStepTracking, TestLogMetricsWithStep, and TestSessionMapBehavior
classes added as part of the #593 fix (MLflow parameter conflict for
multi-prompt sessions).
"""

from typing import Any
from unittest.mock import MagicMock, Mock, patch

from mcp_coder.config.mlflow_config import MLflowConfig
from mcp_coder.llm.mlflow_logger import MLflowLogger


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
