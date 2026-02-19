"""Compact diff pipeline: suppress moved-code blocks to reduce diff size."""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .diffs import get_branch_diff

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_CONTENT_LENGTH: int = 10  # ignore short lines like "pass", "}" when matching moves
MIN_BLOCK_LINES: int = 3  # consecutive moved lines needed to emit a summary

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Hunk:
    """Represents a single unified diff hunk."""

    header: str  # raw "@@ -a,b +c,d @@" line
    lines: list[str] = field(default_factory=list)


@dataclass
class FileDiff:
    """Represents the diff for a single file."""

    headers: list[str] = field(
        default_factory=list
    )  # "diff --git ...", "index ...", etc.
    hunks: list[Hunk] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Layer 1: Parsing
# ---------------------------------------------------------------------------


def parse_diff(text: str) -> list[FileDiff]:
    """Parse a plain unified diff string into FileDiff/Hunk objects."""
    files: list[FileDiff] = []
    if not text.strip():
        return files

    current_file: Optional[FileDiff] = None
    current_hunk: Optional[Hunk] = None

    for line in text.splitlines():
        if line.startswith("diff --git"):
            # Save previous hunk/file
            if current_hunk is not None and current_file is not None:
                current_file.hunks.append(current_hunk)
                current_hunk = None
            if current_file is not None:
                files.append(current_file)
            current_file = FileDiff(headers=[line])
        elif current_file is not None and line.startswith("@@"):
            # Start a new hunk
            if current_hunk is not None:
                current_file.hunks.append(current_hunk)
            current_hunk = Hunk(header=line)
        elif current_hunk is not None:
            current_hunk.lines.append(line)
        elif current_file is not None:
            # File header lines (index, ---, +++)
            current_file.headers.append(line)

    # Flush last hunk and file
    if current_hunk is not None and current_file is not None:
        current_file.hunks.append(current_hunk)
    if current_file is not None:
        files.append(current_file)

    return files


