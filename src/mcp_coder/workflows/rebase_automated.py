"""Git-only rebase with the LLM rebase as fallback, for automated workflows.

Lives in ``workflows`` rather than in ``workflow_steps/rebase.py``: it composes
``run_rebase_workflow``, and ``workflow_steps`` sits below ``workflows`` in the
import-linter layers.
"""

import logging
from dataclasses import replace
from pathlib import Path

from mcp_coder.mcp_workspace_git import git_check_ignore
from mcp_coder.workflow_steps.commit import push_changes
from mcp_coder.workflow_steps.rebase import RebaseOutcome, _attempt_rebase_and_push
from mcp_coder.workflow_utils.failure_handling import exception_summary
from mcp_coder.workflows.rebase import run_rebase_workflow
from mcp_coder.workflows.rebase_permissions import rebase_settings_file

logger = logging.getLogger(__name__)

AUTOMATED_EXCLUDED_MARKERS: list[str] = [
    "not claude_cli_integration",
    "not copilot_cli_integration",
    "not langchain_integration",
    "not llm_integration",
    "not jenkins_integration",
    "not install_integration",
]

_LLM_TRIGGER_REASONS = ("conflict", "rebase_failed")
# A path inside the folder, never ".mcp-coder" itself: a "/.mcp-coder/*" rule
# does not match the folder, and a ".mcp-coder/" rule cannot match a missing one.
_IGNORE_PROBE = ".mcp-coder/rebase_sessions/probe"
_NOT_IGNORED = "No paths are ignored."


def _mcp_coder_dir_problem(project_dir: Path) -> str | None:
    """Return why the LLM rebase must not run (``.mcp-coder/`` not ignored), or None.

    The LLM rebase writes session files under ``.mcp-coder/``; if git tracks
    them, they would dirty the tree mid-rebase.

    Args:
        project_dir: Path to the project directory

    Returns:
        A problem description, or None when ``.mcp-coder/`` is gitignored.
    """
    try:
        output = git_check_ignore(project_dir, pathspec=[_IGNORE_PROBE])
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return (
            "LLM rebase skipped: could not check that .mcp-coder/ is gitignored: "
            f"{exception_summary(exc)}"
        )
    if output.strip() == _NOT_IGNORED:
        return "LLM rebase skipped: .mcp-coder/ is not gitignored"
    return None


def rebase_with_llm_fallback(
    project_dir: Path,
    provider: str,
    mcp_config: str | None,
    settings_override: str | None = None,
) -> RebaseOutcome:
    """Git-only rebase, then the LLM rebase on conflict / rebase_failed.

    After a successful LLM rebase the branch is pushed with a plain push,
    never ``--force-with-lease``.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider for the rebase session
        mcp_config: MCP config path for the rebase session
        settings_override: Already-resolved settings path; None uses the
            least-privilege rebase settings.

    Returns:
        The git-only ``RebaseOutcome`` unchanged when the LLM did not run.
        Otherwise ``reason`` is ``"ok"`` (LLM rebase and push succeeded),
        ``"push_failed"`` (push rejected), or the git-only reason with
        ``llm_detail`` explaining the hand-off.
    """
    outcome = _attempt_rebase_and_push(project_dir)
    if outcome.reason not in _LLM_TRIGGER_REASONS:
        return outcome

    problem = _mcp_coder_dir_problem(project_dir)
    if problem:
        logger.warning("%s", problem)
        return replace(outcome, llm_detail=problem)

    logger.info("Git-only rebase ended with %s - trying the LLM rebase", outcome.reason)
    try:
        with rebase_settings_file(settings_override) as settings:
            result = run_rebase_workflow(
                project_dir,
                provider,
                outcome.base_branch,
                mcp_config,
                settings,
                markers=AUTOMATED_EXCLUDED_MARKERS,
            )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("LLM rebase crashed", exc_info=True)
        return replace(
            outcome, llm_detail=f"LLM rebase crashed: {exception_summary(exc)}"
        )

    if result.push_rejected:
        return replace(
            outcome, reason="push_failed", files=(), llm_detail=result.reason
        )
    if result.exit_code != 0:
        return replace(outcome, llm_detail=result.reason)
    if not push_changes(project_dir):
        logger.warning("LLM rebase succeeded, but the plain push was rejected")
        return replace(
            outcome,
            reason="push_failed",
            files=(),
            llm_detail="LLM rebase succeeded, but the plain push was rejected",
        )
    return replace(outcome, reason="ok", files=(), llm_detail=result.reason)
