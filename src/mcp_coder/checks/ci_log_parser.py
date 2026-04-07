"""CI log parsing utilities.

Pure functions for parsing and filtering GitHub Actions log output,
extracted from branch_status.py to keep that module under the file-size limit.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Tuple

if TYPE_CHECKING:
    from mcp_coder.utils.github_operations.ci_results_manager import CIResultsManager

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

    All lines after ``##[endgroup]`` (before the next ``##[group]``) are
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
                # Lines after ##[endgroup] – attach to preceding group
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

    All lines after ``##[endgroup]`` are included (they typically contain
    exit-code information and command output).

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


def _build_ci_error_details(
    ci_manager: CIResultsManager,
    status_result: Any,
    max_lines: int,
) -> Optional[str]:
    """Build structured CI error details with logs for multiple failed jobs.

    Shows logs for as many failed jobs as fit within the line limit.

    Args:
        ci_manager: CIResultsManager instance
        status_result: Result from get_latest_ci_status
        max_lines: Maximum total lines for output (default 300)

    Returns:
        Structured error details string or None if no logs available
    """
    run_data = status_result["run"]
    jobs_data = status_result.get("jobs", [])
    # Extract GitHub Actions run URL for user navigation
    run_url = run_data.get("url", "")

    # Get all failed jobs
    failed_jobs = [job for job in jobs_data if job.get("conclusion") == "failure"]

    # Collect distinct run_ids from failed jobs, preserving order
    failed_run_ids: List[int] = list(
        dict.fromkeys(j["run_id"] for j in failed_jobs if j.get("run_id"))
    )

    # Fetch logs for up to 3 failed run_ids
    logs: Dict[str, str] = {}
    fetched_run_ids = failed_run_ids[:3]
    for rid in fetched_run_ids:
        try:
            run_logs = ci_manager.get_run_logs(rid)
            logs.update(run_logs)
        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow when GitHub/CI exception types are stable
            logger.warning(f"Failed to get logs for run {rid}: {e}")

    if not failed_jobs:
        logger.info("No failed jobs found in CI results")
        return None

    # Build output sections
    output_lines: List[str] = []
    lines_used = 0
    jobs_shown: List[str] = []
    jobs_truncated: List[str] = []

    # Prepend jobs_fetch_warning if present (Decision 7)
    jobs_fetch_warning = run_data.get("jobs_fetch_warning")
    if jobs_fetch_warning:
        output_lines.append(f"WARNING: {jobs_fetch_warning}")
        output_lines.append("")
        lines_used += 2

    # Section 1: Summary header (will be updated at end)
    summary_placeholder_idx = len(output_lines)
    output_lines.append("")  # Placeholder for summary
    output_lines.append("")
    lines_used += 2

    # Add GitHub Actions run URL if available
    if run_url:
        output_lines.append(f"GitHub Actions: {run_url}")
        output_lines.append("")
        lines_used += 2

    # Section 2: Show logs for each failed job until we hit the limit
    for job in failed_jobs:
        job_name = job.get("name", "unknown")

        # Find first failed step
        step_name = "unknown"
        step_number = 0
        for step in job.get("steps", []):
            if step.get("conclusion") == "failure":
                step_name = step.get("name", "unknown")
                step_number = step.get("number", 0)
                break

        log_content = _find_log_content(logs, job_name, step_number, step_name)

        # Strip timestamps first so ##[group] markers are parseable
        if log_content:
            log_content = _strip_timestamps(log_content)

        # Extract just the failed step's section from the full job log
        if log_content:
            extracted = _extract_failed_step_log(log_content, step_name)
            if extracted:
                log_content = extracted

        # Calculate how many lines this job's section would take
        # Header lines: "## Job:", optional "View job:" (if URL available), "Failed step:", blank line
        job_id = job.get("id")
        has_job_url = bool(run_url and job_id)
        job_header_lines = 4 if has_job_url else 3

        if log_content:
            log_lines = log_content.split("\n")
        elif has_job_url:
            log_lines = [
                "(logs not available locally)",
                f"View on GitHub: {run_url}/job/{job_id}",
            ]
        else:
            log_lines = ["(logs not available)"]

        # Calculate remaining budget for this job
        remaining_budget = (
            max_lines - lines_used - job_header_lines - 5
        )  # Reserve 5 for footer

        if remaining_budget <= 10:
            # Not enough space for meaningful logs, add to truncated list
            jobs_truncated.append(job_name)
            continue

        # Truncate log if needed (only applies to real log content, not fallback messages)
        if log_content and len(log_lines) > remaining_budget:
            # Use head + tail truncation
            head_count = min(10, remaining_budget // 6)
            tail_count = remaining_budget - head_count - 1  # -1 for truncation message
            truncated_log = (
                log_lines[:head_count]
                + [
                    f"[... truncated {len(log_lines) - head_count - tail_count} lines ...]"
                ]
                + log_lines[-tail_count:]
            )
            log_content = "\n".join(truncated_log)
            log_lines = truncated_log

        # Add job section
        output_lines.append(f"## Job: {job_name}")
        if has_job_url:
            output_lines.append(f"View job: {run_url}/job/{job_id}")
        output_lines.append(f"Failed step: {step_name}")
        output_lines.append("")
        if log_content:
            output_lines.append(log_content)
        else:
            output_lines.append("\n".join(log_lines))
        output_lines.append("")

        lines_used += job_header_lines + len(log_lines) + 1
        jobs_shown.append(job_name)

    # Section 3: List jobs that didn't fit
    if jobs_truncated:
        output_lines.append("## Other failed jobs (logs truncated to save space)")
        for job_name in jobs_truncated:
            # Find step name for this job
            for job in failed_jobs:
                if job.get("name") == job_name:
                    step_name = "unknown"
                    for step in job.get("steps", []):
                        if step.get("conclusion") == "failure":
                            step_name = step.get("name", "unknown")
                            break
                    output_lines.append(f'- {job_name}: step "{step_name}" failed')
                    break

    # Update summary placeholder
    all_failed = jobs_shown + jobs_truncated
    output_lines[summary_placeholder_idx] = (
        f"## CI Failure Summary\n"
        f"Failed jobs ({len(all_failed)}): {', '.join(all_failed)}"
    )

    return "\n".join(output_lines)
