"""PR title/body text helpers shared by PR-creating and PR-refreshing workflows."""

import logging
import re
from pathlib import Path

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.mcp_workspace_git import get_branch_diff
from mcp_coder.mcp_workspace_github import PullRequestManager
from mcp_coder.prompt_manager import get_prompt_with_substitutions
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.workflow_utils.base_branch import detect_base_branch

logger = logging.getLogger(__name__)

# GitHub closing keywords followed by an issue reference, e.g. "Closes #123"
_CLOSING_REF_RE = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b:?\s*#(\d+)\b", re.IGNORECASE
)


def closing_issue_numbers(body: str) -> list[int]:
    """Return the issue numbers the body closes (Closes/Fixes/Resolves #N).

    Args:
        body: PR body text

    Returns:
        Sorted, de-duplicated issue numbers.
    """
    return sorted({int(n) for n in _CLOSING_REF_RE.findall(body or "")})


def ensure_closing_reference(body: str, issue_number: int) -> str:
    """Return body guaranteed to contain a closing keyword for issue_number.

    Args:
        body: PR body text
        issue_number: Issue the PR should close on merge

    Returns:
        The body unchanged if it already closes the issue, otherwise the body
        with ``Closes #<issue_number>`` appended.
    """
    numbers = closing_issue_numbers(body)
    if issue_number in numbers:
        return body
    if numbers:
        logger.warning(
            "PR body already closes other issue(s) %s; also adding Closes #%s",
            ", ".join(f"#{n}" for n in numbers),
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


def refresh_pr_description(
    project_dir: Path,
    branch: str,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
) -> bool:
    """Refresh the open PR's title/body from the full branch diff. Best-effort, never raises.

    Closing references in the current PR body are re-applied to the new body.
    Never changes a label.

    Args:
        project_dir: Path to project directory
        branch: Head branch of the open PR
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional path to MCP configuration file
        settings_file: Optional path to .claude/settings.local.json; forwarded to prompt_llm.

    Returns:
        True if the PR was updated, False if unchanged, skipped or failed.
    """
    try:
        pr_manager = PullRequestManager(project_dir)
        prs = pr_manager.find_pull_request_by_head(branch)
        if not prs:
            logger.warning(
                "No open PR for branch %s - skipping description refresh", branch
            )
            return False

        pr = pr_manager.get_pull_request(prs[0]["number"])
        base_branch = detect_base_branch(project_dir, current_branch=branch)
        if base_branch is None:
            logger.warning(
                "Could not detect base branch - skipping description refresh"
            )
            return False

        diff_content = get_branch_diff(
            project_dir, base_branch=base_branch, exclude_paths=["pr_info/"]
        )
        if not diff_content or not diff_content.strip():
            logger.info("No diff content - skipping description refresh")
            return False

        current_body = pr.get("body") or ""
        prompt = get_prompt_with_substitutions(
            str(PROMPTS_FILE_PATH),
            "PR Description Refresh",
            {
                "pr_title": pr.get("title") or "",
                "pr_body": current_body,
                "git_diff_content": diff_content,
            },
        )

        logger.info(
            f"Calling LLM for PR description refresh using provider={provider}..."
        )
        text = prompt_llm(
            prompt,
            provider=provider,
            # Inactivity budget (was wall-clock), kept below the CI step cap.
            timeout=300,
            env_vars=prepare_llm_environment(project_dir),
            project_dir=str(project_dir),
            mcp_config=mcp_config,
            settings_file=settings_file,
            branch_name=get_branch_name_for_logging(project_dir),
        )["text"].strip()

        if text.upper().startswith("UNCHANGED"):
            logger.info("PR #%s description still accurate - not updated", pr["number"])
            return False

        title, body = parse_pr_summary(text)
        for issue_number in closing_issue_numbers(current_body):
            body = ensure_closing_reference(body, issue_number)

        updated = bool(
            pr_manager.update_pull_request(pr["number"], title=title, body=body)
        )
        if updated:
            logger.info("PR #%s description refreshed", pr["number"])
        else:
            logger.warning("PR #%s description update failed", pr["number"])
        return updated

    except Exception as e:  # pylint: disable=broad-exception-caught  # best-effort
        logger.warning("PR description refresh failed (non-blocking): %s", e)
        return False
