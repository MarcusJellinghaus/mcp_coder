"""Shared workflow failure handling utilities.

Provides common failure handling logic used by both the implement and
create-pr workflows: failure logging, label transitions, and comment posting.
"""

import logging
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.mcp_workspace_git import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from mcp_coder.mcp_workspace_github import IssueManager
from mcp_coder.utils.subprocess_runner import execute_command
from mcp_coder.workflow_utils.label_transitions import update_workflow_label

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkflowFailure:
    """Structured failure info shared across workflows.

    Attributes:
        category: Label ID in labels.json, e.g. "pr_creating_failed".
        stage: Workflow stage where failure occurred, e.g. "prerequisites".
        message: Human-readable error description.
        elapsed_time: Optional elapsed time in seconds.
    """

    category: str
    stage: str
    message: str
    elapsed_time: float | None = None


def llm_failure_reason(exc: BaseException) -> str | None:
    """Map an LLM exception to a workflow failure reason, else None.

    This is the single exception→reason classifier shared by all workflows.

    Args:
        exc: The exception raised by an LLM call.

    Returns:
        ``"timeout"`` for :class:`LLMTimeoutError`, ``"mcp_unavailable"`` for
        :class:`McpServersUnavailableError`, or ``None`` for any other
        exception (i.e. not a categorizable LLM failure).
    """
    if isinstance(exc, LLMTimeoutError):
        return "timeout"
    if isinstance(exc, McpServersUnavailableError):
        return "mcp_unavailable"
    return None


def format_mcp_unavailable_message(error: McpServersUnavailableError) -> str:
    """Build a clear, server-naming failure message for the typed guard error.

    The guard raises ``McpServersUnavailableError`` when a Claude session starts
    without its configured MCP servers. This turns the carried
    ``unavailable_servers`` mapping into a human-readable, deterministically
    ordered message suitable for a workflow failure comment.

    Args:
        error: The typed guard error carrying ``unavailable_servers``.

    Returns:
        A message naming each unavailable server and its status, e.g.
        ``"MCP servers unavailable: mcp-tools-py (failed), mcp-workspace
        (unknown). ..."``. Falls back to ``"unknown"`` when no servers were
        recorded.
    """
    servers = error.unavailable_servers or {}
    named = (
        ", ".join(f"{name} ({status})" for name, status in sorted(servers.items()))
        or "unknown"
    )
    return (
        f"MCP servers unavailable: {named}. The Claude session started without "
        f"its configured tools and was aborted; check the MCP server logs and "
        f".mcp.json."
    )


def get_diff_stat(project_dir: Path) -> str:
    """Get git diff --stat for uncommitted changes.

    Returns:
        Diff stat output, or empty string on error.
    """
    try:
        result = execute_command(
            ["git", "diff", "HEAD", "--stat"], cwd=str(project_dir)
        )
        if result.return_code == 0:
            return result.stdout
        return ""
    except Exception:  # pylint: disable=broad-exception-caught
        return ""


