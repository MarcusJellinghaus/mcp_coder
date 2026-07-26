#!/usr/bin/env python3
"""Bucket interactive Bash commands by *purpose* and flag MCP-tool overlap.

Reads a ``permission_events.jsonl`` produced by
``extract_permission_events.py --source interactive`` and classifies every
``Bash`` call into a purpose (git_read, gh_issue_write, file_read, ...). Each
purpose is mapped to whether an MCP tool already covers it, so the output
separates:

- **duplicates an existing MCP tool** — an advertising / adoption gap (the model
  reached for Bash when an MCP tool exists), and
- **no MCP equivalent** — a candidate for new MCP functionality.

Usage:
    python tools/mlflow/analyze_bash_commands.py
    python tools/mlflow/analyze_bash_commands.py --input .ml_flow_analysis --samples 3
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# purpose -> (existing MCP tool covering it, or None if it's a gap)
PURPOSE_MCP: Dict[str, Optional[str]] = {
    "git_read": "mcp-workspace git (read subcommands)",
    "git_write": None,
    "gh_issue_read": "github_issue_view / github_issue_list",
    "gh_issue_write": None,
    "gh_pr_read": "github_pr_view",
    "gh_pr_write": None,
    "gh_other": None,
    "file_read": "read_file",
    "file_list": "list_directory",
    "file_search": "search_files",
    "file_write": "save_file / edit_file / move_file / delete_this_file",
    "text_proc": None,
    "run_python": None,
    "run_tests": "run_pytest_check",
    "run_checks": "run_mypy_check / run_ruff_check / run_pylint_check / ...",
    "pkg_install": None,
    "mcp_coder": "partial (some Bash(mcp-coder ...) allow-listed)",
    "nav_env": "n/a (shell navigation / env only)",
    "other": None,
}

_GIT_WRITE = {
    "commit", "add", "push", "rebase", "checkout", "reset", "stash", "merge",
    "pull", "cherry-pick", "revert", "restore", "switch", "clean", "mv", "rm",
    "tag", "init", "remote",
}
_GIT_READ = {
    "status", "diff", "log", "show", "branch", "rev-parse", "ls-files",
    "ls-tree", "describe", "blame", "fetch", "merge-base", "cat-file",
    "shortlog", "rev-list", "config",
}
_ISSUE_WRITE = {"create", "edit", "comment", "close", "reopen", "delete", "lock"}
_PR_WRITE = {"create", "edit", "comment", "close", "merge", "review", "ready"}


def effective_command(command: str) -> str:
    """Strip leading env assignments and ``cd <path>`` (&&, ;, newline) wrappers."""
    c = command.strip()
    c = re.sub(r"^(?:\w+=(?:\"[^\"]*\"|'[^']*'|\S+)\s+)+", "", c)
    while True:
        m = re.match(r"^cd\s+(?:\"[^\"]*\"|'[^']*'|\S+)\s*(?:&&|;|\n)\s*", c)
        if not m:
            break
        c = c[m.end() :]
    return c.strip()


def _tokens(command: str) -> List[str]:
    return command.split()


def classify_purpose(command: str) -> str:
    """Classify a raw Bash command string into a purpose bucket."""
    eff = effective_command(command)
    toks = _tokens(eff)
    if not toks:
        return "nav_env"
    verb = toks[0]
    sub = toks[1] if len(toks) > 1 else ""

    if verb == "git":
        if sub in _GIT_WRITE:
            return "git_write"
        if sub in _GIT_READ:
            return "git_read"
        return "git_write"  # unknown git subcommand: treat conservatively
    if verb == "gh":
        area = sub
        action = toks[2] if len(toks) > 2 else ""
        if area == "issue":
            return "gh_issue_write" if action in _ISSUE_WRITE else "gh_issue_read"
        if area == "pr":
            return "gh_pr_write" if action in _PR_WRITE else "gh_pr_read"
        return "gh_other"
    if verb in ("cat", "head", "tail", "less", "more", "type", "bat"):
        # `cat > file <<EOF` / `cat >file` is a heredoc write, not a read.
        return "file_write" if (">" in eff) else "file_read"
    if verb in ("ls", "dir", "tree", "find", "fd"):
        return "file_list"
    if verb in ("grep", "rg", "egrep", "fgrep", "findstr", "ag", "ack"):
        return "file_search"
    if verb in ("sed", "awk", "perl") and "-i" in toks:
        return "file_write"
    if verb in ("echo", "printf") and (">" in eff or ">>" in eff):
        return "file_write"
    if verb in ("tee", "cp", "copy", "mv", "move", "rm", "del", "mkdir", "touch", "rmdir"):
        return "file_write"
    if verb in ("sed", "awk", "perl", "sort", "uniq", "wc", "jq", "cut", "tr", "xargs"):
        return "text_proc"
    if verb in ("echo", "printf"):
        return "nav_env"
    if verb in ("pytest",) or (verb.endswith("python") and "pytest" in eff):
        return "run_tests"
    if verb in ("mypy", "ruff", "pylint", "black", "isort", "tach", "vulture", "bandit", "flake8"):
        return "run_checks"
    if "python" in verb or verb in ("py", "python3"):
        return "run_python"
    if verb in ("pip", "uv", "poetry", "pipx"):
        return "pkg_install"
    if verb.endswith("mcp-coder") or verb == "mcp-coder":
        return "mcp_coder"
    if verb in ("cd", "export", "set", "source", "pushd", "popd", "start"):
        return "nav_env"
    return "other"


def load_bash_events(path: Path) -> List[Dict[str, Any]]:
    """Load Bash events from a permission_events.jsonl (or dir containing it)."""
    if path.is_dir():
        path = path / "permission_events.jsonl"
    events: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            e = json.loads(line)
            if e.get("tool_name") == "Bash":
                events.append(e)
    return events


def command_of(event: Dict[str, Any]) -> str:
    """Pull the raw command string out of an event's tool_input."""
    ti = event.get("tool_input")
    if isinstance(ti, dict):
        return str(ti.get("command", ""))
    return ""


