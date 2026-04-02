#!/usr/bin/env python3
"""Inspect a single MLflow run's conversation in detail.

Shows the full tool call trace for a specific run, useful for debugging
why a step failed or understanding what Claude did during implementation.

Usage:
    python tools/inspect_mlflow_run.py <run_id>
    python tools/inspect_mlflow_run.py <run_id> --step 2
    python tools/inspect_mlflow_run.py <run_id> --show-content
    python tools/inspect_mlflow_run.py <run_id> --filter save_file
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


def get_run_info(conn: sqlite3.Connection, run_id: str) -> Optional[Dict[str, Any]]:
    """Get run metadata from database."""
    cursor = conn.cursor()
    # Support partial run IDs
    cursor.execute(
        """
        SELECT r.run_uuid, r.name, r.start_time, r.end_time,
               r.artifact_uri, r.status, e.name
        FROM runs r
        JOIN experiments e ON r.experiment_id = e.experiment_id
        WHERE r.run_uuid LIKE ?
        """,
        (run_id + "%",),
    )
    row = cursor.fetchone()
    if not row:
        return None

    # Get params
    pcursor = conn.cursor()
    pcursor.execute("SELECT key, value FROM params WHERE run_uuid = ?", (row[0],))
    params = {r[0]: r[1] for r in pcursor.fetchall()}

    # Get metrics
    mcursor = conn.cursor()
    mcursor.execute("SELECT key, value FROM metrics WHERE run_uuid = ?", (row[0],))
    metrics = {r[0]: float(r[1]) for r in mcursor.fetchall()}

    return {
        "run_id": row[0],
        "name": row[1],
        "start_time": format_timestamp(row[2]) if row[2] else "N/A",
        "end_time": format_timestamp(row[3]) if row[3] else "N/A",
        "artifact_uri": row[4],
        "status": row[5],
        "experiment_name": row[6],
        "params": params,
        "metrics": metrics,
    }


def get_artifact_base(artifact_uri: str) -> Optional[Path]:
    """Parse artifact URI to local path."""
    artifact_path_str = urllib.parse.urlparse(artifact_uri).path
    if artifact_path_str.startswith("/") and ":" in artifact_path_str:
        artifact_path_str = artifact_path_str[1:]
    p = Path(artifact_path_str)
    return p if p.exists() else None


def load_step(base: Path, step_num: int) -> Optional[Dict[str, Any]]:
    """Load a single step's data."""
    conv_dir = base / "conversation_data"
    conv_file = conv_dir / f"step_{step_num}_conversation.json"
    prompt_file = conv_dir / f"step_{step_num}_prompt.txt"
    params_file = conv_dir / f"step_{step_num}_all_params.json"

    if not conv_file.exists():
        return None

    result: Dict[str, Any] = {"step": step_num}
    try:
        with open(conv_file, "r", encoding="utf-8") as f:
            result["conversation"] = json.load(f)
    except json.JSONDecodeError:
        return None

    if prompt_file.exists():
        result["prompt"] = prompt_file.read_text(encoding="utf-8")
    if params_file.exists():
        with open(params_file, "r", encoding="utf-8") as f:
            result["params"] = json.load(f)

    return result


def list_steps(base: Path) -> List[int]:
    """List available step numbers."""
    conv_dir = base / "conversation_data"
    if not conv_dir.exists():
        return []
    steps = []
    for f in conv_dir.glob("step_*_conversation.json"):
        try:
            steps.append(int(f.name.split("_")[1]))
        except (ValueError, IndexError):
            continue
    return sorted(steps)


