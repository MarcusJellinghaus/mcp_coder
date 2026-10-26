"""PR title/body text helpers shared by PR-creating and PR-refreshing workflows."""

import logging
import re

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
