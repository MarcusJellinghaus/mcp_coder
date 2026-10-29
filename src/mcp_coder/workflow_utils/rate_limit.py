"""Recognise GitHub rate-limit errors and stop GitHub work on the first one.

Manager methods re-raise rate limits as the raw ``GithubException`` /
``RetryError``; ``get_authenticated_username`` wraps one in a ``ValueError``
whose ``__cause__`` is the original. These helpers map all of them to
``GitHubRateLimitError``.
"""

import logging

from mcp_coder.mcp_workspace_github import GitHubRateLimitError, to_rate_limit_error
from mcp_coder.utils.log_utils import OUTPUT

logger = logging.getLogger(__name__)

__all__ = ["as_rate_limit", "log_rate_limit_stop", "raise_if_rate_limited"]


def as_rate_limit(exc: BaseException) -> GitHubRateLimitError | None:
    """Return a GitHubRateLimitError for a rate-limit exception, else None.

    Args:
        exc: Any exception, possibly wrapping a rate limit as ``__cause__``.

    Returns:
        ``exc`` itself if it already is a GitHubRateLimitError, a new one for a
        raw rate-limit exception (or one wrapped as ``__cause__``), else None.
    """
    if isinstance(exc, GitHubRateLimitError):
        return exc
    rate_limit = to_rate_limit_error(exc)
    if rate_limit is None and exc.__cause__ is not None:
        rate_limit = to_rate_limit_error(exc.__cause__)
    return rate_limit


def raise_if_rate_limited(exc: BaseException) -> None:
    """Raise GitHubRateLimitError (``from exc``) if exc is a rate limit.

    Call first in a broad ``except`` block; returns normally otherwise.

    Args:
        exc: The caught exception.

    Raises:
        GitHubRateLimitError: If exc is or wraps a GitHub rate limit.
    """
    rate_limit = as_rate_limit(exc)
    if rate_limit is exc:
        raise exc
    if rate_limit is not None:
        raise rate_limit from exc


def log_rate_limit_stop(exc: GitHubRateLimitError) -> None:
    """Log the single "rate limit hit, stopping" line at OUTPUT level.

    Args:
        exc: The rate-limit error that stopped the run.
    """
    when = (
        f"reset at {exc.reset_at:%Y-%m-%d %H:%M:%S %Z}"
        if exc.reset_at
        else "reset time unknown"
    )
    logger.log(OUTPUT, "GitHub rate limit hit, stopping GitHub work: %s", when)
