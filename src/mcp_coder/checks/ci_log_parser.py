"""CI log parsing utilities.

Pure functions for parsing and filtering GitHub Actions log output,
extracted from branch_status.py to keep that module under the file-size limit.
"""

import logging
import re
from typing import List, Mapping, Optional, Tuple

logger = logging.getLogger(__name__)

# Timestamp pattern: YYYY-MM-DDTHH:MM:SS.NNNNNNNZ followed by optional space
_TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s?")


def _strip_timestamps(log_content: str) -> str:
    """Strip GitHub Actions timestamps from log lines.

    Removes timestamps like '2026-01-28T12:58:02.8274205Z ' from lines.
    Handles timestamps at line start or after ANSI escape sequences.

    Args:
        log_content: Raw log content with timestamps

    Returns:
        Log content with timestamps removed
    """
    lines = log_content.split("\n")
    cleaned_lines = [_TIMESTAMP_PATTERN.sub("", line) for line in lines]
    return "\n".join(cleaned_lines)


def _parse_groups(log_content: str) -> List[Tuple[str, List[str]]]:
    """Parse ``##[group]``/``##[endgroup]`` sections from a GitHub Actions log.

    Lines starting with ``##[error]`` immediately after ``##[endgroup]`` are
    attached to the preceding group.

    Returns:
        List of (label, content_lines) tuples.
    """
    groups: List[Tuple[str, List[str]]] = []
    current_label: Optional[str] = None
    current_lines: List[str] = []

    for line in log_content.split("\n"):
        if line.startswith("##[group]"):
            if current_label is not None:
                groups.append((current_label, current_lines))
            current_label = line[len("##[group]") :]
            current_lines = []
        elif line.startswith("##[endgroup]"):
            if current_label is not None:
                groups.append((current_label, current_lines))
                current_label = None
                current_lines = []
        else:
            if current_label is not None:
                current_lines.append(line)
            elif groups:
                # Lines after ##[endgroup] – capture ##[error] lines
                if line.startswith("##[error]"):
                    label, lines_so_far = groups[-1]
                    groups[-1] = (label, lines_so_far + [line])

    # Save any unclosed group
    if current_label is not None:
        groups.append((current_label, current_lines))

    return groups


def _extract_failed_step_log(log_content: str, step_name: str) -> str:
    """Extract only the failed step's section from a GitHub Actions job log.

    GitHub Actions logs in the newer format concatenate all steps into a single
    file, delimited by ``##[group]``/``##[endgroup]`` markers. This function
    finds the section matching *step_name* and returns just that content,
    stripping the marker lines themselves.

    Matching strategy (case-insensitive, in priority order):
      1. Exact match: group label == step_name
      2. Prefix match: group label starts with step_name
      3. Contains match: step_name is a substring of group label
      4. Error-group fallback: if step_name is empty/unknown or none of
         the above matched, return all groups containing ``##[error]`` lines.

    Lines starting with ``##[error]`` immediately after ``##[endgroup]`` are
    included (they typically contain the exit-code information).

    Args:
        log_content: Full job log content (all steps concatenated).
        step_name: The failed step name from the GitHub Actions API.

    Returns:
        Extracted section content, or empty string if extraction fails.
    """
    if not log_content:
        return ""

    groups = _parse_groups(log_content)

    if not groups:
        return ""

    # Try name-based matching when step_name is provided and non-trivial
    if step_name and step_name.lower() != "unknown":
        step_lower = step_name.lower()

        # 1. Exact match
        for label, lines in groups:
            if label.lower() == step_lower:
                return "\n".join(lines)

        # 2. Prefix match (label starts with step_name)
        for label, lines in groups:
            if label.lower().startswith(step_lower):
                return "\n".join(lines)

        # 3. Contains match (step_name in label)
        for label, lines in groups:
            if step_lower in label.lower():
                return "\n".join(lines)

    # 4. Error-group fallback: collect groups that contain ##[error] lines
    error_sections: List[str] = []
    for label, lines in groups:
        if any(line.startswith("##[error]") for line in lines):
            error_sections.append(f"--- {label} ---")
            error_sections.append("\n".join(lines))

    return "\n".join(error_sections)


def truncate_ci_details(
    details: str, max_lines: int = 300, head_lines: int = 10
) -> str:
    """Truncate CI details with head + tail preservation.

    Extract log excerpt: first head_lines + last (max_lines - head_lines) lines
    if log exceeds max_lines. The default is tail-biased (10 head, 290 tail)
    because errors typically appear at the end of CI logs.

    Args:
        details: Full CI details content as string
        max_lines: Maximum lines before truncation (default 300)
        head_lines: Number of lines to keep from the start (default 10)

    Returns:
        Original details if under max_lines, otherwise truncated with marker
    """
    if not details:
        return ""

    lines = details.split("\n")

    if len(lines) <= max_lines:
        return details

    # Take first head_lines and last (max_lines - head_lines) lines
    tail_lines = max_lines - head_lines
    first_lines = lines[:head_lines]
    last_lines = lines[-tail_lines:]
    truncated_count = len(lines) - max_lines

    return "\n".join(
        first_lines + [f"[... truncated {truncated_count} lines ...]"] + last_lines
    )


def _find_log_content(
    logs: Mapping[str, str],
    job_name: str,
    step_number: int,
    step_name: str,
) -> str:
    """Find log content for a job using GitHub format first, falling back to old format.

    GitHub format: {number}_{job_name}.txt (execution number doesn't match step.number)
    Old format: {job_name}/{step_number}_{step_name}.txt

    Args:
        logs: Dict mapping log filenames to content
        job_name: Name of the job
        step_number: Step number from API (used for old format fallback)
        step_name: Step name (used for old format fallback)

    Returns:
        Log content string, or empty string if not found
    """
    # Try GitHub format first: pattern match on _{job_name}.txt
    matching_files = [f for f in logs.keys() if f.endswith(f"_{job_name}.txt")]

    if matching_files:
        if len(matching_files) > 1:
            logger.warning(
                f"Multiple log files found for job '{job_name}': {matching_files}. "
                f"Using: {matching_files[0]}"
            )
        return logs[matching_files[0]]

    # Fallback to old format: {job_name}/{step_number}_{step_name}.txt
    log_filename = f"{job_name}/{step_number}_{step_name}.txt"
    log_content = logs.get(log_filename, "")

    if not log_content and step_name:
        available_files = list(logs.keys())
        logger.warning(
            f"No log file found for job '{job_name}'. "
            f"Tried: '*_{job_name}.txt' and '{log_filename}'. "
            f"Available: {available_files}"
        )

    return log_content
