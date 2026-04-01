"""Helper functions for the create-pr workflow.

Contains PR summary parsing and failure handling utilities extracted
from core.py to keep module size manageable.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure,
    format_elapsed_time,
    handle_workflow_failure,
)

logger = logging.getLogger(__name__)


def parse_pr_summary(llm_response: str) -> Tuple[str, str]:
    """Parse LLM response into PR title and body.

    Expected format:
    TITLE: feat: some title
    BODY:
    ## Summary
    ...

    Args:
        llm_response: Raw response from LLM

    Returns:
        Tuple of (title, body) strings
    """
    if not llm_response or not llm_response.strip():
        logger.warning("Empty LLM response, using fallback PR title/body")
        return "Pull Request", "Pull Request"

    content = llm_response.strip()

    # Look for TITLE: and BODY: markers
    title_match = None
    body_content = None

    # Extract title after "TITLE:"
    for line in content.split("\n"):
        if line.strip().startswith("TITLE:"):
            title_match = line.strip()[6:].strip()  # Remove "TITLE:" prefix
            break

    # Extract body after "BODY:"
    body_start = content.find("BODY:")
    if body_start != -1:
        body_content = content[body_start + 5 :].strip()  # Remove "BODY:" prefix

    # Fallback parsing if structured format not found
    if not title_match:
        logger.warning("No TITLE: found, attempting fallback parsing")
        lines = content.split("\n")
        # Try to find a line that looks like a title (starts with conventional prefix)
        for line in lines:
            line_stripped = line.strip()
            if any(
                line_stripped.startswith(prefix)
                for prefix in ["feat:", "fix:", "docs:", "refactor:", "test:", "chore:"]
            ):
                title_match = line_stripped
                break

        # If still no title found, use first non-empty line
        if not title_match:
            for line in lines:
                if line.strip():
                    title_match = line.strip()
                    break

    if not body_content:
        logger.warning("No BODY: found, using full response as body")
        body_content = content

    # Final fallbacks
    title = title_match or "Pull Request"
    body = body_content or "Pull Request"

    logger.info(f"Parsed PR title: {title}")
    return title, body


def format_failure_comment(
    stage: str,
    message: str,
    elapsed_time: float | None = None,
    pr_url: str | None = None,
    pr_number: int | None = None,
    is_cleanup_failure: bool = False,
) -> str:
    """Format a GitHub comment for a create-pr workflow failure.

    Returns:
        Formatted GitHub comment string.
    """
    lines = [
        "## PR Creation Failed",
        f"**Stage:** {stage}",
        f"**Error:** {message}",
    ]
    if elapsed_time is not None:
        lines.append(f"**Elapsed:** {format_elapsed_time(elapsed_time)}")
    if pr_url and pr_number:
        lines.append(f"**PR:** [{pr_number}]({pr_url})")
    if is_cleanup_failure:
        lines.append("\n> **Note:** pr_info/ directory may still exist on the branch")
    return "\n".join(lines)


def handle_create_pr_failure(
    stage: str,
    message: str,
    project_dir: Path,
    update_labels: bool,
    elapsed_time: float | None = None,
    issue_number: int | None = None,
    pr_url: str | None = None,
    pr_number: int | None = None,
    is_cleanup_failure: bool = False,
) -> None:
    """Convenience wrapper: format comment + call shared handler."""
    comment = format_failure_comment(
        stage=stage,
        message=message,
        elapsed_time=elapsed_time,
        pr_url=pr_url,
        pr_number=pr_number,
        is_cleanup_failure=is_cleanup_failure,
    )
    failure = WorkflowFailure(
        category="pr_creating_failed",
        stage=stage,
        message=message,
        elapsed_time=elapsed_time,
    )
    handle_workflow_failure(
        failure=failure,
        comment_body=comment,
        project_dir=project_dir,
        from_label_id="pr_creating",
        update_labels=update_labels,
        issue_number=issue_number,
    )
