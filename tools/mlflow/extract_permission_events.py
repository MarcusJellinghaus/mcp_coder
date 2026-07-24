#!/usr/bin/env python3
"""Extract permission / tool-use events from Claude Code sessions.

One CLI, two sources (``--source``):

- ``headless`` (default) — mcp-coder's **MLflow** runs. Claude Code runs with a
  restricted MCP tool set and no human, so every call to a non-allow-listed tool
  is auto-denied and recorded as a ``permission_denials`` entry. Native ``Bash``
  is never exposed here. One event per denial.
- ``interactive`` — Claude Code's own **transcripts**
  (``~/.claude/projects/<project>/*.jsonl``). ``Bash`` and native tools *are*
  exposed and the human approves/rejects. One event per tool-use call, with an
  ``outcome`` (executed / denied_by_user / interrupted / error) and
  ``was_allowlisted`` (matched against ``.claude/settings*.json``).

Both sources emit the **same event schema** (with a ``source`` column) to
``permission_events.jsonl`` + ``.csv``, so ``analyze_permission_events.py`` can
consume either. See ``tools/mlflow/README.md`` for the headless-vs-interactive
background.

Usage:
    python tools/mlflow/extract_permission_events.py                       # headless
    python tools/mlflow/extract_permission_events.py --limit 500
    python tools/mlflow/extract_permission_events.py --source interactive
    python tools/mlflow/extract_permission_events.py --source interactive --project-dir /path/to/repo
"""

import argparse
import csv
import json
import re
import sqlite3
import urllib.parse
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from mcp_coder.utils.user_app_data import get_user_app_data_dir

REJECTION_MARKER = "doesn't want to proceed with this tool use"


# ======================================================================
# Shared classifiers / helpers
# ======================================================================
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
        for k in ("save_file", "edit_file", "append", "delete", "move_", "rename_", "write", "edit")
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


# ======================================================================
# Source: headless (MLflow artifacts)
# ======================================================================
def get_mlflow_db_path() -> Path:
    """Get the MLflow database path from config or default location."""
    config_path = get_user_app_data_dir("mcp_coder") / "config.toml"
    if config_path.exists():
        config_text = config_path.read_text(encoding="utf-8")
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


