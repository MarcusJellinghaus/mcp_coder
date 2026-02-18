#!/usr/bin/env python3
"""
compact_diff.py - Logical git diff that strips moved code blocks.

Standard git diff shows moved code as full deletions + additions, inflating
diffs by thousands of lines. This script:
  1. Runs git diff with rename/copy detection (collapses file-level moves)
  2. Parses the unified diff to collect all removed and added lines
  3. Lines appearing as BOTH removed and added (across any file) are "moved"
  4. Consecutive moved blocks of >= min_block lines are replaced with a summary

Usage:
    python tools/compact_diff.py [base_branch] [--clipboard] [--stat] [--min-block N]

Examples:
    python tools/compact_diff.py                     # print compact diff vs main
    python tools/compact_diff.py feature/parent      # vs specific branch
    python tools/compact_diff.py --clipboard         # copy LLM prompt to clipboard
    python tools/compact_diff.py --stat              # stat summary only
    python tools/compact_diff.py --min-block 5       # require 5-line blocks to summarise
"""

from __future__ import annotations

import argparse
import io
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pyperclip
import git as gitpython

MIN_CONTENT_LENGTH = 10   # ignore short lines like `pass`, `return` when matching moves
MIN_BLOCK_DEFAULT = 3     # consecutive lines needed to call a block "moved"
DEFAULT_PATHS = ["src/", "tests/"]


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Hunk:
    header: str
    lines: list[str] = field(default_factory=list)


@dataclass
class FileDiff:
    headers: list[str] = field(default_factory=list)
    hunks: list[Hunk] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def detect_base_branch(repo: gitpython.Repo) -> str:
    """Return the default remote branch (main/master) via gitpython."""
    try:
        ref = repo.remote("origin").refs["HEAD"]
        return ref.reference.name.split("/")[-1]
    except Exception:
        pass
    for name in ("main", "master"):
        try:
            repo.commit(name)
            return name
        except gitpython.BadName:
            pass
    return "main"


def run_git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    return result.stdout


def git_stat(base: str, paths: list[str]) -> str:
    return run_git("diff", "--stat",
                   "--find-renames=40%", "--find-copies=40%", "--find-copies-harder",
                   f"{base}...HEAD", "--", *paths)


def git_diff(base: str, paths: list[str]) -> str:
    return run_git("diff",
                   "--find-renames=40%", "--find-copies=40%", "--find-copies-harder",
                   "--diff-algorithm=histogram",
                   "--unified=5", "--no-prefix",
                   f"{base}...HEAD", "--", *paths)


# ---------------------------------------------------------------------------
# Unified diff parser
# ---------------------------------------------------------------------------

