#!/usr/bin/env python3
"""View latest MLflow database entries.

This script queries the MLflow SQLite database and displays recent runs
with their parameters, metrics, and artifact locations.

Usage:
    python tools/get_latest_mlflow_db_entries.py [--limit N] [--experiment NAME]
    
Examples:
    # Show last 5 runs
    python tools/get_latest_mlflow_db_entries.py
    
    # Show last 10 runs
    python tools/get_latest_mlflow_db_entries.py --limit 10
    
    # Show runs from specific experiment
    python tools/get_latest_mlflow_db_entries.py --experiment mcp-coder-conversations
"""

import argparse
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_mlflow_db_path() -> Path:
    """Get the MLflow database path from config or default location."""
    # Try to get from config (check both possible locations)
    config_paths = [
        Path.home() / ".mcp_coder" / "config.toml",
        Path.home() / ".config" / "mcp-coder" / "config.toml",
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            import re
            
            config_text = config_path.read_text()
            match = re.search(r'tracking_uri\s*=\s*"sqlite:///([^"]+)"', config_text)
            if match:
                db_path = match.group(1)
                # Expand ~ if present
                if db_path.startswith("~/"):
                    db_path = str(Path.home() / db_path[2:])
                return Path(db_path)
    
    # Default location
    return Path.home() / "mlflow_data" / "mlflow.db"


def format_timestamp(timestamp_ms: int) -> str:
    """Format timestamp from milliseconds to readable string."""
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def get_experiments(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Get all active experiments."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT experiment_id, name, artifact_location, lifecycle_stage
        FROM experiments
        WHERE lifecycle_stage = 'active'
        ORDER BY experiment_id
    """)
    
    experiments = []
    for row in cursor.fetchall():
        experiments.append({
            "id": row[0],
            "name": row[1],
            "artifact_location": row[2],
            "lifecycle_stage": row[3],
        })
    
    return experiments


def get_latest_runs(
    conn: sqlite3.Connection,
    limit: int = 5,
    experiment_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get latest runs with their details."""
    cursor = conn.cursor()
    
    # Build query
    query = """
        SELECT 
            r.run_uuid,
            r.experiment_id,
            r.name,
            r.start_time,
            r.end_time,
            r.artifact_uri,
            r.status,
            e.name as experiment_name
        FROM runs r
        JOIN experiments e ON r.experiment_id = e.experiment_id
        WHERE r.lifecycle_stage = 'active'
    """
    
    params: List[Any] = []
    if experiment_name:
        query += " AND e.name = ?"
        params.append(experiment_name)
    
    query += " ORDER BY r.start_time DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    
    runs = []
    for row in cursor.fetchall():
        run_id = row[0]
        runs.append({
            "run_id": run_id,
            "experiment_id": row[1],
            "name": row[2],
            "start_time": format_timestamp(row[3]) if row[3] else "N/A",
            "end_time": format_timestamp(row[4]) if row[4] else "N/A",
            "artifact_uri": row[5],
            "status": row[6],
            "experiment_name": row[7],
            "params": get_run_params(conn, run_id),
            "metrics": get_run_metrics(conn, run_id),
        })
    
    return runs


def get_run_params(conn: sqlite3.Connection, run_id: str) -> Dict[str, str]:
    """Get parameters for a run."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT key, value FROM params WHERE run_uuid = ? ORDER BY key",
        (run_id,)
    )
    return {row[0]: row[1] for row in cursor.fetchall()}


def get_run_metrics(conn: sqlite3.Connection, run_id: str) -> Dict[str, float]:
    """Get metrics for a run."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT key, value FROM metrics WHERE run_uuid = ? ORDER BY key",
        (run_id,)
    )
    return {row[0]: float(row[1]) for row in cursor.fetchall()}


def print_experiments(experiments: List[Dict[str, Any]]) -> None:
    """Print experiments in a formatted table."""
    print("\n" + "=" * 80)
    print("EXPERIMENTS")
    print("=" * 80)
    
    for exp in experiments:
        print(f"\nID: {exp['id']}")
        print(f"Name: {exp['name']}")
        print(f"Artifact Location: {exp['artifact_location']}")
        print(f"Status: {exp['lifecycle_stage']}")


def print_runs(runs: List[Dict[str, Any]]) -> None:
    """Print runs in a formatted table."""
    print("\n" + "=" * 80)
    print(f"LATEST RUNS ({len(runs)} total)")
    print("=" * 80)
    
    for i, run in enumerate(runs, 1):
        print(f"\n[{i}] Run: {run['name'] or 'Unnamed'}")
        print(f"    ID: {run['run_id']}")
        print(f"    Experiment: {run['experiment_name']}")
        print(f"    Status: {run['status']}")
        print(f"    Start: {run['start_time']}")
        print(f"    End: {run['end_time']}")
        print(f"    Artifacts: {run['artifact_uri']}")
        
        if run['params']:
            print(f"    Parameters ({len(run['params'])}):")
            for key, value in sorted(run['params'].items()):
                print(f"      {key}: {value}")
        
        if run['metrics']:
            print(f"    Metrics ({len(run['metrics'])}):")
            for key, value in sorted(run['metrics'].items()):
                print(f"      {key}: {value:.4f}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="View latest MLflow database entries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of runs to display (default: 5)"
    )
    parser.add_argument(
        "--experiment",
        type=str,
        help="Filter by experiment name"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        help="Path to MLflow SQLite database (auto-detected if not specified)"
    )
    parser.add_argument(
        "--experiments-only",
        action="store_true",
        help="Only show experiments, not runs"
    )
    
    args = parser.parse_args()
    
    # Get database path
    if args.db_path:
        db_path = Path(args.db_path)
    else:
        db_path = get_mlflow_db_path()
    
    if not db_path.exists():
        print(f"Error: MLflow database not found at {db_path}")
        print("\nLooked in:")
        print(f"  - {db_path}")
        print(f"  - Config: {Path.home() / '.config' / 'mcp-coder' / 'config.toml'}")
        return
    
    print(f"MLflow Database: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Get experiments
        experiments = get_experiments(conn)
        print_experiments(experiments)
        
        if not args.experiments_only:
            # Get latest runs
            runs = get_latest_runs(conn, args.limit, args.experiment)
            print_runs(runs)
    
    finally:
        conn.close()
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
