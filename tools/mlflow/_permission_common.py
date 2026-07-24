"""Shared helpers + event schema for the permission-event extractors.

Used by ``_source_mlflow.py`` (headless MLflow runs) and
``_source_transcripts.py`` (interactive Claude Code transcripts), both driven by
the single ``extract_permission_events.py`` CLI. Keeping the classifiers,
follow-up analysis, event schema and writers here means the two source readers
stay thin and never drift apart.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast


def mcp_server(tool_name: str) -> str:
    """Extract the MCP server name from a tool name (mcp__<server>__<tool>)."""
    if tool_name.startswith("mcp__"):
        return tool_name[5:].partition("__")[0]
    return "(native)"


def tool_category(tool_name: str) -> str:
    """Rough category for grouping (bash/read/write/exec/git/github/other)."""
    n = tool_name.lower()
    if n == "bash":
        return "bash"
    # github before git: "__github_*" also contains the "__git" substring.
    if "github" in n:
        return "github"
    if any(k in n for k in ("git_", "__git", "branch_status", "base_branch")):
        return "git"
    if any(
        k in n
        for k in (
            "read",
            "search",
            "list",
            "glob",
            "grep",
            "find_ref",
            "library_source",
            "check_file",
            "get_reference",
        )
    ):
        return "read"
    if any(
        k in n
        for k in (
            "save_file",
            "edit_file",
            "append",
            "delete",
            "move_",
            "rename_",
            "write",
            "edit",
        )
    ):
        return "write"
    if any(k in n for k in ("run_", "_check", "format_code", "sleep")):
        return "exec"
    return "other"


def bash_verb(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """First token of a Bash command, for grouping (e.g. git / gh / python)."""
    if tool_name != "Bash":
        return ""
    command = str(tool_input.get("command", "")).strip()
    return command.split()[0] if command else ""


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


def analyze_followup(
    target_id: str,
    target_name: str,
    target_input: Dict[str, Any],
    calls: List[Tuple[str, str, Dict[str, Any]]],
    results: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Determine what the model did after the target call (retry / switch / recover)."""
    order = [c[0] for c in calls]
    followup_action = "none (last call in step)"
    next_tool = ""
    if target_id in order:
        k = order.index(target_id)
        if k + 1 < len(calls):
            next_tool = calls[k + 1][1]
            followup_action = (
                "retried_same"
                if next_tool == target_name
                else f"switched_to:{next_tool}"
            )
    eventually_succeeded = False
    for cid, name, inp in calls:
        if name == target_name and inp == target_input:
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
        return cast(Dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError):
        return None


CSV_COLUMNS = [
    "source",
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
    "bash_verb",
    "outcome",
    "was_available",
    "was_allowlisted",
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
        writer = csv.DictWriter(
            f, fieldnames=CSV_COLUMNS, extrasaction="ignore", restval=""
        )
        writer.writeheader()
        for e in events:
            row = dict(e)
            row["tool_input"] = json.dumps(e.get("tool_input", {}), ensure_ascii=False)[
                :300
            ]
            row["user_reply"] = (e.get("user_reply") or "").replace("\n", " ")[:300]
            writer.writerow(row)

    print(f"\nWrote {len(events)} events:")
    print(f"  {jsonl_path}")
    print(f"  {csv_path}")
