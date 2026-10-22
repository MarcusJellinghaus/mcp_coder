"""Helper functions for the create-pr workflow.

Contains PR summary parsing and failure handling utilities extracted
from core.py to keep module size manageable.
"""

import logging
import re
from pathlib import Path

from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure,
    format_elapsed_time,
    handle_workflow_failure,
)

logger = logging.getLogger(__name__)

# GitHub closing keywords followed by an issue reference, e.g. "Closes #123"
_CLOSING_REF_RE = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b:?\s*#(\d+)\b", re.IGNORECASE
)


def ensure_closing_reference(body: str, issue_number: int) -> str:
    """Return body guaranteed to contain a closing keyword for issue_number.

    Args:
        body: PR body text
        issue_number: Issue the PR should close on merge

    Returns:
        The body unchanged if it already closes the issue, otherwise the body
        with ``Closes #<issue_number>`` appended.
    """
    numbers = {int(n) for n in _CLOSING_REF_RE.findall(body)}
    if issue_number in numbers:
        return body
    others = sorted(numbers)
    if others:
        logger.warning(
            "PR body already closes other issue(s) %s; also adding Closes #%s",
            ", ".join(f"#{n}" for n in others),
            issue_number,
        )
    return f"{body}\n\nCloses #{issue_number}"


def parse_pr_summary(llm_response: str) -> tuple[str, str]:
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
        "## ❌ PR Creation Failed",
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
    update_issue_labels: bool,
    post_issue_comments: bool = False,
    elapsed_time: float | None = None,
    issue_number: int | None = None,
    pr_url: str | None = None,
    pr_number: int | None = None,
    is_cleanup_failure: bool = False,
    category: str = "pr_creating_failed",
) -> None:
    """Convenience wrapper: format comment + call shared handler.

    ``category`` is the label ID applied to the issue for this failure; it
    defaults to the general ``pr_creating_failed``, while the summary-generation
    catch passes the classified ``pr_creating_timeout`` / ``pr_creating_mcp``.
    """
    comment = format_failure_comment(
        stage=stage,
        message=message,
        elapsed_time=elapsed_time,
        pr_url=pr_url,
        pr_number=pr_number,
        is_cleanup_failure=is_cleanup_failure,
    )
    failure = WorkflowFailure(
        category=category,
        stage=stage,
        message=message,
        elapsed_time=elapsed_time,
    )
    handle_workflow_failure(
        failure=failure,
        comment_body=comment,
        project_dir=project_dir,
        from_label_id="pr_creating",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
        issue_number=issue_number,
    )
