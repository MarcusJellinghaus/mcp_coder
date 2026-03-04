#!/usr/bin/env python3
"""Query MLflow SQLite database to show recent runs and experiments."""

import sqlite3
import sys
from pathlib import Path


def get_db_path() -> Path:
    """Get the MLflow database path."""
    # Read from config using the same logic as get_mlflow_config.py
    import os
    
    try:
        # Try to import and use tomllib/tomli
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                # Fallback to default
                return Path.home() / "mlflow_data" / "mlflow.db"
        
        config_path = Path.home() / ".mcp_coder" / "config.toml"
        if not config_path.exists():
            return Path.home() / "mlflow_data" / "mlflow.db"
        
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        
        tracking_uri = config.get("mlflow", {}).get("tracking_uri", "sqlite:///~/mlflow_data/mlflow.db")
        
        # Extract path from SQLite URI
        if tracking_uri.startswith("sqlite:///"):
            path = tracking_uri[len("sqlite:///"):]
            path = os.path.expanduser(path)
            return Path(path)
        else:
            # Filesystem backend - look for mlflow.db in that directory
            path = os.path.expanduser(tracking_uri)
            return Path(path) / "mlflow.db"
    
    except Exception as e:
        print(f"Warning: Could not read config: {e}", file=sys.stderr)
        return Path.home() / "mlflow_data" / "mlflow.db"


def main():
    """Query and display MLflow data."""
    db_path = get_db_path()
    
    print("=" * 70)
    print("MLflow Database Query Tool")
    print("=" * 70)
    print(f"\nDatabase location: {db_path}")
    
    if not db_path.exists():
        print(f"\n[ERROR] Database file does not exist!")
        print(f"   Expected at: {db_path}")
        print("\nPossible reasons:")
        print("  1. MLflow hasn't logged any runs yet")
        print("  2. The tracking_uri in config.toml points to a different location")
        print("  3. MLflow is using a filesystem backend (not SQLite)")
        return 1
    
    print(f"[OK] Database exists ({db_path.stat().st_size:,} bytes)")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check experiments
        print("\n" + "=" * 70)
        print("EXPERIMENTS")
        print("=" * 70)
        
        cursor.execute("""
            SELECT experiment_id, name, artifact_location, lifecycle_stage
            FROM experiments
            ORDER BY experiment_id
        """)
        
        experiments = cursor.fetchall()
        if experiments:
            for exp_id, name, artifact_loc, lifecycle in experiments:
                print(f"\nExperiment ID: {exp_id}")
                print(f"  Name: {name}")
                print(f"  Artifact Location: {artifact_loc}")
                print(f"  Status: {lifecycle}")
        else:
            print("\n[WARN] No experiments found")
        
        # Check recent runs
        print("\n" + "=" * 70)
        print("RECENT RUNS (Last 10)")
        print("=" * 70)
        
        cursor.execute("""
            SELECT 
                r.run_uuid,
                r.experiment_id,
                e.name as experiment_name,
                r.status,
                r.start_time,
                r.end_time,
                r.artifact_uri
            FROM runs r
            LEFT JOIN experiments e ON r.experiment_id = e.experiment_id
            ORDER BY r.start_time DESC
            LIMIT 10
        """)
        
        runs = cursor.fetchall()
        if runs:
            for run_id, exp_id, exp_name, status, start_time, end_time, artifact_uri in runs:
                from datetime import datetime
                start_dt = datetime.fromtimestamp(start_time / 1000) if start_time else None
                duration_ms = (end_time - start_time) if (end_time and start_time) else None
                
                print(f"\nRun ID: {run_id[:8]}...")
                print(f"  Experiment: {exp_name} (ID: {exp_id})")
                print(f"  Status: {status}")
                if start_dt:
                    print(f"  Started: {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                if duration_ms:
                    print(f"  Duration: {duration_ms}ms")
                
                # Get metrics for this run
                cursor.execute("""
                    SELECT key, value
                    FROM metrics
                    WHERE run_uuid = ?
                    ORDER BY key
                """, (run_id,))
                
                metrics = cursor.fetchall()
                if metrics:
                    print(f"  Metrics:")
                    for key, value in metrics:
                        print(f"    - {key}: {value}")
                
                # Get parameters
                cursor.execute("""
                    SELECT key, value
                    FROM params
                    WHERE run_uuid = ?
                    ORDER BY key
                """, (run_id,))
                
                params = cursor.fetchall()
                if params:
                    print(f"  Parameters:")
                    for key, value in params[:5]:  # Show first 5
                        print(f"    - {key}: {value}")
                    if len(params) > 5:
                        print(f"    ... and {len(params) - 5} more")
        else:
            print("\n[WARN] No runs found")
        
        # Summary statistics
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        cursor.execute("SELECT COUNT(*) FROM experiments")
        exp_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM runs")
        run_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM metrics")
        metric_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM params")
        param_count = cursor.fetchone()[0]
        
        print(f"\nTotal Experiments: {exp_count}")
        print(f"Total Runs: {run_count}")
        print(f"Total Metrics: {metric_count}")
        print(f"Total Parameters: {param_count}")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("[OK] Query completed successfully")
        print("=" * 70)
        
        return 0
    
    except sqlite3.Error as e:
        print(f"\n[ERROR] Database error: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
