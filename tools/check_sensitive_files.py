"""Warn when a pull request changes sensitive files.

A changed file is flagged when its effective level under the base branch's
.mcp-file-access is read-only, when it is .mcp-file-access itself, or when
it is on WATCH_LIST. Matching reuses the MCP server's rules loader; rules and
paths are lower-cased, so Linux CI applies the stricter Windows behaviour.

Prints one GitHub Actions ``::warning`` annotation per flagged file and a
Markdown table, appended to $GITHUB_STEP_SUMMARY when set, else printed.
Advisory only: exits 0 after a completed check, 1 when git fails.

Usage:
    python tools/check_sensitive_files.py --base HEAD^1 --head HEAD
"""

import argparse
import logging
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from mcp_workspace.file_tools.access_rules import (
    READ_ONLY,
    AccessRules,
    load_access_rules,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_FILE = ".mcp-file-access"
WATCH_LIST = (
    "/pyproject.toml",
    "/.claude/agents/",
    "/.claude/skills/",
    "/.github/workflows/",
    "/tools/check_sensitive_files.py",
)
_REGULAR_MODES = (b"100644", b"100755")


@dataclass(frozen=True)
class GitResult:
    """Outcome of one git command."""

    returncode: int
    stdout: bytes
    stderr: str


def run_git(args: Sequence[str]) -> GitResult:
    """Run git in the repository root.

    Args:
        args: Arguments after ``git``.
    """
    cmd = ["git", *args]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, check=False)
    return GitResult(
        result.returncode, result.stdout, result.stderr.decode(errors="replace")
    )


def _git(*args: str) -> bytes:
    """Run git and return its stdout.

    Args:
        *args: Arguments after ``git``.

    Raises:
        SystemExit: If git exits non-zero.
    """
    result = run_git(args)
    if result.returncode != 0:
        raise SystemExit(
            f"git {' '.join(args)} failed ({result.returncode}): "
            f"{result.stderr.strip()}"
        )
    return result.stdout


def _load(data: bytes) -> AccessRules:
    """Load rules from bytes via the MCP server's loader.

    Args:
        data: Content of a rules file.
    """
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, RULES_FILE).write_bytes(data)
        return load_access_rules(Path(tmp))


def _base_rules(base: str) -> tuple[AccessRules | None, dict[int, str]]:
    """Load the base branch's rules, lower-cased for matching.

    Args:
        base: Git ref whose rules file applies.

    Returns:
        The lower-cased rules and the original pattern per line number, or
        ``(None, {})`` when the rules file is absent or invalid.
    """
    listing = _git("ls-tree", "-z", base, "--", RULES_FILE)
    if not listing:
        print(f"No {RULES_FILE} on {base}: read-only rule check skipped.")
        return None, {}
    problems: list[str]
    original = lowered = AccessRules()
    if listing.split(b" ", 1)[0] not in _REGULAR_MODES:
        problems = ["not a regular file"]
    else:
        raw = _git("show", f"{base}:{RULES_FILE}")
        try:
            original = _load(raw)
            problems = list(original.problems)
            if not problems:
                lowered = _load(raw.decode("utf-8-sig").lower().encode("utf-8"))
                problems = list(lowered.problems)
        except (re.error, ValueError) as exc:
            problems = [f"pattern error: {exc}"]
    if problems:
        message = (
            f"{RULES_FILE} on {base} is invalid ({'; '.join(problems)}). "
            "The MCP server treats every committed file as read-only while "
            "the rules file is invalid; read-only rule matching skipped."
        )
        print("::warning::" + _escape_data(message))
        return None, {}
    return lowered, {rule.line: rule.pattern for rule in original.rules}


def _reasons(
    path: str,
    rules: AccessRules | None,
    patterns: dict[int, str],
    watch: AccessRules,
) -> list[str]:
    """List why a changed path is sensitive.

    Args:
        path: Changed path as git reports it.
        rules: Lower-cased base rules, or None to skip read-only matching.
        patterns: Original rule pattern per line number.
        watch: Rules built from WATCH_LIST.
    """
    lowered = path.lower()
    reasons = []
    if rules is not None:
        rule = rules.match(lowered)
        if rule is not None and rule.level == READ_ONLY:
            reasons.append(f"read-only rule {patterns[rule.line]}")
    if lowered == RULES_FILE:
        reasons.append("rules file")
    watched = watch.match(lowered)
    if watched is not None:
        reasons.append(f"watch list {watched.pattern}")
    return reasons


def _escape_data(text: str) -> str:
    """Escape a workflow command message.

    Args:
        text: Message text.
    """
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_property(text: str) -> str:
    """Escape a workflow command property value.

    Args:
        text: Property value.
    """
    return _escape_data(text).replace(":", "%3A").replace(",", "%2C")


def _escape_cell(text: str) -> str:
    """Escape text for one Markdown table cell.

    Args:
        text: Cell text.
    """
    return text.replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _summary(flagged: dict[str, list[str]]) -> str:
    """Build the Markdown summary of flagged files.

    Args:
        flagged: Reasons per flagged path.
    """
    if not flagged:
        return "No sensitive files changed.\n"
    lines = [
        "## Sensitive files changed",
        "",
        "| File | Reasons |",
        "|---|---|",
    ]
    for path, reasons in flagged.items():
        lines.append(f"| {_escape_cell(path)} | {_escape_cell('; '.join(reasons))} |")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    """Warn about sensitive files changed between base and head.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.
    """
    parser = argparse.ArgumentParser(
        description="Warn when a pull request changes sensitive files."
    )
    parser.add_argument("--base", required=True, help="Base ref; its rules apply.")
    parser.add_argument("--head", required=True, help="Head ref of the PR.")
    args = parser.parse_args(argv)

    merge_base = _git("merge-base", args.base, args.head).decode().strip()
    diff = _git("diff", "--name-only", "--no-renames", "-z", merge_base, args.head)
    paths = [p.decode("utf-8", errors="replace") for p in diff.split(b"\0") if p]

    rules, patterns = _base_rules(args.base)
    watch = _load("".join(f"read-only {p}\n" for p in WATCH_LIST).encode())
    flagged = {p: r for p in paths if (r := _reasons(p, rules, patterns, watch))}

    for path, reasons in flagged.items():
        print(
            f"::warning file={_escape_property(path)}::"
            f"{_escape_data('; '.join(reasons))}"
        )
    summary = _summary(flagged)
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with Path(step_summary).open("a", encoding="utf-8") as f:
            f.write(summary)
    else:
        print(summary, end="")
    return 0


if __name__ == "__main__":
    logging.getLogger(load_access_rules.__module__).disabled = True
    sys.exit(main())