def parse_diff(text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    current: FileDiff | None = None
    current_hunk: Hunk | None = None

    for line in text.splitlines(keepends=True):
        if line.startswith("diff --git"):
            if current_hunk is not None and current is not None:
                current.hunks.append(current_hunk)
                current_hunk = None
            if current is not None:
                files.append(current)
            current = FileDiff(headers=[line])
        elif line.startswith("@@") and current is not None:
            if current_hunk is not None:
                current.hunks.append(current_hunk)
            current_hunk = Hunk(header=line)
        elif current_hunk is not None:
            current_hunk.lines.append(line)
        elif current is not None:
            current.headers.append(line)

    if current_hunk is not None and current is not None:
        current.hunks.append(current_hunk)
    if current is not None:
        files.append(current)
    return files


# ---------------------------------------------------------------------------
# Moved block detection
# ---------------------------------------------------------------------------

def _is_significant(content: str) -> bool:
    return len(content.strip()) >= MIN_CONTENT_LENGTH


def collect_moved_lines(files: list[FileDiff]) -> set[str]:
    """Lines present as both removals and additions across all files = moved."""
    removed: set[str] = set()
    added: set[str] = set()
    for fd in files:
        for hunk in fd.hunks:
            for line in hunk.lines:
                content = line[1:].strip()
                if not _is_significant(content):
                    continue
                if line.startswith("-"):
                    removed.add(content)
                elif line.startswith("+"):
                    added.add(content)
    return removed & added


def render_compact(files: list[FileDiff], moved: set[str], min_block: int) -> str:
    """Render the diff, replacing moved blocks with one-line summaries."""
    out: list[str] = []

    for fd in files:
        rendered_hunks: list[tuple[str, list[str]]] = []

        for hunk in fd.hunks:
            rendered: list[str] = []
            lines = hunk.lines
            i = 0
            while i < len(lines):
                line = lines[i]
                sign = line[0] if line and line[0] in "+-" else " "

                if sign not in "+-":
                    rendered.append(line)
                    i += 1
                    continue

                # Gather consecutive lines with the same sign
                j = i
                while j < len(lines) and lines[j].startswith(sign):
                    j += 1
                block = lines[i:j]

                # Count lines in this block that are "moved"
                moved_count = sum(
                    1 for ln in block
                    if _is_significant(ln[1:].strip()) and ln[1:].strip() in moved
                )
                total_significant = sum(1 for ln in block if _is_significant(ln[1:].strip()))

                is_moved_block = (
                    len(block) >= min_block
                    and total_significant >= min_block
                    and moved_count >= total_significant * 0.8
                )

                if is_moved_block:
                    verb = "moved away" if sign == "-" else "moved here"
                    rendered.append(f"  ~~~ {len(block)} lines {verb} (unchanged) ~~~\n")
                else:
                    rendered.extend(block)
                i = j

            has_real_change = any(
                ln.startswith(("+", "-")) and "~~~ " not in ln for ln in rendered
            )
            has_summary = any("~~~ " in ln for ln in rendered)
            if has_real_change or has_summary:
                rendered_hunks.append((hunk.header, rendered))

        if rendered_hunks:
            out.extend(fd.headers)
            for header, lines in rendered_hunks:
                out.append(header)
                out.extend(lines)

    return "".join(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Force UTF-8 on stdout — Windows defaults to CP1252 when redirected to a file
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("base_branch", nargs="?", help="Base branch (default: auto-detect)")
    parser.add_argument("--clipboard", action="store_true",
                        help="Copy LLM review prompt to clipboard instead of printing")
    parser.add_argument("--stat", action="store_true", help="Show diff stat only, no full diff")
    parser.add_argument("--min-block", type=int, default=MIN_BLOCK_DEFAULT,
                        help=f"Min consecutive lines to summarise as a moved block (default: {MIN_BLOCK_DEFAULT})")
    parser.add_argument("--paths", nargs="+", default=DEFAULT_PATHS,
                        help=f"Paths to diff (default: {DEFAULT_PATHS})")
    parser.add_argument("--no-filter", action="store_true",
                        help="Skip moved-block filtering (raw compact diff only)")
    args = parser.parse_args()

    # Repo + branch discovery via gitpython
    try:
        repo = gitpython.Repo(Path.cwd(), search_parent_directories=True)
    except gitpython.InvalidGitRepositoryError:
        print("Error: not in a git repository", file=sys.stderr)
        sys.exit(1)

    base = args.base_branch or detect_base_branch(repo)
    current = repo.active_branch.name

    print(f"Current branch: {current}", file=sys.stderr)
    print(f"Base branch:    {base}", file=sys.stderr)
    print(file=sys.stderr)

    stat = git_stat(base, args.paths)
    print("=== Diff summary ===", file=sys.stderr)
    print(stat, file=sys.stderr)

    if args.stat:
        return

    raw = git_diff(base, args.paths)
    raw_lines = raw.count("\n")

    if args.no_filter:
        output = raw
        print(f"Lines: {raw_lines} (no filtering)", file=sys.stderr)
    else:
        files = parse_diff(raw)
        moved = collect_moved_lines(files)
        output = render_compact(files, moved, args.min_block)
        compact_lines = output.count("\n")
        print(f"Lines: {raw_lines} → {compact_lines} "
              f"({raw_lines - compact_lines} moved-block lines summarised)\n", file=sys.stderr)

    if args.clipboard:
        prompt = (
            "## Code Review Request\n\n"
            "Review the changes below and identify any issues.\n"
            "Lines marked `~~~ N lines moved here/away (unchanged) ~~~` are pure code moves"
            " — focus on the remaining additions and deletions.\n\n"
            "### Focus Areas:\n"
            "- Logic errors or bugs\n"
            "- Unnecessary debug code or print statements\n"
            "- Code that could break existing functionality\n"
            "- Compliance with existing architecture principles\n\n"
            "### Output Format:\n"
            "1. **Summary** - What changed (1-2 sentences)\n"
            "2. **Critical Issues** - Must fix before merging\n"
            "3. **Suggestions** - Nice to have improvements\n"
            "4. **Good** - What works well\n\n"
            "Do not perform any action. Just present the code review.\n\n"
            f"Current branch: {current}\n"
            f"Base branch:    {base}\n\n"
            f"=== DIFF SUMMARY ===\n\n{stat}\n"
            f"=== GIT DIFF ===\n\n{output}"
        )
        pyperclip.copy(prompt)
        print("Copied to clipboard.", file=sys.stderr)
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
