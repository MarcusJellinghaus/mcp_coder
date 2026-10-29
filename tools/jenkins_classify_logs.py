#!/usr/bin/env python3
"""Tag downloaded Jenkins console logs with known issue ids.

Reads the ``index.csv`` written by ``jenkins_download_logs.py``, searches each
log for the signatures in ``jenkins_issue_patterns.toml`` and rewrites the
index with the target repo, the issue ids found and the installed versions of
the mcp packages (repo venv and tool env). Prints per-id counts, with
unsupported target repos reported separately, and the logs nothing matched.
Workflow: ``tools/jenkins_issue_analysis.md``.

Usage:
    python tools/jenkins_classify_logs.py [--logdir DIR] [--patterns FILE]
"""

import argparse
import csv
import re
import sys
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

DEFAULT_LOGDIR = Path(".scratch/jenkins_logs")
DEFAULT_PATTERNS = Path(__file__).with_name("jenkins_issue_patterns.toml")
INDEX_FILENAME = "index.csv"
REPO_COLUMN = "repo"
ISSUES_COLUMN = "issue_identified"
MISMATCH_COLUMN = "version_mismatch"


@dataclass(frozen=True)
class Patterns:
    """Compiled contents of the patterns file."""

    signatures: list[tuple[str, re.Pattern[str]]]
    pre_workflow: frozenset[str]
    no_status_id: str
    blocked_trigger: str
    blocked_text: re.Pattern[str]
    blocked_reasons: list[tuple[str, re.Pattern[str]]]
    blocked_other: str
    unsupported_repos: frozenset[str]
    packages: tuple[str, ...]
    tool_env_marker: str


def load_patterns(path: Path) -> Patterns:
    """Load and compile the patterns file.

    Args:
        path: TOML patterns file

    Returns:
        Compiled patterns
    """
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    signatures = data["signature"]
    blocked = data["blocked"]
    return Patterns(
        signatures=[(s["id"], re.compile(s["regex"])) for s in signatures],
        pre_workflow=frozenset(s["id"] for s in signatures if s.get("pre_workflow")),
        no_status_id=data["classifier"]["no_status_id"],
        blocked_trigger=blocked["trigger"],
        blocked_text=re.compile(blocked["text"]),
        blocked_reasons=[
            (r["id"], re.compile(r["regex"], re.IGNORECASE)) for r in blocked["reason"]
        ],
        blocked_other=blocked["other"],
        unsupported_repos=frozenset(data["classifier"]["unsupported_repos"]),
        packages=tuple(data["versions"]["packages"]),
        tool_env_marker=data["versions"]["tool_env_marker"],
    )


def classify(text: str, patterns: Patterns) -> list[str]:
    """Return the issue ids found in one log.

    Args:
        text: Console log
        patterns: Compiled patterns

    Returns:
        Matching signature ids in file order, then the blocked reason (when
        the trigger matched) and the no-status id (when a pre-workflow
        signature matched)
    """
    ids = [issue_id for issue_id, rx in patterns.signatures if rx.search(text)]
    if patterns.blocked_trigger in ids:
        match = patterns.blocked_text.search(text)
        reason = match.group(1) if match else ""
        ids.append(
            next(
                (sub for sub, rx in patterns.blocked_reasons if rx.search(reason)),
                patterns.blocked_other,
            )
        )
    if patterns.pre_workflow.intersection(ids):
        ids.append(patterns.no_status_id)
    return ids


def extract_versions(text: str, patterns: Patterns) -> dict[str, str]:
    """Find the installed versions of the mcp packages in one log.

    Lines like ``mcp-coder 0.1.21`` or `` + mcp-coder==0.1.21 (from ...)``
    before the tool env marker give the repo venv version (last one wins,
    later installs replace earlier ones); after it, the tool env version
    (first one wins).

    Args:
        text: Console log
        patterns: Compiled patterns

    Returns:
        Column name ("venv_<pkg>" / "tool_<pkg>") to version, for every
        package found
    """
    names = "|".join(re.escape(p) for p in patterns.packages)
    line_rx = re.compile(rf"^(?: \+ )?({names})(?:==| )(\d\S*)", re.MULTILINE)
    venv_part, _, tool_part = text.partition(patterns.tool_env_marker)
    found: dict[str, str] = {}
    for match in line_rx.finditer(venv_part):
        found[f"venv_{match[1]}"] = match[2]
    for match in line_rx.finditer(tool_part):
        found.setdefault(f"tool_{match[1]}", match[2])
    return found


def version_mismatch(versions: dict[str, str], packages: tuple[str, ...]) -> str:
    """List the packages whose venv and tool env versions differ.

    Args:
        versions: Output of extract_versions
        packages: Packages to compare

    Returns:
        Package names joined by ";", "" when none differ or one side is missing
    """
    return ";".join(
        p
        for p in packages
        if versions.get(f"venv_{p}")
        and versions.get(f"tool_{p}")
        and versions[f"venv_{p}"] != versions[f"tool_{p}"]
    )