# ---------------------------------------------------------------------------
# Layer 2: ANSI detection (Pass 1)
# ---------------------------------------------------------------------------

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from a string."""
    return _ANSI_ESCAPE_RE.sub("", text)


def is_moved_line(raw_line: str) -> bool:
    """True if the ANSI-coloured diff line is classified as moved by git.

    Looks for the 'dim' SGR attribute (code 2) in the ANSI codes.
    Only +/- lines can be moved; context lines and headers return False.

    Note: ANSI dim codes (\\x1b[2m) are confirmed to work on Windows —
    no special environment setup is required.
    """
    plain = strip_ansi(raw_line)
    if not plain or plain[0] not in ("+", "-"):
        return False
    # Look for SGR code 2 (dim) in the ANSI sequences of this line
    codes_found = set()
    for match in _ANSI_ESCAPE_RE.finditer(raw_line):
        seq = match.group()
        # Strip \x1b[ and trailing m, split by ;
        inner = seq[2:-1]
        for code in inner.split(";"):
            codes_found.add(code)
    return "2" in codes_found


def extract_moved_blocks_ansi(ansi_diff: str) -> set[str]:
    """Return the set of stripped line contents that git marked as moved.

    Uses is_moved_line() per line to identify lines coloured with ANSI dim
    by --color-moved=dimmed-zebra.
    """
    moved: set[str] = set()
    for line in ansi_diff.splitlines():
        if is_moved_line(line):
            plain = strip_ansi(line)
            # Strip the leading +/- sign and add content
            content = plain[1:]
            moved.add(content)
    return moved


# ---------------------------------------------------------------------------
# Layer 3: Python cross-file matching (Pass 2)
# ---------------------------------------------------------------------------


def is_significant_line(content: str) -> bool:
    """True if stripped content length >= MIN_CONTENT_LENGTH."""
    return len(content.strip()) >= MIN_CONTENT_LENGTH


def collect_line_occurrences(files: list[FileDiff]) -> tuple[set[str], set[str]]:
    """Return (removed_lines, added_lines) sets of significant stripped content."""
    removed: set[str] = set()
    added: set[str] = set()
    for file_diff in files:
        for hunk in file_diff.hunks:
            for line in hunk.lines:
                if line.startswith("-"):
                    content = line[1:]
                    if is_significant_line(content):
                        removed.add(content)
                elif line.startswith("+"):
                    content = line[1:]
                    if is_significant_line(content):
                        added.add(content)
    return removed, added


def find_moved_lines(files: list[FileDiff]) -> set[str]:
    """Return intersection of removed and added significant lines = moved."""
    removed, added = collect_line_occurrences(files)
    return removed & added


# ---------------------------------------------------------------------------
# Layer 4: Block analysis
# ---------------------------------------------------------------------------


def format_moved_summary(count: int) -> str:
    """Return '# [moved: N lines not shown]' comment string."""
    return f"# [moved: {count} lines not shown]"


# ---------------------------------------------------------------------------
# Layer 5: Rendering
# ---------------------------------------------------------------------------


def render_hunk(hunk: Hunk, moved_lines: set[str]) -> str:
    """Render a single hunk, replacing moved blocks >= MIN_BLOCK_LINES.

    A block is suppressed only when block >= MIN_BLOCK_LINES AND ALL
    significant lines in the block are moved (100% threshold).
    """
    output: list[str] = [hunk.header]
    lines = hunk.lines
    i = 0
    while i < len(lines):
        line = lines[i]
        # Context lines are emitted as-is
        if line.startswith(" ") or (line and line[0] not in ("+", "-")):
            output.append(line)
            i += 1
            continue

        # Gather consecutive lines with the same sign (+/-)
        sign = line[0]
        block: list[str] = []
        j = i
        while j < len(lines) and lines[j].startswith(sign):
            block.append(lines[j])
            j += 1

        # Count significant moved lines in block
        significant_moved = [
            bl for bl in block if is_significant_line(bl[1:]) and bl[1:] in moved_lines
        ]
        significant_total = [bl for bl in block if is_significant_line(bl[1:])]

        # Suppress block if: length >= MIN_BLOCK_LINES AND all significant lines moved
        if (
            len(block) >= MIN_BLOCK_LINES
            and len(significant_total) > 0
            and len(significant_moved) == len(significant_total)
        ):
            output.append(format_moved_summary(len(block)))
        else:
            output.extend(block)

        i += len(block)

    # Return empty string if only the header remains (hunk is empty after suppression)
    if output == [hunk.header]:
        return ""
    return "\n".join(output)


def render_file_diff(file_diff: FileDiff, moved_lines: set[str]) -> str:
    """Render all hunks for one file; skip file entirely if all hunks are empty.

    After moved-block suppression.
    """
    rendered_hunks: list[str] = []
    for hunk in file_diff.hunks:
        rendered = render_hunk(hunk, moved_lines)
        if rendered:
            rendered_hunks.append(rendered)

    if not rendered_hunks:
        return ""

    parts = file_diff.headers + rendered_hunks
    return "\n".join(parts)


def render_compact_diff(plain_diff: str, ansi_diff: str) -> str:
    """Top-level entry point.

    Combine Pass 1 (ANSI) and Pass 2 (Python) moved-line sets, then render.
    """
    if not plain_diff.strip():
        return ""

    plain_files = parse_diff(plain_diff)
    ansi_moved = extract_moved_blocks_ansi(ansi_diff)  # Pass 1
    py_moved = find_moved_lines(plain_files)  # Pass 2
    all_moved = ansi_moved | py_moved

    output: list[str] = []
    for file_diff in plain_files:
        rendered = render_file_diff(file_diff, all_moved)
        if rendered:
            output.append(rendered)

    return "\n".join(output)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def get_compact_diff(
    project_dir: Path,
    base_branch: str,
    exclude_paths: Optional[list[str]] = None,
) -> str:
    """Obtain a compact diff by running get_branch_diff() twice and rendering.

    Returns compact diff string (may be empty if no changes).
    """
    logger.debug(
        "Getting compact diff for %s (base: %s, excludes: %s)",
        project_dir,
        base_branch,
        exclude_paths,
    )

    plain_diff = get_branch_diff(
        project_dir=project_dir,
        base_branch=base_branch,
        exclude_paths=exclude_paths,
        ansi=False,
    )
    if not plain_diff:
        return ""

    ansi_diff = get_branch_diff(
        project_dir=project_dir,
        base_branch=base_branch,
        exclude_paths=exclude_paths,
        ansi=True,
    )

    return render_compact_diff(plain_diff, ansi_diff)
