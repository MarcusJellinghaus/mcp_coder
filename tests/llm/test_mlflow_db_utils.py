"""Tests for mlflow_db_utils — raw SQLite queries for MLflow tracking."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mcp_coder.llm.mlflow_db_utils import TrackingStats, query_sqlite_tracking


def _make_test_db(tmp_path: Path, runs: list[dict[str, object]]) -> Path:
    """Create a minimal MLflow-schema SQLite DB with given runs.

    Each run dict has keys: start_time_ms, source_name, experiment_name.
    Returns path to .db file.
    """
    db_path = tmp_path / "mlflow.db"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("CREATE TABLE experiments (experiment_id TEXT PRIMARY KEY, name TEXT)")
    cur.execute(
        "CREATE TABLE runs ("
        "  run_uuid TEXT PRIMARY KEY,"
        "  experiment_id TEXT,"
        "  start_time INTEGER"
        ")"
    )
    cur.execute("CREATE TABLE tags (run_uuid TEXT, key TEXT, value TEXT)")

    # Collect unique experiment names and assign IDs
    exp_names: dict[str, str] = {}
    for run in runs:
        exp_name = str(run["experiment_name"])
        if exp_name not in exp_names:
            exp_id = str(len(exp_names))
            exp_names[exp_name] = exp_id
            cur.execute("INSERT INTO experiments VALUES (?, ?)", (exp_id, exp_name))

    # Insert runs and tags
    for idx, run in enumerate(runs):
        run_uuid = f"run-{idx}"
        exp_id = exp_names[str(run["experiment_name"])]
        cur.execute(
            "INSERT INTO runs VALUES (?, ?, ?)",
            (run_uuid, exp_id, run["start_time_ms"]),
        )
        cur.execute(
            "INSERT INTO tags VALUES (?, ?, ?)",
            (run_uuid, "mlflow.source.name", str(run["source_name"])),
        )

    conn.commit()
    conn.close()
    return db_path


class TestTrackingStats:
    """Tests for the TrackingStats dataclass."""

    def test_dataclass_fields(self) -> None:
        now = datetime.now(tz=timezone.utc)
        stats = TrackingStats(run_count=5, last_run_time=now, test_prompt_logged=True)
        assert stats.run_count == 5
        assert stats.last_run_time == now
        assert stats.test_prompt_logged is True


class TestQuerySqliteTracking:
    """Tests for query_sqlite_tracking()."""

    def test_empty_db_returns_zeros(self, tmp_path: Path) -> None:
        db_path = _make_test_db(tmp_path, runs=[])
        result = query_sqlite_tracking(str(db_path), "my-experiment")
        assert result == TrackingStats(0, None, False)

    def test_experiment_not_found(self, tmp_path: Path) -> None:
        db_path = _make_test_db(
            tmp_path,
            runs=[
                {
                    "start_time_ms": 1000000,
                    "source_name": "mcp-coder",
                    "experiment_name": "other-experiment",
                }
            ],
        )
        result = query_sqlite_tracking(str(db_path), "my-experiment")
        assert result == TrackingStats(0, None, False)

    def test_counts_mcp_coder_runs(self, tmp_path: Path) -> None:
        runs = [
            {
                "start_time_ms": 1000000,
                "source_name": "mcp-coder",
                "experiment_name": "exp",
            },
            {
                "start_time_ms": 2000000,
                "source_name": "mcp-coder",
                "experiment_name": "exp",
            },
            {
                "start_time_ms": 3000000,
                "source_name": "mcp-coder",
                "experiment_name": "exp",
            },
        ]
        db_path = _make_test_db(tmp_path, runs=runs)
        result = query_sqlite_tracking(str(db_path), "exp")
        assert result.run_count == 3

    def test_ignores_other_source_tags(self, tmp_path: Path) -> None:
        runs = [
            {
                "start_time_ms": 1000000,
                "source_name": "mcp-coder",
                "experiment_name": "exp",
            },
            {
                "start_time_ms": 2000000,
                "source_name": "other-tool",
                "experiment_name": "exp",
            },
        ]
        db_path = _make_test_db(tmp_path, runs=runs)
        result = query_sqlite_tracking(str(db_path), "exp")
        assert result.run_count == 1

    def test_last_run_time_is_utc(self, tmp_path: Path) -> None:
        ts_ms = 1_711_100_000_000  # known epoch ms
        db_path = _make_test_db(
            tmp_path,
            runs=[
                {
                    "start_time_ms": ts_ms,
                    "source_name": "mcp-coder",
                    "experiment_name": "exp",
                }
            ],
        )
        result = query_sqlite_tracking(str(db_path), "exp")
        assert result.last_run_time is not None
        assert result.last_run_time.tzinfo == timezone.utc
        expected = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
        assert result.last_run_time == expected

    def test_since_none_prompt_false(self, tmp_path: Path) -> None:
        db_path = _make_test_db(
            tmp_path,
            runs=[
                {
                    "start_time_ms": 1000000,
                    "source_name": "mcp-coder",
                    "experiment_name": "exp",
                }
            ],
        )
        result = query_sqlite_tracking(str(db_path), "exp", since=None)
        assert result.test_prompt_logged is False

    def test_since_before_run_true(self, tmp_path: Path) -> None:
        run_ts_ms = 2_000_000_000  # 2000 seconds after epoch
        since = datetime.fromtimestamp(1_000_000, tz=timezone.utc)  # 1000s after epoch
        db_path = _make_test_db(
            tmp_path,
            runs=[
                {
                    "start_time_ms": run_ts_ms,
                    "source_name": "mcp-coder",
                    "experiment_name": "exp",
                }
            ],
        )
        result = query_sqlite_tracking(str(db_path), "exp", since=since)
        assert result.test_prompt_logged is True

    def test_since_after_run_false(self, tmp_path: Path) -> None:
        run_ts_ms = 1_000_000_000  # 1000s after epoch (in ms)
        since = datetime.fromtimestamp(2_000_000, tz=timezone.utc)  # well after
        db_path = _make_test_db(
            tmp_path,
            runs=[
                {
                    "start_time_ms": run_ts_ms,
                    "source_name": "mcp-coder",
                    "experiment_name": "exp",
                }
            ],
        )
        result = query_sqlite_tracking(str(db_path), "exp", since=since)
        assert result.test_prompt_logged is False

    def test_since_exact_boundary_true(self, tmp_path: Path) -> None:
        run_ts_ms = 5_000_000_000  # exact value
        since = datetime.fromtimestamp(run_ts_ms / 1000.0, tz=timezone.utc)
        db_path = _make_test_db(
            tmp_path,
            runs=[
                {
                    "start_time_ms": run_ts_ms,
                    "source_name": "mcp-coder",
                    "experiment_name": "exp",
                }
            ],
        )
        result = query_sqlite_tracking(str(db_path), "exp", since=since)
        assert result.test_prompt_logged is True
