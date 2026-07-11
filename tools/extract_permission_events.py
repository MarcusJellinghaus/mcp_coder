#!/usr/bin/env python3
"""Extract permission (approval/denial) events from MLflow conversation artifacts.

mcp-coder runs Claude Code headless with a restricted tool set. A tool can be
*connected* (via .mcp.json) yet not be on the *allow-list* (settings
``permissions.allow`` / ``--allowedTools``). In ``permissionMode: default`` with
no human present, every call to a non-allow-listed tool returns an error like:

    "Claude requested permissions to use <tool>, but you haven't granted it yet."

That error is recorded as a ``permission_denials`` entry in the run's result
message. This script harvests every such event across all runs, enriches it with
master data (date, branch, model, session, cost, ...), records what the model
*did next* (retried / switched / gave up) and whether the tool later succeeded,
then writes a JSONL + CSV dataset.

Note: these headless runs contain no *manual* approvals — every event is an
auto-denial. The ``outcome`` column is kept generic (denied/allowed/approved) so
interactive runs can slot in later.

Usage:
    python tools/extract_permission_events.py
    python tools/extract_permission_events.py --output permission_data/ --limit 500
    python tools/extract_permission_events.py --db-path /path/to/mlflow.db

Outputs (in --output dir, default: current dir):
    permission_events.jsonl   one event per line, full detail
    permission_events.csv     flat table for spreadsheets / pandas
"""

import argparse
import csv
import json
import re
import sqlite3
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mcp_coder.utils.user_app_data import get_user_app_data_dir


def get_mlflow_db_path() -> Path:
    """Get the MLflow database path from config or default location."""
    config_path = get_user_app_data_dir("mcp_coder") / "config.toml"
    if config_path.exists():
        config_text = config_path.read_text()
        match = re.search(r'tracking_uri\s*=\s*"sqlite:///([^"]+)"', config_text)
        if match:
            db_path = match.group(1)
            if db_path.startswith("~/"):
                db_path = str(Path.home() / db_path[2:])
            return Path(db_path)
    return Path.home() / "mlflow_data" / "mlflow.db"


def get_artifact_base(artifact_uri: str) -> Optional[Path]:
    """Parse artifact URI to local path."""
    artifact_path_str = urllib.parse.urlparse(artifact_uri).path
    if artifact_path_str.startswith("/") and ":" in artifact_path_str:
        artifact_path_str = artifact_path_str[1:]
    p = Path(artifact_path_str)
    return p if p.exists() else None


def get_runs(conn: sqlite3.Connection, limit: Optional[int]) -> List[Dict[str, Any]]:
    """Get active runs (newest first), with DB params attached."""
    cursor = conn.cursor()
    query = """
        SELECT r.run_uuid, r.name, r.start_time, r.status, r.artifact_uri, e.name
        FROM runs r
        JOIN experiments e ON r.experiment_id = e.experiment_id
        WHERE r.lifecycle_stage = 'active'
        ORDER BY r.start_time DESC
    """
    if limit:
        query += f" LIMIT {int(limit)}"
    cursor.execute(query)
    runs = []
    for row in cursor.fetchall():
        run_id = row[0]
        pcur = conn.cursor()
        pcur.execute("SELECT key, value FROM params WHERE run_uuid = ?", (run_id,))
        params = {r[0]: r[1] for r in pcur.fetchall()}
        runs.append(
            {
                "run_id": run_id,
                "name": row[1],
                "start_time": row[2],
                "status": row[3],
                "artifact_uri": row[4],
                "experiment": row[5],
                "db_params": params,
            }
        )
    return runs


def mcp_server(tool_name: str) -> str:
    """Extract the MCP server name from a tool name (mcp__<server>__<tool>)."""
    if tool_name.startswith("mcp__"):
        return tool_name[5:].partition("__")[0]
    return "(native)"


def tool_category(tool_name: str) -> str:
    """Rough category for grouping (read / write / exec / git / github / other)."""
    n = tool_name.lower()
    if any(k in n for k in ("git_", "__git", "branch_status", "base_branch")):
        return "git"
    if "github" in n:
        return "github"
    if any(
        k in n
        for k in (
            "read",
            "search",
            "list",
            "find_ref",
            "library_source",
            "list_symbols",
            "check_file",
            "get_reference",
        )
    ):
        return "read"
    if any(
        k in n
        for k in ("save_file", "edit_file", "append", "delete", "move_", "rename_")
    ):
        return "write"
    if any(k in n for k in ("run_", "_check", "format_code", "sleep")):
        return "exec"
    return "other"


