"""Raw SQLite queries for MLflow tracking database.

This module queries MLflow's SQLite database directly using stdlib sqlite3,
avoiding any MLflow import. This prevents circular dependencies since
mlflow_logger.py already imports mlflow.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class TrackingStats:
    """Statistics from querying an MLflow tracking database.

    Attributes:
        run_count: Total runs matching source tag + experiment.
        last_run_time: UTC datetime of most recent run, or None.
        test_prompt_logged: True if a run exists with start_time >= since.
    """

    run_count: int
    last_run_time: datetime | None
    test_prompt_logged: bool


def query_sqlite_tracking(
    db_path: str,
    experiment_name: str,
    since: datetime | None = None,
) -> TrackingStats:
    """Query an MLflow SQLite database for tracking statistics.

    Uses raw sqlite3 only — no MLflow import.

    Args:
        db_path: Absolute path to the SQLite .db file (tilde already expanded by caller).
        experiment_name: MLflow experiment name to filter runs by.
        since: UTC datetime; if provided, test_prompt_logged is True when a
               run with start_time >= since exists.

    Returns:
        TrackingStats with run_count, last_run_time, test_prompt_logged.
        Returns TrackingStats(0, None, False) if the DB has no matching data.
    """
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        cur = conn.cursor()

        # Count runs and find latest start_time for mcp-coder tagged runs
        cur.execute(
            """
            SELECT COUNT(*), MAX(r.start_time)
            FROM runs r
            JOIN experiments e ON r.experiment_id = e.experiment_id
            JOIN tags t ON r.run_uuid = t.run_uuid
            WHERE e.name = ?
              AND t.key = 'mlflow.source.name'
              AND t.value = 'mcp-coder'
            """,
            (experiment_name,),
        )
        row = cur.fetchone()
        run_count: int = row[0] if row and row[0] else 0
        last_run_epoch_ms: int | None = row[1] if row else None

        # Convert epoch milliseconds to UTC datetime
        last_run_time: datetime | None = None
        if last_run_epoch_ms is not None:
            last_run_time = datetime.fromtimestamp(
                last_run_epoch_ms / 1000.0, tz=timezone.utc
            )

        # Check if any run exists with start_time >= since
        test_prompt_logged = False
        if since is not None:
            since_epoch_ms = int(since.timestamp() * 1000)
            cur.execute(
                """
                SELECT 1
                FROM runs r
                JOIN experiments e ON r.experiment_id = e.experiment_id
                JOIN tags t ON r.run_uuid = t.run_uuid
                WHERE e.name = ?
                  AND t.key = 'mlflow.source.name'
                  AND t.value = 'mcp-coder'
                  AND r.start_time >= ?
                LIMIT 1
                """,
                (experiment_name, since_epoch_ms),
            )
            test_prompt_logged = cur.fetchone() is not None

        return TrackingStats(
            run_count=run_count,
            last_run_time=last_run_time,
            test_prompt_logged=test_prompt_logged,
        )
    finally:
        conn.close()