def safe_print(text: str) -> None:
    """Print with Unicode fallback."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


def print_tool_trace(
    step_data: Dict[str, Any],
    filter_text: Optional[str] = None,
    show_content: bool = False,
    content_limit: int = 500,
) -> None:
    """Print the tool call trace for a step."""
    conv = step_data.get("conversation", {})
    resp = conv.get("response_data", {})
    raw = resp.get("raw_response", {})
    messages = raw.get("messages", [])

    if not messages:
        # Try simpler format
        text = resp.get("text", "")
        if text:
            safe_print(f"  Response: {text[:content_limit]}")
        else:
            print("  (no message data available)")
        return

    msg_count = 0
    tool_count = 0
    error_count = 0

    for i, msg in enumerate(messages):
        mtype = msg.get("type", "")

        if mtype == "system":
            subtype = msg.get("subtype", "")
            if subtype == "init":
                tools = msg.get("tools", [])
                print(f"  [{i}] SYSTEM init | {len(tools)} tools available")
            continue

        if mtype == "user":
            # Check for tool results
            tr = msg.get("tool_use_result")
            if tr:
                if isinstance(tr, dict):
                    content_str = str(tr.get("content", ""))
                    structured = tr.get("structuredContent")
                else:
                    content_str = str(tr)
                    structured = None

                is_error = "error" in content_str.lower() or (
                    isinstance(structured, dict) and structured.get("is_error")
                )

                if is_error:
                    error_count += 1

                if filter_text and filter_text.lower() not in content_str.lower():
                    continue

                label = "ERROR" if is_error else "RESULT"
                preview = content_str[:content_limit] if show_content else content_str[:150]
                safe_print(f"  [{i}] {label}: {preview}")
            else:
                # User message
                um = msg.get("message", {})
                if isinstance(um, dict):
                    c = um.get("content", "")
                    if isinstance(c, str) and c.strip():
                        preview = c[:200]
                        safe_print(f"  [{i}] USER: {preview}")
            continue

        if mtype == "assistant":
            content = msg.get("message", {}).get("content", [])
            if not isinstance(content, list):
                continue

            for block in content:
                if not isinstance(block, dict):
                    continue
                bt = block.get("type", "")

                if bt == "tool_use":
                    tool_count += 1
                    name = block.get("name", "?")
                    inp = block.get("input", {})

                    if filter_text and filter_text.lower() not in name.lower():
                        inp_str = json.dumps(inp)
                        if filter_text.lower() not in inp_str.lower():
                            continue

                    # Format input concisely
                    if "file_path" in inp:
                        summary = f"file={inp['file_path']}"
                    elif "command" in inp:
                        cmd = inp["command"]
                        summary = f"cmd={cmd[:120]}"
                    elif "pattern" in inp:
                        summary = f"pattern={inp['pattern']}"
                    elif "prompt" in inp:
                        summary = f"prompt={str(inp['prompt'])[:80]}"
                    else:
                        summary = json.dumps(inp)[:150]

                    safe_print(f"  [{i}] CALL: {name} | {summary}")

                    if show_content and inp:
                        for k, v in inp.items():
                            if k in ("file_path", "command", "pattern"):
                                continue
                            vstr = str(v)[:content_limit]
                            safe_print(f"         {k}: {vstr}")

                elif bt == "text":
                    t = block.get("text", "")
                    if t.strip():
                        if filter_text and filter_text.lower() not in t.lower():
                            continue
                        msg_count += 1
                        safe_print(f"  [{i}] TEXT: {t[:300]}")

                elif bt == "thinking":
                    # Skip thinking blocks unless showing content
                    if show_content:
                        t = block.get("thinking", "")[:200]
                        if filter_text and filter_text.lower() not in t.lower():
                            continue
                        safe_print(f"  [{i}] THINKING: {t}")

            continue

        if mtype == "result":
            is_err = msg.get("is_error", False)
            result_text = str(msg.get("result", ""))
            label = "FINAL_ERROR" if is_err else "FINAL"
            safe_print(f"  [{i}] {label}: {result_text[:content_limit]}")

    print(f"\n  Summary: {len(messages)} messages, {tool_count} tool calls, {error_count} errors")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Inspect a single MLflow run's conversation trace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "run_id", help="Run ID (full or prefix)"
    )
    parser.add_argument(
        "--step",
        type=int,
        help="Show only this step number (default: all steps)",
    )
    parser.add_argument(
        "--filter",
        type=str,
        help="Filter trace to entries matching this text",
    )
    parser.add_argument(
        "--show-content",
        action="store_true",
        help="Show full tool input/output content",
    )
    parser.add_argument(
        "--content-limit",
        type=int,
        default=500,
        help="Max chars for content display (default: 500)",
    )
    parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Only show the prompt text for each step",
    )
    parser.add_argument(
        "--db-path", type=str, help="Path to MLflow SQLite database"
    )

    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else get_mlflow_db_path()
    if not db_path.exists():
        print(f"Error: MLflow database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    try:
        run = get_run_info(conn, args.run_id)
        if not run:
            print(f"Error: No run found matching '{args.run_id}'")
            return

        # Print run header
        print("=" * 80)
        print(f"Run: {run['run_id']}")
        print(f"Name: {run['name']}")
        print(f"Experiment: {run['experiment_name']}")
        print(f"Status: {run['status']}")
        print(f"Time: {run['start_time']} -> {run['end_time']}")
        if run["params"]:
            print("Params:")
            for k, v in sorted(run["params"].items()):
                print(f"  {k}: {v}")
        if run["metrics"]:
            print("Metrics:")
            for k, v in sorted(run["metrics"].items()):
                print(f"  {k}: {v:.2f}")
        print("=" * 80)

        base = get_artifact_base(run["artifact_uri"])
        if not base:
            print(f"\nArtifact directory not found: {run['artifact_uri']}")
            return

        steps = list_steps(base)
        if not steps:
            print("\nNo conversation steps found in artifacts.")
            return

        if args.step is not None:
            steps = [args.step] if args.step in steps else []
            if not steps:
                print(f"\nStep {args.step} not found. Available: {list_steps(base)}")
                return

        for step_num in steps:
            step_data = load_step(base, step_num)
            if not step_data:
                continue

            print(f"\n{'─' * 40} Step {step_num} {'─' * 40}")

            prompt = step_data.get("prompt", "")
            if prompt:
                preview = prompt[:500] if not args.show_content else prompt[:2000]
                safe_print(f"Prompt: {preview}")
                if len(prompt) > len(preview):
                    print(f"  ... ({len(prompt)} chars total)")

            if not args.prompt_only:
                print("\nTool Trace:")
                print_tool_trace(
                    step_data,
                    filter_text=args.filter,
                    show_content=args.show_content,
                    content_limit=args.content_limit,
                )

    finally:
        conn.close()


if __name__ == "__main__":
    main()
