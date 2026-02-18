#!/usr/bin/env python3
"""
git-refactor-diff: Produce minimal diffs that exclude moved-but-unchanged code.

Uses git's --color-moved=dimmed-zebra to detect code that was merely relocated
(within or across files) and strips those lines from the diff output. The result
is a clean unified diff showing only lines that were *actually* added, removed,
or modified — perfect for code review of refactoring branches or for feeding
into an LLM with a limited context window.

How it works:
  1. Runs `git diff` with --color-moved=dimmed-zebra and custom color overrides
     that assign a unique, recognizable ANSI style ("dim white") to all six
     moved-line color slots.
  2. Parses the raw ANSI output line by line. Lines whose coloring matches the
     "moved" style are classified as moved; everything else is kept.
  3. Moved diff lines (those starting with + or -) are dropped. File headers,
     hunk headers, and context lines are preserved so the output remains a
     valid (though potentially sparse) unified diff.
  4. Empty hunks (where all changes were moved) are collapsed to a single
     summary comment like:  # [hunk: all lines were moved, no real changes]
  5. Files where every hunk was purely moved get a one-line summary instead of
     a full diff block.

Requirements:
  - Python 3.8+
  - git 2.17+ (first version with --color-moved support)

Installation:
  Save this file somewhere on your PATH and make it executable:
    chmod +x git_refactor_diff.py

  Or install as a git alias:
    git config --global alias.rdiff '!python3 /path/to/git_refactor_diff.py'

Usage:
  # Compare current branch to main (most common)
  python git_refactor_diff.py main..HEAD

  # Compare two specific commits
  python git_refactor_diff.py abc1234 def5678

  # Compare working tree to HEAD
  python git_refactor_diff.py

  # Pipe to file for LLM consumption
  python git_refactor_diff.py main..HEAD > refactor.diff

  # With extra git diff flags (passed through)
  python git_refactor_diff.py main..HEAD -- src/

  # Show stats summary at the end
  python git_refactor_diff.py --stats main..HEAD

Examples:
  Before (standard git diff of a 1000-line file split into 3 files):
    ~2000 lines of red/green diff (every line appears as both deleted and added)

  After (git-refactor-diff):
    ~50 lines showing only import changes, minor edits, and a summary of which
    blocks were moved where.

Output format:
  The output is a standard unified diff with two additions:
  - Comment lines starting with # summarize moved-only hunks/files
  - A trailing stats block (with --stats) showing lines kept vs stripped

Limitations:
  - git's move detection requires blocks of ≥20 alphanumeric characters.
    Very short moved lines (like bare `pass` or `}`) may not be detected.
  - Indentation changes during a move may prevent detection. Use
    --color-moved-ws=ignore-all-space (enabled by default) to mitigate.
  - This tool post-processes git's output; it does not do its own AST analysis.
    Semantically identical but textually different code won't be detected.

License: MIT
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import TextIO

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# ANSI escape sequence pattern: matches ESC[ ... m (SGR sequences)
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# The marker we use to tag moved lines.  We configure git to color all six
# moved-line slots as "white dim", which produces ANSI codes containing
# SGR 2 (dim) and SGR 37 (white).  We detect any line whose ANSI codes
# include the dim attribute (SGR 2) as a moved line.
#
# Specifically, git emits sequences like:
#   \x1b[2;37m   (dim + white foreground)  -- for dimmed moved lines
#   \x1b[2m      (dim only)               -- variant in some git versions
#
# We look for the dim attribute (code 2) in any SGR sequence on the line.
DIM_CODE_RE = re.compile(r"\x1b\[([0-9;]*;)?2(;[0-9;]*)?m")


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from a string."""
    return ANSI_RE.sub("", text)


def is_moved_line(raw_line: str) -> bool:
    """
    Determine if a raw (ANSI-colored) diff line represents moved code.

    We configured git to use 'dim white' for all moved-line color slots.
    A line is considered moved if it contains an ANSI SGR sequence with
    the dim attribute (code 2).

    Only diff content lines (starting with + or - after stripping ANSI)
    can be moved. Headers and context lines are never classified as moved.
    """
    clean = strip_ansi(raw_line)
    if not clean.startswith(("+", "-")):
        return False
    # Don't classify file headers as moved
    if clean.startswith(("+++", "---")):
        return False
    return bool(DIM_CODE_RE.search(raw_line))


# ---------------------------------------------------------------------------
# Git invocation
# ---------------------------------------------------------------------------

