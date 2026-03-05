"""CLI commands for Git tool operations.

This module provides the git-tool command group for Git-related operations.
"""

import argparse
import fnmatch
import logging
import sys

from ...utils.git_operations.compact_diffs import get_compact_diff
from ...utils.git_operations.diffs import get_git_diff_for_commit
from ...workflow_utils.base_branch import detect_base_branch
from ...workflows.utils import resolve_project_dir

logger = logging.getLogger(__name__)


def _apply_exclude_patterns_to_uncommitted_diff(
    uncommitted_diff: str, exclude_patterns: list[str]
) -> str:
    """Filter uncommitted diff by exclude patterns.

    Removes diff blocks for files matching any exclude pattern.
    Preserves section headers (=== STAGED CHANGES ===, etc.) only if
    they have remaining content after filtering.

    Args:
        uncommitted_diff: Raw uncommitted diff from get_git_diff_for_commit()
        exclude_patterns: List of glob patterns to exclude (e.g., ["*.log", "pr_info/**"])

    Returns:
        Filtered diff with excluded files removed, preserving section headers.
        Returns empty string if all files are excluded.
    """
    if not exclude_patterns or not uncommitted_diff:
        return uncommitted_diff

    lines = uncommitted_diff.split("\n")
    filtered_lines: list[str] = []
    current_block: list[str] = []
    skip_current_block = False

    for line in lines:
        # Section headers (keep them, decide later if section is empty)
        if line.startswith("=== ") and line.endswith(" ==="):
            # Flush previous block
            if current_block and not skip_current_block:
                filtered_lines.extend(current_block)
            current_block = [line]
            skip_current_block = False
            continue

        # Diff block start (diff --git <file> <file>)
        if line.startswith("diff --git "):
            # Flush previous block
            if current_block and not skip_current_block:
                filtered_lines.extend(current_block)

            # Extract filename from "diff --git a/file.py b/file.py"
            # Format: "diff --git <path> <path>" (no a/ b/ prefix due to --no-prefix)
            # Note: split() on spaces means paths containing spaces will misparse
            # (parts[2] would be only the first word). This is a known limitation.
            parts = line.split()
            if len(parts) >= 3:
                filepath = parts[2]  # First path (identical with --no-prefix)

                # Check if file matches any exclude pattern.
                # Note: fnmatch's * matches everything including /, unlike shell
                # globbing. So "pr_info/*" already matches "pr_info/notes.md"
                # — ** has no special meaning here, it just works by coincidence.
                skip_current_block = any(
                    fnmatch.fnmatch(filepath, pattern) for pattern in exclude_patterns
                )
            else:
                skip_current_block = False

            current_block = [line]
            continue

        # Regular diff line (part of current block)
        current_block.append(line)

    # Flush last block
    if current_block and not skip_current_block:
        filtered_lines.extend(current_block)

    # Remove empty sections (section header with no content)
    result: list[str] = []
    i = 0
    while i < len(filtered_lines):
        line = filtered_lines[i]

        # If it's a section header, check if next non-empty line is another section header
        if line.startswith("=== ") and line.endswith(" ==="):
            # Look ahead for content
            j = i + 1
            has_content = False
            while j < len(filtered_lines):
                next_line = filtered_lines[j]
                if next_line.strip():  # Non-empty line
                    if next_line.startswith("=== ") and next_line.endswith(" ==="):
                        # Another section header, no content in current section
                        break
                    else:
                        # Found content
                        has_content = True
                        break
                j += 1

            if has_content:
                result.append(line)
        else:
            result.append(line)

        i += 1

    return "\n".join(result).strip()


def execute_compact_diff(args: argparse.Namespace) -> int:
    """Execute git-tool compact-diff command.

    Returns:
        0  Success — compact diff printed to stdout
        1  Could not detect base branch
        2  Error (invalid repo, unexpected exception)
    """
    try:
        logger.info("Starting compact-diff")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # Use provided base branch or auto-detect
        base_branch = (
            args.base_branch if args.base_branch else detect_base_branch(project_dir)
        )

        if base_branch is None:
            logger.warning("Could not detect base branch")
            print("Error: Could not detect base branch", file=sys.stderr)
            return 1

        # Get committed changes
        committed_diff = get_compact_diff(project_dir, base_branch, args.exclude or [])

        # Get uncommitted changes (unless --committed-only flag set)
        if not args.committed_only:
            uncommitted_diff = get_git_diff_for_commit(project_dir)

            # Apply exclude patterns to uncommitted diff
            if uncommitted_diff and args.exclude:
                uncommitted_diff = _apply_exclude_patterns_to_uncommitted_diff(
                    uncommitted_diff, args.exclude
                )

            if uncommitted_diff:
                if committed_diff:
                    result = f"{committed_diff}\n\n=== UNCOMMITTED CHANGES ===\n{uncommitted_diff}"
                else:
                    result = f"No committed changes\n\n=== UNCOMMITTED CHANGES ===\n{uncommitted_diff}"
            else:
                result = committed_diff
        else:
            result = committed_diff

        print(result)
        return 0

    except ValueError as e:
        # resolve_project_dir raises ValueError for invalid directories
        logger.error(f"Error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        logger.error(f"Error generating compact diff: {e}")
        logger.debug("Exception details:", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 2