def target_repo(display_name: str) -> str:
    """Return the repo part of a workflow build label.

    Args:
        display_name: Build display name, e.g. "mcp_coder - #1346 - implement - #2559"

    Returns:
        "mcp_coder" for the example, "" when the name has no " - "
    """
    repo, sep, _ = display_name.partition(" - ")
    return repo if sep else ""


def _version_columns(packages: tuple[str, ...]) -> list[str]:
    return [f"{env}_{p}" for env in ("venv", "tool") for p in packages]


def tag_rows(rows: list[dict[str, str]], logdir: Path, patterns: Patterns) -> None:
    """Add repo, issue ids, versions and mismatch to each index row in place.

    Args:
        rows: index.csv rows (need "file" and "display_name")
        logdir: Directory holding the logs
        patterns: Compiled patterns
    """
    for row in rows:
        text = (logdir / row["file"]).read_text(encoding="utf-8", errors="replace")
        versions = extract_versions(text, patterns)
        row[REPO_COLUMN] = target_repo(row.get("display_name", ""))
        row[ISSUES_COLUMN] = ";".join(classify(text, patterns))
        for column in _version_columns(patterns.packages):
            row[column] = versions.get(column, "")
        row[MISMATCH_COLUMN] = version_mismatch(versions, patterns.packages)


def write_rows(path: Path, rows: list[dict[str, str]], patterns: Patterns) -> None:
    """Rewrite the index with the generated columns last.

    Args:
        path: index.csv to write
        rows: Tagged rows
        patterns: Compiled patterns (for the version column names)
    """
    generated = [REPO_COLUMN, ISSUES_COLUMN, *_version_columns(patterns.packages)]
    generated.append(MISMATCH_COLUMN)
    fields = [k for k in rows[0] if k not in generated] + generated
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _id_lines(rows: list[dict[str, str]]) -> list[str]:
    """One report line per issue id: count, last seen, mcp-coder version range."""
    by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in sorted(rows, key=lambda r: r.get("timestamp", "")):
        for issue_id in filter(None, row[ISSUES_COLUMN].split(";")):
            by_id[issue_id].append(row)
    lines = []
    for issue_id, hits in sorted(by_id.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        first, last = (
            h.get("tool_mcp-coder") or h.get("venv_mcp-coder") or "?"
            for h in (hits[0], hits[-1])
        )
        lines.append(
            f"  {len(hits):3}  {issue_id}  last: #{hits[-1].get('number', '?')} "
            f"{hits[-1].get('timestamp', '')[:10]}  mcp-coder: {first} .. {last}"
        )
    return lines


def report(rows: list[dict[str, str]], patterns: Patterns) -> str:
    """Summarise the tagged rows.

    Args:
        rows: Tagged rows
        patterns: Compiled patterns

    Returns:
        Multi-line report text
    """
    supported = [r for r in rows if r[REPO_COLUMN] not in patterns.unsupported_repos]
    unsupported = [r for r in rows if r[REPO_COLUMN] in patterns.unsupported_repos]
    unmatched = [r["file"] for r in rows if not r[ISSUES_COLUMN]]
    mismatched = sum(1 for r in rows if r[MISMATCH_COLUMN])
    lines = [f"{len(rows)} logs, {len(rows) - len(unmatched)} classified"]
    lines.append(f"Supported repos ({len(supported)} logs):")
    lines += _id_lines(supported)
    if unsupported:
        names = ", ".join(sorted(patterns.unsupported_repos))
        lines.append(f"Unsupported repos: {names} ({len(unsupported)} logs):")
        lines += _id_lines(unsupported)
    lines.append(f"venv/tool env version mismatch: {mismatched} logs")
    lines.append(f"Unmatched ({len(unmatched)}):")
    lines += [f"  {name}" for name in unmatched]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the tool.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Exit code: 0 on success, 1 on unreadable patterns, index or logs
    """
    parser = argparse.ArgumentParser(
        description="Tag downloaded Jenkins console logs with known issue ids."
    )
    parser.add_argument(
        "--logdir",
        type=Path,
        default=DEFAULT_LOGDIR,
        help=f"directory with the logs and {INDEX_FILENAME} (default: {DEFAULT_LOGDIR})",
    )
    parser.add_argument(
        "--patterns",
        type=Path,
        default=DEFAULT_PATTERNS,
        help="TOML signatures file (default: jenkins_issue_patterns.toml next to this script)",
    )
    args = parser.parse_args(argv)
    try:
        patterns = load_patterns(args.patterns)
    except (OSError, tomllib.TOMLDecodeError, KeyError, re.error) as e:
        print(f"Error loading patterns '{args.patterns}': {e!r}", file=sys.stderr)
        return 1
    index = args.logdir / INDEX_FILENAME
    try:
        with index.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            print(f"No builds listed in '{index}'")
            return 0
        tag_rows(rows, args.logdir, patterns)
        write_rows(index, rows, patterns)
    except OSError as e:
        print(f"Error reading or writing logs in '{args.logdir}': {e}", file=sys.stderr)
        return 1
    print(report(rows, patterns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
