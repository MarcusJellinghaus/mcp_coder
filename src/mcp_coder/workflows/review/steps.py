"""Lane-context resolution and the implementation-lane after-steps gates.

These are the non-loop helpers the shared review engine (:mod:`core`) delegates
to around the round loop:

* :func:`_resolve_context` — resolve the issue number and (implementation lane
  only) the base branch the reviewer diffs against, *before* the loop.
* :func:`_after_steps` — run the rebase + CI gates *after* a dismiss (final
  gate) or a ``tasks`` application (mid-loop), for ``review-implementation``.

Both are behaviour-preserving relocations out of ``core`` to keep that module
under its line budget; the loop imports them back unchanged.
"""

import logging
from pathlib import Path

from mcp_coder.mcp_workspace_git import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from mcp_coder.workflow_steps.ci import check_and_fix_ci
from mcp_coder.workflow_steps.rebase import _attempt_rebase_and_push
from mcp_coder.workflow_utils.base_branch import detect_base_branch
from mcp_coder.workflow_utils.failure_handling import llm_failure_reason

from .config import ReviewConfig

logger = logging.getLogger(__name__)


def _resolve_context(
    config: ReviewConfig, project_dir: Path
) -> tuple[int | None, str | None]:
    """Resolve the issue number and (impl only) the base branch to diff against.

    Args:
        config: The review workflow config.
        project_dir: Repository root.

    Returns:
        ``(issue_number, base_branch)``. ``base_branch`` is ``None`` when the
        workflow does not inject one (``review-plan``); for
        ``review-implementation`` (``inject_base_branch``) it is the detected
        base branch the reviewer diffs the feature branch against.
    """
    issue_number: int | None = None
    branch_name = get_current_branch_name(project_dir)
    if branch_name:
        issue_number = extract_issue_number_from_branch(branch_name)

    base_branch: str | None = None
    if config.inject_base_branch:
        base_branch = detect_base_branch(project_dir)
    return issue_number, base_branch


def _after_steps(
    config: ReviewConfig,
    project_dir: Path,
    provider: str,
    mcp_config: str | None,
    settings_file: str | None,
    is_dismiss: bool,
) -> str | None:
    """Run the after-steps (rebase + CI) for the implementation lane.

    ``review-plan`` has ``run_after_steps=False`` so this is a no-op there. For
    ``review-implementation`` it enforces two gates in order:

    1. **Rebase gate (mandated — never success on an unresolved rebase):** the
       branch is rebased onto its base branch via ``_attempt_rebase_and_push``.
       If that cannot complete cleanly (e.g. a merge conflict) the return is
       ``"rebase"``, which the caller routes to a needs-human handoff
       (``07:code-review``) — never a success and never a failure label.
    2. **CI gate:** ``check_and_fix_ci`` runs its own retries (reusing
       ``implement``'s prompt headers, overriding only ``session_dir_name``). A
       green result returns ``None``. A red result returns ``"ci"``: on the
       final dismiss gate (``is_dismiss``) the caller treats that as a terminal
       ``17f-ci`` failure; mid-loop the caller instead carries it forward as a
       finding (see :data:`core._CI_NOTE`).

    Args:
        config: The review workflow config.
        project_dir: Repository root.
        provider: LLM provider.
        mcp_config: Optional MCP config path.
        settings_file: Optional Claude settings file.
        is_dismiss: Whether this runs on the final dismiss gate (vs mid-loop).
            Logged for diagnostics; the caller owns the terminal-vs-finding
            interpretation of a red CI result.

    Returns:
        A failure reason (``"rebase"`` / ``"ci"`` / ``"timeout"`` /
        ``"mcp_unavailable"`` / ``"general"``) or ``None`` when the after-steps
        are clean or there is nothing to do. The broadened ``except`` scoped to
        the CI call categorizes a generic exception as ``"general"`` rather than
        letting it escape — but it does **not** wrap the rebase gate, so the
        ``"rebase"`` control-flow return is preserved.
    """
    if not config.run_after_steps:
        return None

    # --- rebase gate (mandated: never success on an unresolved rebase) ---
    if not _attempt_rebase_and_push(project_dir):
        # NotYetImplemented (#1066): a conflict-resolving automatic
        # ``mcp-coder git-tool rebase`` attempt slots in HERE once #1066 ships
        # (before the needs-human fallback). Until then a needs-rebase /
        # unresolvable-conflict outcome simply routes to needs-human
        # (``07:code-review``) and is never a success.
        logger.info("Rebase could not complete cleanly; routing to needs-human")
        return "rebase"

    # --- CI gate ---
    branch = get_current_branch_name(project_dir)
    if not branch:
        return None
    try:
        ci_ok = check_and_fix_ci(
            project_dir=project_dir,
            branch=branch,
            provider=provider,
            mcp_config=mcp_config,
            settings_file=settings_file,
            session_dir_name=config.session_dir_name,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return llm_failure_reason(exc) or "general"
    if ci_ok:
        return None
    if not is_dismiss:
        logger.info("CI is red mid-loop; carrying it forward as a review finding")
    return "ci"