def result_text(content: Any) -> str:
    """Flatten a tool_result content field to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                parts.append(b.get("text", ""))
            else:
                parts.append(str(b))
        return " ".join(parts)
    return str(content)


def index_step(msgs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Pull init/result metadata and build ordered tool-call + result maps."""
    init: Dict[str, Any] = {}
    result: Dict[str, Any] = {}
    calls: List[Tuple[str, str, Dict[str, Any]]] = []  # (id, name, input) in order
    results: Dict[str, Dict[str, Any]] = {}  # id -> {is_error, text}

    for m in msgs:
        mtype = m.get("type")
        if mtype == "system" and m.get("subtype") == "init":
            init = m
        elif mtype == "result":
            result = m
        elif mtype == "assistant":
            content = m.get("message", {}).get("content", [])
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        calls.append(
                            (b.get("id", ""), b.get("name", ""), b.get("input", {}))
                        )
        elif mtype == "user":
            content = m.get("message", {}).get("content", [])
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        results[b.get("tool_use_id", "")] = {
                            "is_error": bool(b.get("is_error")),
                            "text": result_text(b.get("content")),
                        }
    return {"init": init, "result": result, "calls": calls, "results": results}


def analyze_followup(
    denied_id: str,
    denied_name: str,
    denied_input: Dict[str, Any],
    calls: List[Tuple[str, str, Dict[str, Any]]],
    results: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Determine what the model did after a denied call."""
    order = [c[0] for c in calls]
    followup_action = "none (last call in step)"
    next_tool = ""
    if denied_id in order:
        k = order.index(denied_id)
        if k + 1 < len(calls):
            next_tool = calls[k + 1][1]
            followup_action = (
                "retried_same"
                if next_tool == denied_name
                else f"switched_to:{next_tool}"
            )
    # Did an identical call (same name + input) later succeed in this step?
    eventually_succeeded = False
    for cid, name, inp in calls:
        if name == denied_name and inp == denied_input:
            r = results.get(cid)
            if r and not r["is_error"]:
                eventually_succeeded = True
                break
    return {
        "followup_action": followup_action,
        "next_tool": next_tool,
        "eventually_succeeded": eventually_succeeded,
    }


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file, returning None on any error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def extract_run_events(run: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all permission events from one run's steps."""
    base = get_artifact_base(run["artifact_uri"])
    if not base:
        return []
    conv_dir = base / "conversation_data"
    if not conv_dir.exists():
        return []

    start_ms = run["start_time"]
    start_dt = datetime.fromtimestamp(start_ms / 1000) if start_ms else None
    date_str = start_dt.strftime("%Y-%m-%d") if start_dt else ""
    time_str = start_dt.strftime("%H:%M:%S") if start_dt else ""
    hour = start_dt.hour if start_dt else None
    start_iso = start_dt.isoformat() if start_dt else ""

    events: List[Dict[str, Any]] = []
    for conv_file in sorted(conv_dir.glob("step_*_conversation.json")):
        try:
            step = int(conv_file.name.split("_")[1])
        except (ValueError, IndexError):
            step = -1

        conv = load_json(conv_file)
        if not conv:
            continue
        msgs = conv.get("response_data", {}).get("raw_response", {}).get("messages", [])
        if not msgs:
            continue

        idx = index_step(msgs)
        init, result = idx["init"], idx["result"]
        denials = result.get("permission_denials") or []
        if not denials:
            continue

        # Per-step master data (all_params overrides DB params when present).
        params = load_json(conv_dir / f"step_{step}_all_params.json") or {}
        db_params = run["db_params"]
        tools_available = set(init.get("tools", []))
        usage = result.get("usage") or {}

        # First line of the step prompt = the workflow prompt identity.
        workflow_prompt = ""
        prompt_file = conv_dir / f"step_{step}_prompt.txt"
        if prompt_file.exists():
            try:
                for line in prompt_file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        workflow_prompt = line.strip()[:120]
                        break
            except OSError:
                pass

        # retry_count: how many times each exact (tool, input) was denied this step.
        denial_counts: Dict[str, int] = {}
        for d in denials:
            key = (
                d.get("tool_name", "")
                + "|"
                + json.dumps(d.get("tool_input", {}), sort_keys=True)
            )
            denial_counts[key] = denial_counts.get(key, 0) + 1

        common = {
            "run_id": run["run_id"],
            "session_id": init.get("session_id"),
            "date": date_str,
            "time": time_str,
            "hour": hour,
            "start_time": start_iso,
            "run_status": run["status"],
            "run_name": run["name"],
            "workflow_prompt": workflow_prompt,
            "step": step,
            "step_name": params.get("step_name"),
            "branch_name": params.get("branch_name"),
            "model": init.get("model") or params.get("model") or db_params.get("model"),
            "provider": params.get("provider") or db_params.get("provider"),
            "claude_code_version": init.get("claude_code_version"),
            "permission_mode": init.get("permissionMode"),
            "working_directory": params.get("working_directory")
            or db_params.get("working_directory")
            or init.get("cwd"),
            "num_tools_available": len(tools_available),
            "mcp_servers": ",".join(
                s.get("name", "") for s in (init.get("mcp_servers") or [])
            ),
            "step_num_turns": result.get("num_turns"),
            "step_total_cost_usd": result.get("total_cost_usd"),
            "step_duration_ms": result.get("duration_ms"),
            "step_stop_reason": result.get("stop_reason"),
            "step_is_error": result.get("is_error"),
            "api_error_status": result.get("api_error_status"),
            "step_input_tokens": usage.get("input_tokens"),
            "step_output_tokens": usage.get("output_tokens"),
        }

        for d in denials:
            tool_name = d.get("tool_name", "")
            tool_input = d.get("tool_input", {})
            tool_use_id = d.get("tool_use_id", "")
            res = idx["results"].get(tool_use_id, {})
            followup = analyze_followup(
                tool_use_id, tool_name, tool_input, idx["calls"], idx["results"]
            )
            event = dict(common)
            event.update(
                {
                    "tool_name": tool_name,
                    "mcp_server": mcp_server(tool_name),
                    "tool_category": tool_category(tool_name),
                    "tool_input": tool_input,
                    "tool_use_id": tool_use_id,
                    "outcome": "denied",
                    "was_available": tool_name in tools_available,
                    "retry_count": denial_counts.get(
                        tool_name + "|" + json.dumps(tool_input, sort_keys=True), 1
                    ),
                    "result_is_error": res.get("is_error"),
                    "user_reply": res.get("text", ""),
                    "followup_action": followup["followup_action"],
                    "next_tool": followup["next_tool"],
                    "eventually_succeeded": followup["eventually_succeeded"],
                }
            )
            events.append(event)
    return events


CSV_COLUMNS = [
    "date",
    "time",
    "hour",
    "start_time",
    "run_id",
    "session_id",
    "step",
    "step_name",
    "branch_name",
    "workflow_prompt",
    "model",
    "provider",
    "claude_code_version",
    "permission_mode",
    "working_directory",
    "run_status",
    "mcp_servers",
    "num_tools_available",
    "tool_name",
    "mcp_server",
    "tool_category",
    "outcome",
    "was_available",
    "retry_count",
    "result_is_error",
    "followup_action",
    "next_tool",
    "eventually_succeeded",
    "step_num_turns",
    "step_total_cost_usd",
    "step_duration_ms",
    "step_stop_reason",
    "step_is_error",
    "api_error_status",
    "step_input_tokens",
    "step_output_tokens",
    "tool_input",
    "user_reply",
]


def write_outputs(events: List[Dict[str, Any]], output_dir: Path) -> None:
    """Write JSONL (full) and CSV (flat) datasets."""
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = output_dir / "permission_events.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    csv_path = output_dir / "permission_events.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for e in events:
            row = dict(e)
            row["tool_input"] = json.dumps(e.get("tool_input", {}), ensure_ascii=False)
            row["user_reply"] = (e.get("user_reply") or "").replace("\n", " ")[:300]
            writer.writerow(row)

    print(f"\nWrote {len(events)} events:")
    print(f"  {jsonl_path}")
    print(f"  {csv_path}")


def print_summary(events: List[Dict[str, Any]]) -> None:
    """Print aggregate stats over the extracted events."""
    from collections import Counter

    if not events:
        print("\nNo permission events found.")
        return
    by_tool = Counter(e["tool_name"] for e in events)
    by_branch = Counter(e.get("branch_name") or "(unknown)" for e in events)
    by_date = Counter(e["date"] for e in events)
    by_followup = Counter(e["followup_action"] for e in events)
    runs = {e["run_id"] for e in events}
    recovered = sum(1 for e in events if e["eventually_succeeded"])
    wasted_loops = sum(1 for e in events if (e.get("retry_count") or 1) >= 3)
    max_retry = max((e.get("retry_count") or 1) for e in events)

    print("\n" + "=" * 60)
    print(f"SUMMARY: {len(events)} events across {len(runs)} runs")
    print("=" * 60)
    print(f"eventually_succeeded (same call later worked): {recovered}")
    print(f"events in a wasted denial loop (retry_count>=3): {wasted_loops}")
    print(f"max retry_count for a single (tool+input): {max_retry}")
    print("\nTop tools denied:")
    for t, c in by_tool.most_common(12):
        print(f"  {c:6d}  {t}")
    print("\nFollow-up action after denial:")
    for a, c in by_followup.most_common():
        print(f"  {c:6d}  {a}")
    print("\nEvents per branch (top 10):")
    for b, c in by_branch.most_common(10):
        print(f"  {c:6d}  {b}")
    print(f"\nDistinct days with events: {len(by_date)}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract permission (approval/denial) events from MLflow artifacts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--limit", type=int, help="Max runs to scan (default: all)")
    parser.add_argument(
        "--output",
        type=str,
        default=".ml_flow_analysis",
        help="Output directory (default: .ml_flow_analysis)",
    )
    parser.add_argument(
        "--db-path", type=str, help="Path to MLflow SQLite database (auto-detected)"
    )
    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else get_mlflow_db_path()
    if not db_path.exists():
        print(f"Error: MLflow database not found at {db_path}")
        return

    print(f"Database: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        runs = get_runs(conn, args.limit)
        print(f"Scanning {len(runs)} runs...")
        events: List[Dict[str, Any]] = []
        for i, run in enumerate(runs, 1):
            events.extend(extract_run_events(run))
            if i % 200 == 0:
                print(f"  ...{i}/{len(runs)} runs, {len(events)} events so far")
    finally:
        conn.close()

    write_outputs(events, Path(args.output))
    print_summary(events)


if __name__ == "__main__":
    main()
