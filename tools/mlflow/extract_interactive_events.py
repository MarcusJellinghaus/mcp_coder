#!/usr/bin/env python3
"""Extract tool-use / permission events from *interactive* Claude Code sessions.

Companion to ``extract_permission_events.py``. That tool reads mcp-coder's
**headless** MLflow runs, where only the MCP toolset is exposed (no ``Bash``) and
non-allow-listed calls are auto-denied. This tool reads the **interactive**
sessions instead — the Claude Code TUI/CLI transcripts under
``~/.claude/projects/<project>/*.jsonl`` — where ``Bash`` and the native tools
*are* exposed and the human approves or rejects calls.

Schema of a transcript (one JSON object per line):

- ``type: assistant`` → ``message.content[]`` holds ``{type: tool_use, id, name,
  input}`` blocks.
- ``type: user`` → ``message.content[]`` holds ``{type: tool_result,
  tool_use_id, content, is_error}``; a **user rejection** has ``is_error: true``
  and content containing "doesn't want to proceed with this tool use".

It emits the same event schema as ``extract_permission_events.py`` (so
``analyze_permission_events.py`` can consume it) plus interactive-only fields:

- ``source``          = "interactive"
- ``outcome``         = executed / denied_by_user / interrupted / error
- ``was_allowlisted`` = is the tool on ``.claude/settings*.json`` permissions.allow
  (True/False for ``mcp__*`` tools, None when it can't be determined, e.g. Bash)
- ``bash_verb``       = first token of a Bash command (for grouping)

The key thing the headless data can't show: **which executed calls were not on
the allow-list** — i.e. what a human actually had to approve.

Usage:
    python tools/mlflow/extract_interactive_events.py
    python tools/mlflow/extract_interactive_events.py --project-dir /path/to/repo
    python tools/mlflow/extract_interactive_events.py --transcripts-dir ~/.claude/projects/foo
"""

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REJECTION_MARKER = "doesn't want to proceed with this tool use"


def sanitize_project_dir(path: Path) -> str:
    """Turn a working directory into Claude Code's transcript-folder name.

    Claude replaces every non-alphanumeric char with '-', e.g.
    ``C:\\Users\\Marcus\\Documents\\GitHub\\mcp_coder`` ->
    ``C--Users-Marcus-Documents-GitHub-mcp-coder``.
    """
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def default_transcript_dir(project_dir: Path) -> Path:
    """Locate the transcript folder for a project under ~/.claude/projects/."""
    return Path.home() / ".claude" / "projects" / sanitize_project_dir(project_dir)


def mcp_server(tool_name: str) -> str:
    """Extract the MCP server name from a tool name (mcp__<server>__<tool>)."""
    if tool_name.startswith("mcp__"):
        return tool_name[5:].partition("__")[0]
    return "(native)"


def tool_category(tool_name: str) -> str:
    """Rough category for grouping (read / write / exec / git / github / bash / other)."""
    n = tool_name.lower()
    if n == "bash":
        return "bash"
    if "github" in n:
        return "github"
    if any(k in n for k in ("git_", "__git", "branch_status", "base_branch")):
        return "git"
    if any(k in n for k in ("read", "search", "list", "glob", "grep", "find_ref")):
        return "read"
    if any(k in n for k in ("write", "edit", "save_file", "append", "delete", "move_")):
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


def load_allowlist(project_dir: Path) -> Dict[str, Any]:
    """Parse .claude/settings*.json permissions.allow into mcp + bash rules.

    Returns ``{"mcp": set[str], "bash_prefixes": list[str], "bash_exact": set[str]}``.
    Bash entries look like ``Bash(git rebase:*)`` (prefix rule, trailing ``:*``)
    or ``Bash(exact command)``.
    """
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
    """Approximate Claude's Bash allow-matching (prefix / exact) on a command.

    Note: this checks the whole command string against the rules; it does not
    split on ``&&``/``|`` the way Claude Code does, so treat as a close estimate.
    """
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
    text = result.get("text", "")
    if REJECTION_MARKER in text:
        return "denied_by_user"
    if result.get("interrupted"):
        return "interrupted"
    if result.get("is_error"):
        return "error"
    return "executed"


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