def extract_run_events(run: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all permission-denial events from one headless run's steps."""
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

        params = load_json(conv_dir / f"step_{step}_all_params.json") or {}
        db_params = run["db_params"]
        tools_available = set(init.get("tools", []))
        usage = result.get("usage") or {}

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

        denial_counts: Dict[str, int] = {}
        for d in denials:
            key = (
                d.get("tool_name", "")
                + "|"
                + json.dumps(d.get("tool_input", {}), sort_keys=True)
            )
            denial_counts[key] = denial_counts.get(key, 0) + 1

        common = {
            "source": "headless",
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
                    "bash_verb": bash_verb(tool_name, tool_input),
                    "tool_input": tool_input,
                    "tool_use_id": tool_use_id,
                    "outcome": "denied",
                    "was_available": tool_name in tools_available,
                    "was_allowlisted": None,
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


def collect_headless(args: argparse.Namespace) -> List[Dict[str, Any]]:
    """Scan the MLflow DB + artifacts and return denial events."""
    db_path = Path(args.db_path) if args.db_path else get_mlflow_db_path()
    if not db_path.exists():
        print(f"Error: MLflow database not found at {db_path}")
        return []
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
    return events


# ======================================================================
# Source: interactive (Claude Code transcripts)
# ======================================================================
def sanitize_project_dir(path: Path) -> str:
    """Turn a working directory into Claude Code's transcript-folder name."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def default_transcript_dir(project_dir: Path) -> Path:
    """Locate the transcript folder for a project under ~/.claude/projects/."""
    return Path.home() / ".claude" / "projects" / sanitize_project_dir(project_dir)


def load_allowlist(project_dir: Path) -> Dict[str, Any]:
    """Parse .claude/settings*.json permissions.allow into mcp + bash rules."""
    mcp: Set[str] = set()
    bash_prefixes: List[str] = []
    bash_exact: Set[str] = set()
    for name in ("settings.json", "settings.local.json"):
        path = project_dir / ".claude" / name
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for entry in data.get("permissions", {}).get("allow", []):
            if not isinstance(entry, str):
                continue
            if entry.startswith("mcp__"):
                mcp.add(entry)
            elif entry.startswith("Bash(") and entry.endswith(")"):
                inner = entry[5:-1].strip()
                if inner.endswith(":*"):
                    bash_prefixes.append(inner[:-2].strip())
                else:
                    bash_exact.add(inner)
    return {"mcp": mcp, "bash_prefixes": bash_prefixes, "bash_exact": bash_exact}


def bash_matches(command: str, allow: Dict[str, Any]) -> bool:
    """Approximate Claude's Bash allow-matching (prefix / exact) on a command."""
    command = command.strip()
    if command in allow["bash_exact"]:
        return True
    return any(command.startswith(p) for p in allow["bash_prefixes"] if p)


def was_allowlisted(
    tool_name: str, tool_input: Dict[str, Any], allow: Dict[str, Any]
) -> Optional[bool]:
    """Whether a call was pre-authorised. None when it can't be determined."""
    if tool_name.startswith("mcp__"):
        return tool_name in allow["mcp"]
    if tool_name == "Bash":
        return bash_matches(str(tool_input.get("command", "")), allow)
    return None


def classify_outcome(result: Optional[Dict[str, Any]]) -> str:
    """executed / denied_by_user / interrupted / error / no_result."""
    if result is None:
        return "no_result"
    if REJECTION_MARKER in result.get("text", ""):
        return "denied_by_user"
    if result.get("interrupted"):
        return "interrupted"
    if result.get("is_error"):
        return "error"
    return "executed"


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read a transcript file into a list of JSON objects (skips bad lines)."""
    out: List[Dict[str, Any]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def index_transcript(
    lines: List[Dict[str, Any]]
) -> Tuple[
    List[Tuple[str, str, Dict[str, Any], Dict[str, Any]]], Dict[str, Dict[str, Any]]
]:
    """Return ordered tool-use calls (id, name, input, envelope) and a result map."""
    calls: List[Tuple[str, str, Dict[str, Any], Dict[str, Any]]] = []
    results: Dict[str, Dict[str, Any]] = {}
    for line in lines:
        ltype = line.get("type")
        msg = line.get("message", {})
        content = msg.get("content", []) if isinstance(msg, dict) else []
        if ltype == "assistant" and isinstance(content, list):
            env = {
                "timestamp": line.get("timestamp", ""),
                "branch": line.get("gitBranch", ""),
                "version": line.get("version", ""),
                "cwd": line.get("cwd", ""),
                "session_id": line.get("sessionId", ""),
            }
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    calls.append(
                        (b.get("id", ""), b.get("name", ""), b.get("input", {}), env)
                    )
        elif ltype == "user" and isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    tur = line.get("toolUseResult")
                    interrupted = bool(isinstance(tur, dict) and tur.get("interrupted"))
                    results[b.get("tool_use_id", "")] = {
                        "is_error": bool(b.get("is_error")),
                        "text": result_text(b.get("content")),
                        "interrupted": interrupted,
                    }
    return calls, results


def extract_session_events(
    path: Path, allow: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Build one event per tool-use call in an interactive transcript file."""
    calls, results = index_transcript(load_jsonl(path))
    calls3 = [(c[0], c[1], c[2]) for c in calls]
    events: List[Dict[str, Any]] = []
    for call_id, name, inp, env in calls:
        if not name:
            continue
        result = results.get(call_id)
        followup = analyze_followup(call_id, name, inp, calls3, results)
        ts = env.get("timestamp", "")
        try:
            dt: Optional[datetime] = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            dt = None
        events.append(
            {
                "source": "interactive",
                "session_id": env.get("session_id") or path.stem,
                "run_id": env.get("session_id") or path.stem,
                "date": dt.strftime("%Y-%m-%d") if dt else "",
                "time": dt.strftime("%H:%M:%S") if dt else "",
                "hour": dt.hour if dt else None,
                "start_time": ts,
                "branch_name": env.get("branch") or "(none)",
                "claude_code_version": env.get("version"),
                "working_directory": env.get("cwd"),
                "tool_name": name,
                "mcp_server": mcp_server(name),
                "tool_category": tool_category(name),
                "bash_verb": bash_verb(name, inp),
                "tool_input": inp,
                "tool_use_id": call_id,
                "outcome": classify_outcome(result),
                "was_available": None,
                "was_allowlisted": was_allowlisted(name, inp, allow),
                "retry_count": 1,
                "result_is_error": result.get("is_error") if result else None,
                "user_reply": (result.get("text", "") if result else "")[:300],
                "followup_action": followup["followup_action"],
                "next_tool": followup["next_tool"],
                "eventually_succeeded": followup["eventually_succeeded"],
            }
        )
    return events


def collect_interactive(args: argparse.Namespace) -> List[Dict[str, Any]]:
    """Scan interactive transcripts and return tool-use events."""
    project_dir = Path(args.project_dir).resolve()
    tdir = (
        Path(args.transcripts_dir)
        if args.transcripts_dir
        else default_transcript_dir(project_dir)
    )
    if not tdir.exists():
        print(f"Error: transcript folder not found at {tdir}")
        return []
    allow = load_allowlist(project_dir)
    print(f"Transcripts: {tdir}")
    print(
        f"Allow rules: {len(allow['mcp'])} mcp tools, "
        f"{len(allow['bash_prefixes']) + len(allow['bash_exact'])} bash patterns"
    )
    files = sorted(tdir.glob("*.jsonl"))
    print(f"Scanning {len(files)} sessions...")
    events: List[Dict[str, Any]] = []
    for path in files:
        events.extend(extract_session_events(path, allow))
    return events


# ======================================================================
# Shared output + summaries
# ======================================================================
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


def print_summary_headless(events: List[Dict[str, Any]]) -> None:
    """Aggregate stats over headless denial events."""
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
    print(f"HEADLESS: {len(events)} denial events across {len(runs)} runs")
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


def print_summary_interactive(events: List[Dict[str, Any]]) -> None:
    """Interactive summary: outcomes, bash usage, rejections, approval candidates."""
    if not events:
        print("\nNo interactive tool events found.")
        return
    sessions = {e["session_id"] for e in events}
    by_outcome = Counter(e["outcome"] for e in events)
    denied = [e for e in events if e["outcome"] == "denied_by_user"]
    executed = [e for e in events if e["outcome"] == "executed"]

    def _label(e: Dict[str, Any]) -> str:
        if e["tool_name"] == "Bash":
            return f"Bash:{e['bash_verb'] or '?'}"
        return str(e["tool_name"])

    approval_candidates = Counter(
        _label(e) for e in executed if e["was_allowlisted"] is False
    )
    bash = [e for e in events if e["tool_name"] == "Bash"]

    print("\n" + "=" * 60)
    print(f"INTERACTIVE: {len(events)} tool calls across {len(sessions)} sessions")
    print("=" * 60)
    print("\nOutcome:")
    for o, c in by_outcome.most_common():
        print(f"  {c:6d}  {o}")
    print(f"\nBash calls: {len(bash)}  (by verb)")
    for v, c in Counter(e["bash_verb"] for e in bash).most_common(12):
        print(f"  {c:6d}  {v or '(empty)'}")
    print(f"\nUser-rejected calls: {len(denied)}  (by tool)")
    for t, c in Counter(e["tool_name"] for e in denied).most_common(12):
        print(f"  {c:6d}  {t}")
    print("\nExecuted but NOT allow-listed (≈ manually approved), by tool:")
    if approval_candidates:
        for t, c in approval_candidates.most_common(15):
            print(f"  {c:6d}  {t}")
    else:
        print("  (none — every executed mcp tool was on the allow-list)")


# ======================================================================
# CLI
# ======================================================================
def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract permission / tool-use events (headless MLflow or interactive transcripts)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source",
        choices=["headless", "interactive"],
        default="headless",
        help="Which sessions to read (default: headless)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".ml_flow_analysis",
        help="Output directory (default: .ml_flow_analysis)",
    )
    # headless
    parser.add_argument("--limit", type=int, help="[headless] Max runs to scan")
    parser.add_argument(
        "--db-path", type=str, help="[headless] Path to MLflow SQLite DB (auto-detected)"
    )
    # interactive
    parser.add_argument(
        "--project-dir",
        type=str,
        default=".",
        help="[interactive] Repo whose transcripts + allow-list to read",
    )
    parser.add_argument(
        "--transcripts-dir",
        type=str,
        help="[interactive] Override the ~/.claude/projects/<project> folder",
    )
    args = parser.parse_args()

    if args.source == "interactive":
        events = collect_interactive(args)
        write_outputs(events, Path(args.output))
        print_summary_interactive(events)
    else:
        events = collect_headless(args)
        write_outputs(events, Path(args.output))
        print_summary_headless(events)


if __name__ == "__main__":
    main()