def summarize(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Count purposes and collect sample commands per purpose."""
    by_purpose: "Counter[str]" = Counter()
    samples: Dict[str, List[str]] = defaultdict(list)
    for e in events:
        cmd = command_of(e)
        purpose = classify_purpose(cmd)
        by_purpose[purpose] += 1
        if len(samples[purpose]) < 6:
            samples[purpose].append(" ".join(cmd.split())[:100])
    return {"by_purpose": by_purpose, "samples": samples, "total": len(events)}


def print_report(summary: Dict[str, Any], n_samples: int) -> None:
    """Print the purpose breakdown split by MCP-tool coverage."""
    by_purpose: "Counter[str]" = summary["by_purpose"]
    samples: Dict[str, List[str]] = summary["samples"]

    gaps: List[Tuple[str, int]] = []
    dupes: List[Tuple[str, int]] = []
    for purpose, count in by_purpose.most_common():
        mcp = PURPOSE_MCP.get(purpose)
        (dupes if mcp and mcp not in ("n/a (shell navigation / env only)",) else gaps).append(
            (purpose, count)
        )

    print("=" * 64)
    print(f"BASH BY PURPOSE: {summary['total']} commands")
    print("=" * 64)

    print("\n--- Duplicates an existing MCP tool (advertising / adoption gap) ---")
    for purpose, count in dupes:
        print(f"\n  {count:5d}  {purpose}   → MCP: {PURPOSE_MCP[purpose]}")
        for s in samples[purpose][:n_samples]:
            print(f"           $ {s}")

    print("\n--- No MCP equivalent (candidate new functionality) ---")
    for purpose, count in gaps:
        label = PURPOSE_MCP.get(purpose) or "(none)"
        print(f"\n  {count:5d}  {purpose}   → MCP: {label}")
        for s in samples[purpose][:n_samples]:
            print(f"           $ {s}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bucket interactive Bash commands by purpose vs MCP-tool coverage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input",
        type=str,
        default=".ml_flow_analysis",
        help="Dataset dir or .jsonl file (default: .ml_flow_analysis)",
    )
    parser.add_argument(
        "--samples", type=int, default=3, help="Sample commands to print per purpose"
    )
    args = parser.parse_args()

    path = Path(args.input)
    if path.is_dir():
        path = path / "permission_events.jsonl"
    if not path.exists():
        print(f"Error: dataset not found at {path}")
        print("Run: extract_permission_events.py --source interactive")
        return

    events = load_bash_events(path)
    print_report(summarize(events), args.samples)


if __name__ == "__main__":
    main()
