#!/usr/bin/env python3
"""Search MLflow conversation artifacts by text content.

Searches prompt text, response text, and tool calls across all MLflow runs.

Usage:
    python tools/search_mlflow_artifacts.py "680"
    python tools/search_mlflow_artifacts.py "task tracker" --field prompt
    python tools/search_mlflow_artifacts.py "save_file" --field tools --limit 10
    python tools/search_mlflow_artifacts.py "pr_info" --branch 680-refactor
"""

import argparse
import json
import re
import sqlite3
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_mlflow_db_path() -> Path:
    """Get the MLflow database path from config or default location."""
    config_paths = [
        Path.home() / ".mcp_coder" / "config.toml",
        Path.home() / ".config" / "mcp-coder" / "config.toml",
    ]
    for config_path in config_paths:
        if config_path.exists():
            config_text = config_path.read_text()
            match = re.search(r'tracking_uri\s*=\s*"sqlite:///([^"]+)"', config_text)
            if match:
                db_path = match.group(1)
                if db_path.startswith("~/"):
                    db_path = str(Path.home() / db_path[2:])
                return Path(db_path)
    return Path.home() / "mlflow_data" / "mlflow.db"


def format_timestamp(timestamp_ms: int) -> str:
    """Format timestamp from milliseconds."""
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def get_all_runs(
    conn: sqlite3.Connection,
    limit: int = 50,
    branch: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get runs with optional filters."""
    cursor = conn.cursor()
    query = """
        SELECT r.run_uuid, r.name, r.start_time, r.end_time,
               r.artifact_uri, r.status, e.name as experiment_name
        FROM runs r
        JOIN experiments e ON r.experiment_id = e.experiment_id
        WHERE r.lifecycle_stage = 'active'
        ORDER BY r.start_time DESC
        LIMIT ?
    """
    cursor.execute(query, (limit,))

    runs = []
    for row in cursor.fetchall():
        run_id = row[0]

        # Get params for filtering
        pcursor = conn.cursor()
        pcursor.execute(
            "SELECT key, value FROM params WHERE run_uuid = ?", (run_id,)
        )
        params = {r[0]: r[1] for r in pcursor.fetchall()}

        # Apply filters
        if branch and params.get("branch_name", "") != branch:
            if branch not in params.get("branch_name", ""):
                continue
        if working_dir and working_dir.lower() not in params.get(
            "working_directory", ""
        ).lower():
            continue

        runs.append(
            {
                "run_id": run_id,
                "name": row[1],
                "start_time": format_timestamp(row[2]) if row[2] else "N/A",
                "start_time_ms": row[2],
                "end_time": format_timestamp(row[3]) if row[3] else "N/A",
                "artifact_uri": row[4],
                "status": row[5],
                "experiment_name": row[6],
                "params": params,
            }
        )
    return runs


def get_artifact_base(artifact_uri: str) -> Optional[Path]:
    """Parse artifact URI to local path."""
    artifact_path_str = urllib.parse.urlparse(artifact_uri).path
    if artifact_path_str.startswith("/") and ":" in artifact_path_str:
        artifact_path_str = artifact_path_str[1:]
    p = Path(artifact_path_str)
    return p if p.exists() else None


def load_step_conversations(artifact_uri: str) -> List[Dict[str, Any]]:
    """Load all step conversation files from a run's artifacts."""
    base = get_artifact_base(artifact_uri)
    if not base:
        return []

    conv_dir = base / "conversation_data"
    if not conv_dir.exists():
        return []

    steps = []
    # Try step_N pattern first
    for step_file in sorted(conv_dir.glob("step_*_conversation.json")):
        try:
            with open(step_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Also load the prompt file
            step_num = step_file.name.split("_")[1]
            prompt_file = conv_dir / f"step_{step_num}_prompt.txt"
            prompt_text = ""
            if prompt_file.exists():
                prompt_text = prompt_file.read_text(encoding="utf-8")
            steps.append(
                {"step": int(step_num), "conversation": data, "prompt": prompt_text}
            )
        except (json.JSONDecodeError, ValueError):
            continue

    # Try legacy conversation.json
    if not steps:
        legacy = conv_dir / "conversation.json"
        if legacy.exists():
            try:
                with open(legacy, "r", encoding="utf-8") as f:
                    data = json.load(f)
                steps.append(
                    {
                        "step": 0,
                        "conversation": data,
                        "prompt": data.get("prompt", ""),
                    }
                )
            except json.JSONDecodeError:
                pass

    return steps


def extract_searchable_text(
    step: Dict[str, Any], field: str
) -> List[Dict[str, str]]:
    """Extract searchable text blocks from a step conversation."""
    results = []
    conv = step.get("conversation", {})
    prompt = step.get("prompt", "")

    if field in ("all", "prompt"):
        if prompt:
            results.append({"field": "prompt", "text": prompt})

    resp = conv.get("response_data", {})

    if field in ("all", "response"):
        text = resp.get("text", "")
        if text:
            results.append({"field": "response", "text": text})

    # Extract from raw_response messages
    raw = resp.get("raw_response", {})
    messages = raw.get("messages", [])

    for msg in messages:
        content = msg.get("message", {}).get("content", [])

        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                bt = block.get("type", "")

                if bt == "tool_use" and field in ("all", "tools"):
                    name = block.get("name", "")
                    inp = json.dumps(block.get("input", {}))
                    results.append(
                        {"field": f"tool_call:{name}", "text": name + " " + inp}
                    )

                if bt == "text" and field in ("all", "response"):
                    t = block.get("text", "")
                    if t.strip():
                        results.append(
                            {"field": "assistant_text", "text": t}
                        )

        # Tool results
        tr = msg.get("tool_use_result")
        if tr and field in ("all", "results"):
            if isinstance(tr, dict):
                content_str = str(tr.get("content", ""))
            else:
                content_str = str(tr)
            if content_str.strip():
                results.append({"field": "tool_result", "text": content_str})

    return results


def search_runs(
    runs: List[Dict[str, Any]],
    query: str,
    field: str = "all",
    case_sensitive: bool = False,
) -> List[Dict[str, Any]]:
    """Search across all runs for matching text."""
    matches = []
    flags = 0 if case_sensitive else re.IGNORECASE

    for run in runs:
        steps = load_step_conversations(run["artifact_uri"])
        run_matches = []

        for step in steps:
            texts = extract_searchable_text(step, field)
            for entry in texts:
                if re.search(query, entry["text"], flags):
                    # Extract context around match
                    m = re.search(query, entry["text"], flags)
                    if m:
                        start = max(0, m.start() - 80)
                        end = min(len(entry["text"]), m.end() + 80)
                        context = entry["text"][start:end]
                        if start > 0:
                            context = "..." + context
                        if end < len(entry["text"]):
                            context = context + "..."

                    run_matches.append(
                        {
                            "step": step["step"],
                            "field": entry["field"],
                            "context": context,
                        }
                    )

        if run_matches:
            matches.append(
                {
                    "run": run,
                    "matches": run_matches,
                }
            )

    return matches


def safe_print(text: str) -> None:
    """Print with Unicode fallback."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Search MLflow conversation artifacts by text content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="Text or regex to search for")
    parser.add_argument(
        "--field",
        choices=["all", "prompt", "response", "tools", "results"],
        default="all",
        help="Which field to search (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max runs to scan (default: 50)",
    )
    parser.add_argument(
        "--branch", type=str, help="Filter by branch name (substring match)"
    )
    parser.add_argument(
        "--working-dir",
        type=str,
        help="Filter by working directory (substring match)",
    )
    parser.add_argument(
        "--case-sensitive", action="store_true", help="Case-sensitive search"
    )
    parser.add_argument(
        "--db-path", type=str, help="Path to MLflow SQLite database"
    )

    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else get_mlflow_db_path()
    if not db_path.exists():
        print(f"Error: MLflow database not found at {db_path}")
        return

    print(f"Database: {db_path}")
    print(f"Searching for: {args.query!r} in field={args.field}")
    if args.branch:
        print(f"Branch filter: {args.branch}")
    if args.working_dir:
        print(f"Working dir filter: {args.working_dir}")
    print()

    conn = sqlite3.connect(db_path)
    try:
        runs = get_all_runs(conn, args.limit, args.branch, args.working_dir)
        print(f"Scanning {len(runs)} runs...")
        matches = search_runs(runs, args.query, args.field, args.case_sensitive)

        print(f"Found {len(matches)} runs with matches.\n")
        print("=" * 80)

        for hit in matches:
            run = hit["run"]
            branch = run["params"].get("branch_name", "N/A")
            wdir = run["params"].get("working_directory", "N/A")
            print(f"\nRun: {run['run_id']}")
            print(f"  Time: {run['start_time']} -> {run['end_time']}")
            print(f"  Branch: {branch}")
            print(f"  Working Dir: {wdir}")
            print(f"  Status: {run['status']}")
            print(f"  Matches ({len(hit['matches'])}):")

            for m in hit["matches"]:
                safe_print(f"    [step {m['step']}] {m['field']}:")
                safe_print(f"      {m['context']}")
            print("-" * 80)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
