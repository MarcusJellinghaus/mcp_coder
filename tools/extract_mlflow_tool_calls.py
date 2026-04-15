#!/usr/bin/env python3
"""Extract raw tool call + result pairs from MLflow conversation artifacts.

Two modes:
  1. One example per unique tool name (for building test data):
     python tools/extract_mlflow_tool_calls.py --unique --output testdata/

  2. All tool calls from a specific run (for debugging a session):
     python tools/extract_mlflow_tool_calls.py --run <run_id> --output testdata/

Options:
    --limit N       Max runs to scan when using --unique (default: 50)
    --output DIR    Output directory (default: current dir)
    --run ID        Extract all tool calls from a specific run (prefix match)
    --unique        Extract one example per unique tool name across recent runs
    --db-path PATH  Path to MLflow SQLite database (auto-detected if not specified)

Examples:
    # One file per unique tool type from last 50 runs
    python tools/extract_mlflow_tool_calls.py --unique --output testdata/

    # All tool calls from a specific run
    python tools/extract_mlflow_tool_calls.py --run 962a21de --output testdata/

    # Scan more runs for unique tools
    python tools/extract_mlflow_tool_calls.py --unique --limit 100 --output testdata/
"""

import argparse
import json
import re
import sqlite3
import urllib.parse
from pathlib import Path
from typing import Any


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


def get_artifact_base(artifact_uri: str) -> Path | None:
    """Parse artifact URI to local path."""
    artifact_path_str = urllib.parse.urlparse(artifact_uri).path
    if artifact_path_str.startswith("/") and ":" in artifact_path_str:
        artifact_path_str = artifact_path_str[1:]
    p = Path(artifact_path_str)
    return p if p.exists() else None


def load_messages(artifact_uri: str, step: int = 0) -> list[dict[str, Any]]:
    """Load messages from a run's conversation artifact."""
    base = get_artifact_base(artifact_uri)
    if not base:
        return []
    conv_file = base / "conversation_data" / f"step_{step}_conversation.json"
    if not conv_file.exists():
        return []
    try:
        data = json.loads(conv_file.read_text(encoding="utf-8"))
        return data.get("response_data", {}).get("raw_response", {}).get("messages", [])
    except (json.JSONDecodeError, ValueError):
        return []


def extract_pairs(msgs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract tool call + result pairs from conversation messages."""
    pairs = []
    for i, m in enumerate(msgs):
        if m.get("type") != "assistant":
            continue
        content = m.get("message", {}).get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            # Find matching result in next few messages
            for j in range(i + 1, min(i + 3, len(msgs))):
                if msgs[j].get("type") == "user" and "tool_use_result" in msgs[j]:
                    pairs.append({
                        "tool_call": block,
                        "tool_result": msgs[j]["tool_use_result"],
                    })
                    break
    return pairs


def get_recent_runs(
    conn: sqlite3.Connection, limit: int = 50
) -> list[dict[str, Any]]:
    """Get recent runs from database."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT run_uuid, artifact_uri, start_time
        FROM runs
        WHERE lifecycle_stage = 'active'
        ORDER BY start_time DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [
        {"run_id": row[0], "artifact_uri": row[1], "start_time": row[2]}
        for row in cursor.fetchall()
    ]


def find_run(conn: sqlite3.Connection, run_id_prefix: str) -> dict[str, Any] | None:
    """Find a run by ID prefix."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT run_uuid, artifact_uri FROM runs WHERE run_uuid LIKE ?",
        (run_id_prefix + "%",),
    )
    row = cursor.fetchone()
    if row:
        return {"run_id": row[0], "artifact_uri": row[1]}
    return None


def safe_filename(name: str) -> str:
    """Convert a tool name to a safe filename."""
    # mcp__workspace__edit_file -> tool_edit_file
    if name.startswith("mcp__"):
        rest = name[5:]
        _, _, tool = rest.partition("__")
        if tool:
            return f"tool_{tool}"
    return f"tool_{name}"


def write_pair(output_dir: Path, filename: str, pair: dict[str, Any]) -> None:
    """Write a tool call/result pair as JSON."""
    out_file = output_dir / f"{filename}.json"
    out_file.write_text(
        json.dumps(pair, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  {out_file.name}")


def extract_unique(conn: sqlite3.Connection, limit: int, output_dir: Path) -> None:
    """Extract one example per unique tool name from recent runs."""
    runs = get_recent_runs(conn, limit)
    print(f"Scanning {len(runs)} runs for unique tool types...\n")

    seen: dict[str, dict[str, Any]] = {}
    for run in runs:
        msgs = load_messages(run["artifact_uri"])
        if not msgs:
            continue
        pairs = extract_pairs(msgs)
        for pair in pairs:
            name = pair["tool_call"].get("name", "")
            if name not in seen:
                seen[name] = pair
                print(f"  Found: {name} (from {run['run_id'][:12]})")

    print(f"\n{len(seen)} unique tool types found. Writing files:\n")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, pair in sorted(seen.items()):
        write_pair(output_dir, safe_filename(name), pair)

    print(f"\nDone. {len(seen)} files written to {output_dir}")


def extract_run(conn: sqlite3.Connection, run_id_prefix: str, output_dir: Path) -> None:
    """Extract all tool calls from a specific run."""
    run = find_run(conn, run_id_prefix)
    if not run:
        print(f"Error: No run found matching '{run_id_prefix}'")
        return

    print(f"Run: {run['run_id']}")
    msgs = load_messages(run["artifact_uri"])
    if not msgs:
        print("No conversation data found.")
        return

    pairs = extract_pairs(msgs)
    if not pairs:
        print("No tool calls found in this run.")
        return

    print(f"{len(pairs)} tool calls found. Writing files:\n")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Number files to preserve call order
    for i, pair in enumerate(pairs, 1):
        name = pair["tool_call"].get("name", "unknown")
        filename = f"{i:02d}_{safe_filename(name)}"
        write_pair(output_dir, filename, pair)

    print(f"\nDone. {len(pairs)} files written to {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract tool call/result pairs from MLflow artifacts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--unique",
        action="store_true",
        help="Extract one example per unique tool name across recent runs",
    )
    parser.add_argument(
        "--run",
        type=str,
        help="Extract all tool calls from a specific run (prefix match)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max runs to scan when using --unique (default: 50)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="Output directory (default: current dir)",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        help="Path to MLflow SQLite database (auto-detected if not specified)",
    )

    args = parser.parse_args()

    if not args.unique and not args.run:
        parser.error("Specify --unique or --run <run_id>")

    db_path = Path(args.db_path) if args.db_path else get_mlflow_db_path()
    if not db_path.exists():
        print(f"Error: MLflow database not found at {db_path}")
        return

    print(f"Database: {db_path}\n")
    output_dir = Path(args.output)
    conn = sqlite3.connect(db_path)

    try:
        if args.unique:
            extract_unique(conn, args.limit, output_dir)
        elif args.run:
            extract_run(conn, args.run, output_dir)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
