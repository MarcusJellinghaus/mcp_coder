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
import json
import os
import sqlite3
import urllib.parse
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


def get_conversation_data(artifact_uri: str) -> Optional[Dict[str, Any]]:
    """Get conversation data from artifacts.
    
    Args:
        artifact_uri: The artifact URI from the MLflow run
        
    Returns:
        Conversation data dict or None if not found
    """
    try:
        # Parse artifact URI to get local path
        artifact_path_str = urllib.parse.urlparse(artifact_uri).path
        # On Windows, urlparse may include leading slash like /C:/...
        if artifact_path_str.startswith("/") and ":" in artifact_path_str:
            artifact_path_str = artifact_path_str[1:]  # Remove leading slash
        
        conversation_file = Path(artifact_path_str) / "conversation_data" / "conversation.json"
        
        if not conversation_file.exists():
            return None
        
        with open(conversation_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    except Exception:
        return None


def analyze_conversation(conversation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze conversation data and extract key information.
    
    Args:
        conversation_data: The conversation data from conversation.json
        
    Returns:
        Analysis dict with first/last messages, message counts, etc.
    """
    analysis = {
        "prompt": conversation_data.get("prompt", "N/A"),
        "response_text": "N/A",
        "message_counts": {},
        "total_messages": 0,
    }
    
    # Get response text
    response_data = conversation_data.get("response_data", {})
    analysis["response_text"] = response_data.get("text", "N/A")
    
    # Try to get detailed message breakdown from raw_response
    raw_response = response_data.get("raw_response", {})
    messages = raw_response.get("messages", [])
    
    if messages:
        # Count messages by role
        counts: Dict[str, int] = {}
        for msg in messages:
            role = msg.get("role", "unknown")
            counts[role] = counts.get(role, 0) + 1
        
        analysis["message_counts"] = counts
        analysis["total_messages"] = len(messages)
    
    return analysis


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


def safe_print(text: str) -> None:
    """Print text with Unicode fallback for Windows console.
    
    Args:
        text: Text to print
    """
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback for Windows console with cp1252 encoding
        print(text.encode('ascii', 'replace').decode('ascii'))


def print_runs(runs: List[Dict[str, Any]], show_conversation: bool = True) -> None:
    """Print runs in a formatted table.
    
    Args:
        runs: List of run data dictionaries
        show_conversation: Whether to show conversation details
    """
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
        
        # Show conversation details
        if show_conversation:
            conversation_data = get_conversation_data(run['artifact_uri'])
            if conversation_data:
                analysis = analyze_conversation(conversation_data)
                
                print(f"\n    Conversation:")
                
                # Show prompt (first message)
                prompt = analysis['prompt']
                if len(prompt) > 100:
                    prompt = prompt[:100] + "..."
                safe_print(f"      Prompt: {prompt}")
                
                # Show response preview (last message)
                response = analysis['response_text']
                if len(response) > 150:
                    response = response[:150] + "..."
                safe_print(f"      Response: {response}")
                
                # Show message counts
                if analysis['total_messages'] > 0:
                    print(f"      Messages: {analysis['total_messages']} total")
                    for role, count in sorted(analysis['message_counts'].items()):
                        print(f"        - {role}: {count}")
            else:
                print(f"\n    Conversation: [No artifact data available]")
        
        if run['params']:
            print(f"\n    Parameters ({len(run['params'])}):")
            for key, value in sorted(run['params'].items()):
                print(f"      {key}: {value}")
        
        if run['metrics']:
            print(f"\n    Metrics ({len(run['metrics'])}):")
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
    parser.add_argument(
        "--no-conversation",
        action="store_true",
        help="Don't show conversation details (faster)"
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
            print_runs(runs, show_conversation=not args.no_conversation)
    
    finally:
        conn.close()
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