def index_transcript(
    lines: List[Dict[str, Any]]
) -> Tuple[List[Tuple[str, str, Dict[str, Any], Dict[str, Any]]], Dict[str, Dict[str, Any]]]:
    """Return ordered tool-use calls and a tool_use_id -> result map.

    Each call is (id, name, input, envelope) where envelope carries timestamp /
    gitBranch / version / cwd from the assistant line.
    """
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
                    interrupted = bool(
                        isinstance(tur, dict) and tur.get("interrupted")
                    )
                    results[b.get("tool_use_id", "")] = {
                        "is_error": bool(b.get("is_error")),
                        "text": result_text(b.get("content")),
                        "interrupted": interrupted,
                    }
    return calls, results


def analyze_followup(
    idx: int,
    calls: List[Tuple[str, str, Dict[str, Any], Dict[str, Any]]],
    results: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """What happened after the call at position idx (retried / switched / recovered)."""
    _, name, inp, _ = calls[idx]
    followup_action = "none (last call)"
    next_tool = ""
    if idx + 1 < len(calls):
        next_tool = calls[idx + 1][1]
        followup_action = (
            "retried_same" if next_tool == name else f"switched_to:{next_tool}"
        )
    eventually_succeeded = False
    for cid, cname, cinp, _ in calls:
        if cname == name and cinp == inp:
            r = results.get(cid)
            if r and not r["is_error"]:
                eventually_succeeded = True
                break
    return {
        "followup_action": followup_action,
        "next_tool": next_tool,
        "eventually_succeeded": eventually_succeeded,
    }


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


def extract_session_events(
    path: Path, allow: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Build one event per tool-use call in a transcript file."""
    calls, results = index_transcript(load_jsonl(path))
    events: List[Dict[str, Any]] = []
    for i, (call_id, name, inp, env) in enumerate(calls):
        if not name:
            continue
        result = results.get(call_id)
        followup = analyze_followup(i, calls, results)
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
                "was_allowlisted": was_allowlisted(name, inp, allow),
                "result_is_error": result.get("is_error") if result else None,
                "user_reply": (result.get("text", "") if result else "")[:300],
                "followup_action": followup["followup_action"],
                "next_tool": followup["next_tool"],
                "eventually_succeeded": followup["eventually_succeeded"],
            }
        )
    return events


CSV_COLUMNS = [
    "source",
    "date",
    "time",
    "session_id",
    "branch_name",
    "claude_code_version",
    "tool_name",
    "mcp_server",
    "tool_category",
    "bash_verb",
    "outcome",
    "was_allowlisted",
    "result_is_error",
    "followup_action",
    "next_tool",
    "eventually_succeeded",
    "tool_input",
    "user_reply",
]


def write_outputs(events: List[Dict[str, Any]], output_dir: Path) -> None:
    """Write JSONL (full) + CSV (flat) datasets."""
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "interactive_events.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    csv_path = output_dir / "interactive_events.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for e in events:
            row = dict(e)
            row["tool_input"] = json.dumps(e.get("tool_input", {}), ensure_ascii=False)[
                :300
            ]
            row["user_reply"] = (e.get("user_reply") or "").replace("\n", " ")[:200]
            writer.writerow(row)
    print(f"\nWrote {len(events)} events:")
    print(f"  {jsonl_path}")
    print(f"  {csv_path}")


def print_summary(events: List[Dict[str, Any]]) -> None:
    """Interactive-specific summary: outcomes, rejections, bash, approval candidates."""
    if not events:
        print("\nNo interactive tool events found.")
        return
    sessions = {e["session_id"] for e in events}
    by_outcome = Counter(e["outcome"] for e in events)
    denied = [e for e in events if e["outcome"] == "denied_by_user"]
    executed = [e for e in events if e["outcome"] == "executed"]
    # "Had to be manually approved": executed calls NOT on the allow-list.
    # Label Bash by its verb so `Bash:gh` etc. are distinguishable.
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


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract tool/permission events from interactive Claude Code transcripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=".",
        help="Repo whose transcripts + allow-list to read (default: current dir)",
    )
    parser.add_argument(
        "--transcripts-dir",
        type=str,
        help="Override the ~/.claude/projects/<project> transcript folder",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".ml_flow_analysis",
        help="Output directory (default: .ml_flow_analysis)",
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    tdir = (
        Path(args.transcripts_dir)
        if args.transcripts_dir
        else default_transcript_dir(project_dir)
    )
    if not tdir.exists():
        print(f"Error: transcript folder not found at {tdir}")
        return

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

    write_outputs(events, Path(args.output))
    print_summary(events)


if __name__ == "__main__":
    main()