def format_elapsed_time(seconds: float) -> str:
    """Format seconds into human-readable string like '12m 34s' or '1h 5m 30s'.

    Returns:
        Human-readable time string.
    """
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def handle_workflow_failure(
    failure: WorkflowFailure,
    comment_body: str,
    project_dir: Path,
    from_label_id: str,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
    issue_number: int | None = None,
) -> None:
    """Handle workflow failure: log banner, set label, post comment.

    Label update respects the ``update_issue_labels`` flag.  The comment is
    only posted when ``post_issue_comments`` is *True*.

    Args:
        failure: Structured failure information.
        comment_body: Pre-formatted comment body to post on the issue.
        project_dir: Path to the project git repository.
        from_label_id: Current workflow label ID to transition from.
        update_issue_labels: Whether to attempt a label transition.
        post_issue_comments: Whether to post a comment on the issue.
        issue_number: Caller-provided issue number; falls back to branch
            name extraction when *None*.
    """
    # 1. Log failure banner
    logger.error("=" * 60)
    logger.error("WORKFLOW FAILED")
    logger.error("Category: %s", failure.category)
    logger.error("Stage: %s", failure.stage)
    logger.error("Error: %s", failure.message)
    logger.error("=" * 60)

    # 2. Resolve issue number
    resolved_issue_number = issue_number
    if resolved_issue_number is None:
        try:
            branch_name = get_current_branch_name(project_dir)
            resolved_issue_number = (
                extract_issue_number_from_branch(branch_name) if branch_name else None
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to extract issue number from branch: %s", exc)

    # 3. Create shared IssueManager if needed for label update or comment
    needs_label_update = update_issue_labels
    needs_comment = post_issue_comments and resolved_issue_number is not None
    if needs_label_update or needs_comment:
        try:
            issue_manager = IssueManager(project_dir)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Failed to create IssueManager: %s", exc)
            return

        # 4. Set failure label (non-blocking)
        if needs_label_update:
            try:
                update_workflow_label(
                    issue_manager,
                    from_label_id=from_label_id,
                    to_label_id=failure.category,
                    validated_issue_number=resolved_issue_number,
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.warning("Failed to update issue label: %s", exc)

        # 5. Post GitHub comment (non-blocking)
        if needs_comment:
            try:
                issue_manager.add_comment(resolved_issue_number, comment_body)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.warning("Failed to post failure comment: %s", exc)


@dataclass(frozen=True)
class GuardOutcome:
    """Context describing an escape netted by :func:`run_guarded`.

    Passed to a ``build_comment`` closure so a workflow can enrich the net
    comment (e.g. ``implement``'s ``Progress: X/Y`` line) from its own live
    locals at net time.

    Attributes:
        caught_exception: The exception that escaped, or *None* for a
            ``SystemExit`` (SIGTERM / ``sys.exit``).
        sigterm_received: Whether the SIGTERM handler fired before the escape.
        elapsed_time: Seconds elapsed since the guard started.
        stage: Generic stage label (``"SIGTERM received"`` or
            ``"Unexpected exit"``).
        message: Human-readable failure message.
    """

    caught_exception: BaseException | None
    sigterm_received: bool
    elapsed_time: float
    stage: str
    message: str


def run_guarded(
    body: Callable[[], int],
    *,
    project_dir: Path,
    from_label_id: str,
    general_category: str,
    comment_header: str,
    build_comment: Callable[[GuardOutcome], str] | None = None,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
    issue_number: int | None = None,
) -> int:
    """Run ``body`` under a shared LLM-failure safety net.

    A **clean return** from ``body()`` — any exit code (``0`` or ``1``) — is
    terminal; the net stays silent. The net fires **only on an escape**: an
    unexpected :class:`Exception` (netted, returns ``1``) or a
    :class:`SystemExit` (netted, then **re-raised** to preserve SIGTERM /
    ``sys.exit`` parity). Every netted escape maps to ``general_category`` —
    precise ``timeout``/``mcp_unavailable`` labels come only from the
    deliberate in-body classify-and-fail paths.

    Args:
        body: The workflow callable returning an exit code.
        project_dir: Path to the project git repository.
        from_label_id: Current workflow (busy) label ID to transition from.
        general_category: General failure label applied on any netted escape.
        comment_header: Header for the generic net comment (used when
            ``build_comment`` is not supplied).
        build_comment: Optional closure building the net comment from the
            :class:`GuardOutcome`; read at net time so it reflects live locals.
        update_issue_labels: Whether to attempt a label transition.
        post_issue_comments: Whether to post a failure comment.
        issue_number: Caller-provided issue number for the failure handler.

    Returns:
        ``body``'s exit code on a clean return, or ``1`` on a netted
        (non-``SystemExit``) escape.

    Raises:
        SystemExit: Re-raised after netting when ``body`` exits via
            ``sys.exit`` / SIGTERM.
    """
    start = time.time()
    sigterm_received = False

    def sigterm_handler(_signum: int, _frame: Any) -> None:
        nonlocal sigterm_received
        sigterm_received = True
        sys.exit(1)

    def _net(caught: BaseException | None) -> None:
        # Wrapped by the caller in try/except so net-failure never crashes.
        stage = "SIGTERM received" if sigterm_received else "Unexpected exit"
        if isinstance(caught, McpServersUnavailableError):
            message = format_mcp_unavailable_message(caught)
        elif sigterm_received:
            message = "Workflow terminated by signal"
        else:
            message = "Workflow exited without reaching a terminal state"
        outcome = GuardOutcome(
            caught_exception=caught,
            sigterm_received=sigterm_received,
            elapsed_time=time.time() - start,
            stage=stage,
            message=message,
        )
        if build_comment is not None:
            comment = build_comment(outcome)
        else:
            comment = (
                f"{comment_header}\n"
                f"**Stage:** {stage}\n"
                f"**Error:** {message}\n"
                f"**Elapsed:** {format_elapsed_time(outcome.elapsed_time)}"
            )
        handle_workflow_failure(
            WorkflowFailure(
                category=general_category,
                stage=stage,
                message=message,
                elapsed_time=outcome.elapsed_time,
            ),
            comment,
            project_dir,
            from_label_id=from_label_id,
            update_issue_labels=update_issue_labels,
            post_issue_comments=post_issue_comments,
            issue_number=issue_number,
        )

    def _safe_net(caught: BaseException | None) -> None:
        try:
            _net(caught)
        except Exception:  # pylint: disable=broad-exception-caught
            logger.error("Safety net failure handling also failed", exc_info=True)

    previous_handler = None
    try:
        previous_handler = signal.signal(signal.SIGTERM, sigterm_handler)
    except (OSError, ValueError):
        logger.debug("Could not register SIGTERM handler")

    try:
        return body()
    except SystemExit:
        _safe_net(None)
        raise
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected exception in workflow", exc_info=True)
        _safe_net(exc)
        return 1
    finally:
        if previous_handler is not None:
            try:
                signal.signal(signal.SIGTERM, previous_handler)
            except (OSError, ValueError):
                pass
