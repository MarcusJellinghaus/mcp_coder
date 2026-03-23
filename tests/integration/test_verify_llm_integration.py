"""End-to-end integration test: execute_verify() with real LLM and MLflow."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.config.mlflow_config import MLflowConfig
from mcp_coder.llm.mlflow_db_utils import query_sqlite_tracking


@pytest.mark.llm_integration
class TestVerifyEndToEndWithRealLLM:
    """End-to-end test: execute_verify() -> real LLM -> real MLflow -> real DB check."""

    def test_execute_verify_logs_to_mlflow(self, tmp_path: Path) -> None:
        """Verify that execute_verify() logs the test prompt to MLflow SQLite DB."""
        mlflow = pytest.importorskip("mlflow")

        from mcp_coder.cli.commands.verify import execute_verify

        db_path = tmp_path / "verify_test.db"
        sqlite_uri = f"sqlite:///{db_path}"

        with (
            patch(
                "mcp_coder.utils.mlflow_config_loader.load_mlflow_config"
            ) as mock_cfg,
            patch(
                "mcp_coder.cli.commands.verify.verify_config",
                return_value={
                    "entries": [
                        {"label": "Config file", "status": "ok", "value": "ok"}
                    ],
                    "has_error": False,
                },
            ),
        ):
            mock_cfg.return_value = MLflowConfig(
                enabled=True,
                tracking_uri=sqlite_uri,
                experiment_name="verify-integration-test",
                artifact_location=str(tmp_path / "artifacts"),
            )
            # Reset the global MLflow logger so it picks up the new config
            import mcp_coder.llm.mlflow_logger as _ml

            _ml._global_logger = None

            before_ts = datetime.now(timezone.utc)
            args = argparse.Namespace(
                check_models=False,
                mcp_config=None,
                llm_method=None,
                project_dir=None,
            )
            exit_code = execute_verify(args)

        assert exit_code == 0, f"execute_verify returned {exit_code}"

        # DB-level assertion: the test prompt run was logged
        stats = query_sqlite_tracking(
            str(db_path),
            "verify-integration-test",
            since=before_ts,
        )
        assert stats.test_prompt_logged is True, (
            f"Expected test prompt run in DB after {before_ts}, "
            f"got: run_count={stats.run_count}, last={stats.last_run_time}"
        )

        # Cleanup: release file locks before tmp_path cleanup (Windows)
        try:
            mlflow.end_run()
            mlflow.set_tracking_uri("")
        except Exception:  # noqa: BLE001
            pass
        import mcp_coder.llm.mlflow_logger as _ml  # noqa: PLW0127

        _ml._global_logger = None
