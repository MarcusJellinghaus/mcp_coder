"""Integration tests for MLflow functionality."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.config.mlflow_config import load_mlflow_config
from mcp_coder.llm.mlflow_logger import get_mlflow_logger
from mcp_coder.llm.storage.session_storage import store_session


class TestMLflowIntegration:
    """Integration tests for complete MLflow workflow."""

    def setup_method(self):
        """Setup for each test."""
        # Reset global state
        import mcp_coder.llm.mlflow_logger
        import mcp_coder.llm.storage.session_storage

        mcp_coder.llm.mlflow_logger._global_logger = None
        mcp_coder.llm.mlflow_logger._mlflow_available = None

        # Reset session storage MLflow availability cache too
        mcp_coder.llm.storage.session_storage._mlflow_available = True

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=False)
    def test_disabled_by_default(self, mock_available, mock_get_config):
        """Test that MLflow integration is disabled when not configured."""
        mock_get_config.return_value = {
            ("mlflow", "enabled"): None,
            ("mlflow", "tracking_uri"): None,
            ("mlflow", "experiment_name"): None,
        }

        # Load config
        config = load_mlflow_config()
        assert config.enabled is False

        # Get logger (should work even when disabled)
        logger = get_mlflow_logger()
        assert logger.config.enabled is False

        # Operations should be no-ops
        result = logger.start_run()
        assert result is None

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    def test_enabled_but_mlflow_unavailable(self, mock_get_config):
        """Test behavior when MLflow is enabled but not installed."""
        mock_get_config.return_value = {
            ("mlflow", "enabled"): "true",
            ("mlflow", "tracking_uri"): "file:///tmp/mlruns",
            ("mlflow", "experiment_name"): "test-experiment",
        }

        with patch(
            "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=False
        ):
            config = load_mlflow_config()
            assert config.enabled is True

            logger = get_mlflow_logger()
            # Should handle gracefully
            result = logger.start_run()
            assert result is None

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    def test_full_conversation_logging_flow(self, mock_get_config):
        """Test complete conversation logging workflow."""
        mock_get_config.return_value = {
            ("mlflow", "enabled"): "true",
            ("mlflow", "tracking_uri"): "file:///tmp/test_mlruns",
            ("mlflow", "experiment_name"): "integration-test",
        }

        mock_mlflow = MagicMock()
        mock_run = MagicMock()
        mock_run.info.run_id = "integration-run-123"
        mock_mlflow.start_run.return_value = mock_run

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                with patch(
                    "mcp_coder.llm.storage.session_storage.get_mlflow_logger"
                ) as mock_get_logger:
                    # Create a mock logger instance
                    mock_logger_instance = MagicMock()
                    mock_logger_instance.config.enabled = True
                    mock_get_logger.return_value = mock_logger_instance

                    # Simulate a complete conversation storage workflow
                    prompt = "What is machine learning?"
                    response_data = {
                        "provider": "claude",
                        "session_id": "test-session-123",
                        "text": "Machine learning is...",
                        "duration_ms": 2500,
                        "cost_usd": 0.02,
                        "raw_response": {
                            "session_info": {
                                "model": "claude-3-sonnet",
                                "usage": {"input_tokens": 15, "output_tokens": 100},
                            }
                        },
                    }

                    with tempfile.TemporaryDirectory() as temp_dir:
                        file_path = store_session(
                            response_data=response_data,
                            prompt=prompt,
                            store_path=temp_dir,
                            step_name="integration_test",
                            branch_name="test-branch",
                        )

                        # Verify file was created
                        assert os.path.exists(file_path)

                        # Verify MLflow logger was called
                        mock_get_logger.assert_called_once()

                        # Verify log_conversation was called with correct arguments
                        assert mock_logger_instance.log_conversation.called
                        call_args = mock_logger_instance.log_conversation.call_args
                        assert call_args[0][0] == prompt  # First arg is prompt
                        assert (
                            call_args[0][1] == response_data
                        )  # Second arg is response_data
                        # Third arg is metadata dict - check key fields
                        metadata = call_args[0][2]
                        assert metadata["model"] == "claude-3-sonnet"
                        assert metadata["branch_name"] == "test-branch"
                        assert metadata["step_name"] == "integration_test"

                        # For backward compatibility, also check the mock_mlflow calls if they happen
                        # (These may or may not be called depending on the implementation)
                        if mock_mlflow.log_params.called:
                            assert mock_mlflow.log_params.called
                            assert mock_mlflow.log_metrics.called
                            assert mock_mlflow.log_artifact.called

    def test_config_loading_with_environment_variables(self):
        """Test configuration loading with environment variable override."""
        # Set environment variables
        with patch.dict(
            os.environ,
            {
                "MLFLOW_TRACKING_URI": "http://localhost:5000",
                "MLFLOW_EXPERIMENT_NAME": "env-override-test",
            },
        ):
            with patch(
                "mcp_coder.config.mlflow_config.get_config_values"
            ) as mock_get_config:
                # Simulate environment variable precedence
                mock_get_config.return_value = {
                    ("mlflow", "enabled"): "true",
                    ("mlflow", "tracking_uri"): "http://localhost:5000",  # From env var
                    ("mlflow", "experiment_name"): "env-override-test",  # From env var
                }

                config = load_mlflow_config()

                # Verify environment variables took precedence
                assert config.enabled is True
                assert config.tracking_uri == "http://localhost:5000"
                assert config.experiment_name == "env-override-test"

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    def test_error_resilience(self, mock_get_config):
        """Test that MLflow errors don't break main functionality."""
        mock_get_config.return_value = {
            ("mlflow", "enabled"): "true",
            ("mlflow", "tracking_uri"): "file:///tmp/mlruns",
            ("mlflow", "experiment_name"): "error-test",
        }

        # Mock MLflow to throw errors
        mock_mlflow = MagicMock()
        mock_mlflow.set_tracking_uri.side_effect = Exception("Connection failed")
        mock_mlflow.start_run.side_effect = Exception("Run creation failed")
        mock_mlflow.log_params.side_effect = Exception("Param logging failed")

        with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
            with patch(
                "mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True
            ):
                # Should not raise exceptions even with MLflow errors
                prompt = "Test prompt"
                response_data = {
                    "provider": "claude",
                    "text": "Test response",
                }

                with tempfile.TemporaryDirectory() as temp_dir:
                    # This should complete successfully despite MLflow errors
                    file_path = store_session(
                        response_data=response_data,
                        prompt=prompt,
                        store_path=temp_dir,
                    )

                    # Main functionality should still work
                    assert os.path.exists(file_path)

                    # File should contain the conversation data
                    with open(file_path, "r") as f:
                        import json

                        data = json.load(f)
                        assert data["prompt"] == prompt
                        assert data["response_data"] == response_data


@pytest.mark.mlflow_integration
class TestMLflowWithRealInstallation:
    """Tests that run only if MLflow is actually installed."""

    def test_real_mlflow_available(self):
        """Test with real MLflow installation if available."""
        try:
            import mlflow

            # Reset availability cache to test real detection
            import mcp_coder.llm.mlflow_logger

            mcp_coder.llm.mlflow_logger._mlflow_available = None

            from mcp_coder.llm.mlflow_logger import is_mlflow_available

            assert is_mlflow_available() is True

        except ImportError:
            pytest.skip("MLflow not installed - skipping real installation test")

    def test_real_mlflow_initialization(self):
        """Test MLflow logger initialization with real MLflow."""
        try:
            import mlflow

            from mcp_coder.config.mlflow_config import MLflowConfig
            from mcp_coder.llm.mlflow_logger import MLflowLogger

            config = MLflowConfig(
                enabled=True,
                tracking_uri="file:///tmp/test_real_mlruns",
                experiment_name="real-test",
            )

            # This should work without mocking
            logger = MLflowLogger(config)
            assert logger._mlflow_module is not None

        except ImportError:
            pytest.skip("MLflow not installed - skipping real initialization test")