# The six color slots git uses for moved lines in dimmed-zebra mode.
# We set them all to "white dim" so we can reliably detect moved lines
# by looking for the dim ANSI attribute.
MOVED_COLOR_CONFIGS = [
    "-c", "color.diff.oldMoved=white dim",
    "-c", "color.diff.oldMovedAlternative=white dim",
    "-c", "color.diff.newMoved=white dim",
    "-c", "color.diff.newMovedAlternative=white dim",
    "-c", "color.diff.newMovedDimmed=white dim",
    "-c", "color.diff.newMovedAlternativeDimmed=white dim",
]

GIT_DIFF_FLAGS = [
    "--color=always",            # force color output even when piped
    "--color-moved=dimmed-zebra",
    "--color-moved-ws=ignore-all-space",
    "--ignore-blank-lines",
    "--minimal",                 # spend extra time to produce smallest diff
    "-M",                        # detect renames
    "-C",                        # detect copies
]


def run_git_diff(extra_args: list[str]) -> str:
    """
    Run git diff with move detection enabled and return the raw output
    including ANSI color codes.

    Args:
        extra_args: Additional arguments passed through to git diff,
                    e.g. ["main..HEAD", "--", "src/"]

    Returns:
        Raw stdout from git diff (with ANSI codes).

    Raises:
        SystemExit: If git is not found or returns an error.
    """
    cmd = ["git"] + MOVED_COLOR_CONFIGS + ["diff"] + GIT_DIFF_FLAGS + extra_args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        print("Error: 'git' not found. Is git installed and on your PATH?",
              file=sys.stderr)
        sys.exit(1)

    if result.returncode not in (0, 1):
        # returncode 1 is normal for "differences found"
        print(f"Error: git diff failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)

    return result.stdout


# ---------------------------------------------------------------------------
# Diff parsing and filtering
# ---------------------------------------------------------------------------

@dataclass
class HunkResult:
    """Result of processing one diff hunk."""
    kept_lines: list[str] = field(default_factory=list)
    total_diff_lines: int = 0      # lines starting with + or -
    moved_diff_lines: int = 0      # lines detected as moved


@dataclass
class FileResult:
    """Result of processing one file's diff."""
    header_lines: list[str] = field(default_factory=list)
    hunks: list[HunkResult] = field(default_factory=list)


@dataclass
class Stats:
    """Aggregate statistics across the entire diff."""
    total_files: int = 0
    files_all_moved: int = 0
    total_diff_lines: int = 0
    moved_lines: int = 0
    kept_lines: int = 0


def process_diff(raw_output: str) -> tuple[list[FileResult], Stats]:
    """
    Parse the ANSI-colored git diff output and classify each line.

    Returns:
        A tuple of (list of FileResult, Stats).
    """
    files: list[FileResult] = []
    current_file: FileResult | None = None
    current_hunk: HunkResult | None = None
    stats = Stats()

    for raw_line in raw_output.splitlines():
        clean = strip_ansi(raw_line)

        # Detect file header (diff --git a/... b/...)
        if clean.startswith("diff --git "):
            if current_file is not None:
                files.append(current_file)
            current_file = FileResult()
            current_file.header_lines.append(clean)
            current_hunk = None
            continue

        # Accumulate other file-level headers (index, ---, +++ lines)
        if current_file is not None and current_hunk is None:
            if clean.startswith(("index ", "---", "+++",
                                 "old mode", "new mode",
                                 "new file", "deleted file",
                                 "similarity", "rename", "copy")):
                current_file.header_lines.append(clean)
                continue

        # Detect hunk header (@@ ... @@)
        if clean.startswith("@@"):
            current_hunk = HunkResult()
            current_hunk.kept_lines.append(clean)
            if current_file is not None:
                current_file.hunks.append(current_hunk)
            continue

        # Process diff content lines
        if current_hunk is not None:
            if clean.startswith(("+", "-")):
                current_hunk.total_diff_lines += 1
                if is_moved_line(raw_line):
                    current_hunk.moved_diff_lines += 1
                    # Skip this line (it's just moved code)
                else:
                    current_hunk.kept_lines.append(clean)
            else:
                # Context line (starts with space) or other
                current_hunk.kept_lines.append(clean)

    # Don't forget the last file
    if current_file is not None:
        files.append(current_file)

    # Compute stats
    for f in files:
        stats.total_files += 1
        file_all_moved = True
        for h in f.hunks:
            stats.total_diff_lines += h.total_diff_lines
            stats.moved_lines += h.moved_diff_lines
            kept = h.total_diff_lines - h.moved_diff_lines
            stats.kept_lines += kept
            if kept > 0:
                file_all_moved = False
        if file_all_moved and f.hunks:
            stats.files_all_moved += 1

    return files, stats


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_output(files: list[FileResult], stats: Stats,
                  show_stats: bool, out: TextIO) -> None:
    """
    Write the filtered diff to the output stream.

    Args:
        files: Parsed and filtered file results.
        stats: Aggregate statistics.
        show_stats: Whether to append a stats summary.
        out: Output stream (e.g. sys.stdout).
    """
    for f in files:
        # Check if this file had only moved code
        file_has_real_changes = any(
            h.total_diff_lines > h.moved_diff_lines for h in f.hunks
        )

        if not file_has_real_changes and f.hunks:
            # Summarize: all changes in this file were just moves
            file_path = _extract_path(f.header_lines)
            total = sum(h.total_diff_lines for h in f.hunks)
            out.write(f"# {file_path}: all {total} changed lines were "
                      f"moved code (no real changes)\n")
            continue

        # Print file headers
        for line in f.header_lines:
            out.write(line + "\n")

        # Print each hunk
        for h in f.hunks:
            if h.moved_diff_lines > 0 and h.moved_diff_lines == h.total_diff_lines:
                # Entire hunk was moved code
                out.write(f"# [hunk: {h.moved_diff_lines} lines were moved, "
                          f"no real changes]\n")
            else:
                for line in h.kept_lines:
                    out.write(line + "\n")
                if h.moved_diff_lines > 0:
                    out.write(f"# [stripped {h.moved_diff_lines} moved "
                              f"lines from this hunk]\n")

    # Stats summary
    if show_stats and stats.total_diff_lines > 0:
        out.write("\n")
        out.write("# " + "=" * 60 + "\n")
        out.write("# git-refactor-diff statistics\n")
        out.write("# " + "=" * 60 + "\n")
        out.write(f"#   Files changed:        {stats.total_files}\n")
        out.write(f"#   Files (all moved):     {stats.files_all_moved}\n")
        out.write(f"#   Total diff lines:      {stats.total_diff_lines}\n")
        out.write(f"#   Moved (stripped):      {stats.moved_lines}\n")
        out.write(f"#   Real changes (kept):   {stats.kept_lines}\n")
        pct = (stats.moved_lines / stats.total_diff_lines) * 100
        out.write(f"#   Reduction:             {pct:.0f}%\n")
        out.write("# " + "=" * 60 + "\n")


def _extract_path(header_lines: list[str]) -> str:
    """Extract the file path from diff header lines."""
    for line in header_lines:
        if line.startswith("diff --git"):
            # Format: diff --git a/path b/path
            parts = line.split(" b/", 1)
            if len(parts) == 2:
                return parts[1]
    return "<unknown>"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-refactor-diff",
        description=(
            "Produce minimal diffs that exclude moved-but-unchanged code. "
            "Uses git's --color-moved detection to identify code that was "
            "merely relocated and strips it from the output. Ideal for "
            "reviewing refactoring branches or feeding diffs to LLMs."
        ),
        epilog=(
            "Examples:\n"
            "  %(prog)s main..HEAD\n"
            "  %(prog)s main..HEAD -- src/\n"
            "  %(prog)s --stats main..HEAD\n"
            "  %(prog)s HEAD~3 HEAD\n"
            "  %(prog)s > clean.diff\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show statistics summary at the end of output",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 0.1.0",
    )
    parser.add_argument(
        "git_args", nargs="*", metavar="GIT_ARG",
        help=(
            "Arguments passed through to git diff. Typically a commit range "
            "like 'main..HEAD', two commits, or nothing (for working tree). "
            "Use '--' to separate paths: 'main..HEAD -- src/'"
        ),
    )
    return parser


def main() -> None:
    # Force UTF-8 on stdout — Windows defaults to CP1252 when piped or redirected
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args()

    # Run git diff with move detection
    raw = run_git_diff(args.git_args)

    if not raw.strip():
        print("No differences found.", file=sys.stderr)
        sys.exit(0)

    # Process and filter
    files, stats = process_diff(raw)

    # Output
    format_output(files, stats, show_stats=args.stats, out=sys.stdout)


if __name__ == "__main__":
    main()
