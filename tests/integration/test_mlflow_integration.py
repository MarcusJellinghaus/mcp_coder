"""Integration tests for MLflow functionality."""

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.config.mlflow_config import load_mlflow_config
from mcp_coder.llm.mlflow_logger import get_mlflow_logger
from mcp_coder.llm.storage.session_storage import store_session
from mcp_coder.llm.types import LLMResponseDict


class TestMLflowIntegration:
    """Integration tests for complete MLflow workflow."""

    def setup_method(self) -> None:
        """Setup for each test."""
        # Reset global state
        import mcp_coder.llm.mlflow_logger

        mcp_coder.llm.mlflow_logger._global_logger = None
        mcp_coder.llm.mlflow_logger._mlflow_available = None

    @patch("mcp_coder.config.mlflow_config.get_config_values")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=False)
    def test_disabled_by_default(
        self, _mock_available: Any, mock_get_config: Any
    ) -> None:
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
    def test_enabled_but_mlflow_unavailable(self, mock_get_config: Any) -> None:
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
    def test_full_conversation_logging_flow(self, mock_get_config: Any) -> None:
        """Test complete conversation logging workflow.

        Note: MLflow logging was moved from session_storage to prompt.py.
        This test verifies that session storage works correctly without MLflow.
        """
        mock_get_config.return_value = {
            ("mlflow", "enabled"): "true",
            ("mlflow", "tracking_uri"): "file:///tmp/test_mlruns",
            ("mlflow", "experiment_name"): "integration-test",
        }

        # Simulate a complete conversation storage workflow
        prompt = "What is machine learning?"
        response_data: Dict[str, Any] = {
            "provider": "claude",
            "session_id": "test-session-123",
            "text": "Machine learning is...",
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "method": "test",
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
                response_data=response_data,  # type: ignore[arg-type]
                prompt=prompt,
                store_path=temp_dir,
                step_name="integration_test",
                branch_name="test-branch",
            )

            # Verify file was created
            assert os.path.exists(file_path)

            # Verify file contains correct data
            with open(file_path, "r") as f:
                data = json.load(f)
                assert data["prompt"] == prompt
                assert data["response_data"] == response_data
                assert data["metadata"]["model"] == "claude-3-sonnet"
                assert data["metadata"]["branch_name"] == "test-branch"
                assert data["metadata"]["step_name"] == "integration_test"

    def test_config_loading_with_environment_variables(self) -> None:
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
    def test_error_resilience(self, mock_get_config: Any) -> None:
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
                response_data: Dict[str, Any] = {
                    "provider": "claude",
                    "session_id": "test-session-456",
                    "text": "Test response",
                    "version": "1.0",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "method": "test",
                    "raw_response": {},
                }

                with tempfile.TemporaryDirectory() as temp_dir:
                    # This should complete successfully despite MLflow errors
                    file_path = store_session(
                        response_data=response_data,  # type: ignore[arg-type]
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

    def test_real_mlflow_available(self) -> None:
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

    def test_real_mlflow_initialization(self, tmp_path: Path) -> None:
        """Test MLflow logger initialization with real MLflow."""
        try:
            import mlflow

            from mcp_coder.config.mlflow_config import MLflowConfig
            from mcp_coder.llm.mlflow_logger import MLflowLogger

            # Use tmp_path to avoid creating files in project root
            tracking_uri = f"file:///{tmp_path / 'test_real_mlruns'}"
            artifact_location = str(tmp_path / "artifacts")

            config = MLflowConfig(
                enabled=True,
                tracking_uri=tracking_uri,
                experiment_name="test-real",
                artifact_location=artifact_location,
            )

            # This should work without mocking
            logger = MLflowLogger(config)
            assert logger._mlflow_module is not None

        except ImportError:
            pytest.skip("MLflow not installed - skipping real initialization test")

    def test_sqlite_backend_with_tilde_expansion(self, tmp_path: Path) -> None:
        """Test MLflow SQLite backend with ~ expansion in path.

        This test verifies that the fix for ~ expansion in SQLite URIs works correctly.
        It creates a temporary SQLite database, logs a conversation, and verifies
        the data was actually written to the database.
        """
        try:
            import mlflow

            from mcp_coder.config.mlflow_config import MLflowConfig
            from mcp_coder.llm.mlflow_logger import MLflowLogger

            # Use pytest's tmp_path fixture for better cleanup handling
            # Create a SQLite database path
            db_path = tmp_path / "mlflow_test.db"

            # Test with sqlite:/// URI format (absolute path)
            sqlite_uri = f"sqlite:///{db_path}"

            # Use tmp_path for artifacts to prevent creating mlruns/ in project root
            artifact_location = str(tmp_path / "artifacts")

            config = MLflowConfig(
                enabled=True,
                tracking_uri=sqlite_uri,
                experiment_name="test-sqlite-expansion",
                artifact_location=artifact_location,
            )

            # Initialize logger with SQLite backend
            logger = MLflowLogger(config)
            assert logger._mlflow_module is not None
            assert logger.config.enabled is True
            mlflow_module = logger._mlflow_module

            # Simulate logging a conversation
            prompt = "Test prompt for SQLite backend"
            response_data: Dict[str, Any] = {
                "text": "Response for SQLite test",
                "session_id": "sqlite-test-session-789",
                "version": "1.0",
                "timestamp": "2024-01-01T00:00:00Z",
                "method": "test",
                "provider": "claude",
                "raw_response": {
                    "session_info": {
                        "model": "claude-3-sonnet",
                        "usage": {"input_tokens": 10, "output_tokens": 20},
                    }
                },
            }

            metadata = {
                "model": "claude-3-sonnet",
                "branch_name": "test-branch",
                "working_directory": str(tmp_path),
            }

            # Start a run and log the conversation
            run_id = logger.start_run()
            assert run_id is not None, "Failed to start MLflow run"

            logger.log_conversation(prompt, response_data, metadata)

            # End the run
            logger.end_run()

            # Verify the SQLite database was created and contains data
            assert db_path.exists(), f"Database file not created at {db_path}"

            # Query the database to verify data was logged
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check experiments table
            cursor.execute(
                "SELECT name FROM experiments WHERE name = ?",
                ("test-sqlite-expansion",),
            )
            experiments = cursor.fetchall()
            assert len(experiments) > 0, "Experiment not found in database"
            assert experiments[0][0] == "test-sqlite-expansion"

            # Check runs table
            cursor.execute("SELECT COUNT(*) FROM runs")
            run_count = cursor.fetchone()[0]
            assert run_count > 0, "No runs found in database"

            # Check metrics table
            cursor.execute("SELECT key, value FROM metrics")
            metrics = cursor.fetchall()
            assert len(metrics) > 0, "No metrics found in database"

            # Verify expected metrics exist
            metric_keys = {metric[0] for metric in metrics}
            assert "usage_input_tokens" in metric_keys
            assert "usage_output_tokens" in metric_keys

            # Check parameters table
            cursor.execute("SELECT key, value FROM params")
            params = cursor.fetchall()
            assert len(params) > 0, "No parameters found in database"

            # Verify expected parameters
            param_dict = {param[0]: param[1] for param in params}
            assert param_dict.get("model") == "claude-3-sonnet"
            assert param_dict.get("provider") == "claude"
            assert param_dict.get("branch_name") == "test-branch"

            # Verify artifacts are referenced in the database
            cursor.execute(
                "SELECT run_uuid, artifact_uri FROM runs ORDER BY start_time DESC LIMIT 1"
            )
            run_result = cursor.fetchone()
            assert run_result is not None, "No run found"
            _, artifact_uri = run_result
            assert artifact_uri is not None, "No artifact URI in database"

            # Verify prompt_length parameter was logged (indicates prompt was captured)
            assert "prompt_length" in param_dict, "prompt_length parameter not logged"
            assert int(param_dict["prompt_length"]) == len(
                prompt
            ), "prompt_length mismatch"

            conn.close()

            # Verify artifact files exist and contain conversation data
            # Extract artifact path from artifact_uri (format: file:///.../artifacts)
            import urllib.parse

            artifact_path_str = urllib.parse.urlparse(artifact_uri).path
            # On Windows, urlparse may include leading slash like /C:/...
            if artifact_path_str.startswith("/") and ":" in artifact_path_str:
                artifact_path_str = artifact_path_str[1:]  # Remove leading slash
            artifact_path = Path(artifact_path_str) / "conversation_data"

            # Verify conversation_data directory exists
            assert (
                artifact_path.exists()
            ), f"Artifact directory not found at {artifact_path}"
            assert (
                artifact_path.is_dir()
            ), f"Artifact path is not a directory: {artifact_path}"

            # Verify prompt.txt exists and contains prompt
            prompt_file = artifact_path / "prompt.txt"
            assert prompt_file.exists(), f"prompt.txt not found at {prompt_file}"
            prompt_content = prompt_file.read_text(encoding="utf-8")
            assert prompt in prompt_content, "Prompt text not found in prompt.txt"

            # Verify conversation.json exists and contains conversation data
            conversation_file = artifact_path / "conversation.json"
            assert (
                conversation_file.exists()
            ), f"conversation.json not found at {conversation_file}"
            conversation_json = json.loads(
                conversation_file.read_text(encoding="utf-8")
            )

            # Verify conversation JSON structure and content
            assert (
                "prompt" in conversation_json
            ), "prompt field missing in conversation.json"
            assert (
                conversation_json["prompt"] == prompt
            ), "Prompt mismatch in conversation.json"

            assert "response_data" in conversation_json, "response_data field missing"
            assert (
                conversation_json["response_data"]["text"] == response_data["text"]
            ), "Response text mismatch"
            assert (
                conversation_json["response_data"]["provider"] == "claude"
            ), "Provider mismatch"

            assert "metadata" in conversation_json, "metadata field missing"
            assert (
                conversation_json["metadata"]["model"] == "claude-3-sonnet"
            ), "Model mismatch in metadata"
            assert (
                conversation_json["metadata"]["branch_name"] == "test-branch"
            ), "Branch name mismatch"

            # Properly cleanup MLflow to release file locks (critical on Windows)
            try:
                # End any active MLflow runs
                mlflow_module.end_run()
            except Exception:
                pass

            try:
                # Clear tracking URI to force close the tracking store
                mlflow_module.set_tracking_uri("")
            except Exception:
                pass

            # Give Windows time to release file handles
            import time

            time.sleep(0.2)

        except ImportError:
            pytest.skip("MLflow not installed - skipping SQLite backend test")
