"""Interactive source: tool-use events from Claude Code transcripts.

Reads Claude Code's own session logs under
``~/.claude/projects/<sanitised-project>/*.jsonl`` (one file per session; *not*
MLflow). ``Bash`` and native tools are exposed and the human approves/rejects,
so this reader emits one event per tool-use call with an ``outcome`` and a
``was_allowlisted`` flag matched against ``.claude/settings*.json``.
"""

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from _permission_common import (  # type: ignore[import-not-found]
    analyze_followup,
    bash_verb,
    mcp_server,
    result_text,
    tool_category,
)

REJECTION_MARKER = "doesn't want to proceed with this tool use"


def sanitize_project_dir(path: Path) -> str:
    """Turn a working directory into Claude Code's transcript-folder name.

    Claude replaces every non-alphanumeric char with '-', e.g.
    ``C:\\Users\\Marcus\\...\\mcp_coder`` -> ``C--Users-Marcus-...-mcp-coder``.
    """
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def default_transcript_dir(project_dir: Path) -> Path:
    """Locate the transcript folder for a project under ~/.claude/projects/."""
    return Path.home() / ".claude" / "projects" / sanitize_project_dir(project_dir)


def load_allowlist(project_dir: Path) -> Dict[str, Any]:
    """Parse .claude/settings*.json permissions.allow into mcp + bash rules.

    Returns ``{"mcp": set[str], "bash_prefixes": list[str], "bash_exact": set[str]}``.
    Bash entries look like ``Bash(git rebase:*)`` (prefix) or ``Bash(exact cmd)``.
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

    Note: checks the whole command string; it does not split on ``&&``/``|`` the
    way Claude Code does, so treat as a close estimate.
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
