"""Automated ``mcp-coder rebase`` workflow — Python-driven (Issues #1066, #1085).

Python executes every git operation and every check deterministically: guards,
the rebase itself, the conflict loop, the baseline-vs-verification regression
comparison, the force-push, and a ``finally`` abort safety net. The LLM is a
content editor only, invoked for exactly two jobs — resolving non-``pr_info/``
merge conflicts (three-stage content inlined by Python) and fixing regressions
found by the deterministic check comparison. Success is decided purely from
repository state plus a set-difference of failure keys; the LLM never
self-reports an outcome.
"""

import json
import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.storage.session_storage import store_session
from mcp_coder.mcp_workspace_git import (
    BaseBranchSource,
    RebaseResult,
    commit_all_changes,
    fetch_remote,
    get_conflict_blob_info,
    get_current_branch_name,
    get_latest_commit_sha,
    get_remote_url,
    get_working_tree_status,
    git_push,
    has_staged_changes,
    is_rebase_in_progress,
    list_tree,
    needs_rebase,
    read_conflict_stage,
    rebase_abort,
    rebase_continue,
    rebase_skip,
    rebase_start,
    resolve_take_theirs_or_remove,
    stage_all_changes,
)
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.workflow_steps.commit import check_formatter_config, run_formatters
from mcp_coder.workflow_steps.constants import LLM_INACTIVITY_TIMEOUT_SECONDS
from mcp_coder.workflow_steps.rebase import (
    BranchCheck,
    _check_branch_not_moved,
    _reset_hard,
)
from mcp_coder.workflow_utils.base_branch import (
    check_base_branch_on_origin,
    detect_base_branch_with_source,
)
from mcp_coder.workflows.rebase_checks import (
    CheckRunError,
    FailureKey,
    _run_all_checks,
)

logger = logging.getLogger(__name__)


def _is_clean(project_dir: Path) -> bool:
    """Fail-closed clean check: a git failure is never clean.

    Returns:
        True only if the status query succeeded and the tree is clean.
    """
    status = get_working_tree_status(project_dir)
    return status["success"] and status["clean"]


def _rebase_in_progress_or_none(project_dir: Path) -> bool | None:
    """Best-effort rebase-state probe for except/finally sites.

    Returns:
        Whether a rebase is in progress, or None (logged) if it cannot be
        determined.
    """
    try:
        return is_rebase_in_progress(project_dir)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Could not determine rebase state: %s", exc)
        return None


def _abort_rebase(project_dir: Path) -> None:
    """Best-effort ``git rebase --abort`` (never raises; a failure is logged).

    Used by the ``finally`` safety net.
    """
    result = rebase_abort(project_dir)
    if not result["success"]:
        logger.error(
            "git rebase --abort failed: %s", result["stderr"] or result["error"]
        )


def _restore_note(project_dir: Path, sha: str) -> str:
    """Restore pre-rebase state via the shared ``_reset_hard``.

    Returns:
        The suffix for the user-visible abort message.
    """
    if _reset_hard(project_dir, sha):
        return "; pre-rebase state restored"
    return "; restoring pre-rebase state FAILED (see log)"


def _rebase_success_shape(project_dir: Path, pre_sha: str) -> bool:
    """Return True iff HEAD moved off ``pre_sha``, tree is clean, and not mid-rebase.

    This is the git-side corroboration of a claimed rebase success: no rebase may
    be in progress, the working tree must be clean, and HEAD must differ from the
    pre-rebase commit. An undeterminable rebase state (logged) counts as failure.
    """
    if _rebase_in_progress_or_none(project_dir) is not False:
        return False
    if not _is_clean(project_dir):
        return False
    return get_latest_commit_sha(project_dir) != pre_sha


# --- Conflict handling ---


def _has_conflict_markers(project_dir: Path, file: str) -> bool:
    """Return True if ``file`` still contains git conflict marker lines.

    Only the seven-char ``<<<<<<< `` / ``>>>>>>> `` line prefixes count — a
    bare ``=======`` appears in legitimate text (e.g. markdown underlines).
    A missing file is marker-free (legitimately deleted during resolution).
    """
    path = project_dir / file
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return any(line.startswith(("<<<<<<< ", ">>>>>>> ")) for line in text.splitlines())


def _show_stage(project_dir: Path, stage: int, file: str) -> str | None:
    """Return the content of ``:<stage>:<file>``, or ``None`` when absent.

    Stages: 1 = common ancestor (merge base), 2 = ours (the base branch being
    rebased onto), 3 = theirs (the feature commits being replayed). A missing
    side (e.g. delete/modify), a binary blob or a read failure yields ``None``.
    """
    result = read_conflict_stage(project_dir, stage, file)
    return result["content"] if result["success"] else None


def _stage_all_and_continue(project_dir: Path) -> RebaseResult:
    """Stage everything and run the non-interactive ``rebase --continue``.

    Staging everything is deliberate (no pathspec): per-file adds break on
    delete/modify resolutions and adjacent LLM edits. A staging failure
    surfaces via the continue (it stops again) and the loop's re-check.

    Returns:
        The ``RebaseResult`` of the continue; ``stopped_on_conflict`` usually
        means the next commit also conflicts (the loop's continue condition).
    """
    stage_all_changes(project_dir)
    return rebase_continue(project_dir)


# --- Check baseline / comparison: extracted to rebase_checks.py ---


_STANDARD_BASES = {"main", "master"}


def _preflight(project_dir: Path) -> str | None:
    """Return ``None`` if the repo is safe to rebase, else an error message.

    Checks, in order: a clean working tree, no rebase/merge in progress, HEAD not
    on ``main``/``master``, an ``origin`` remote present, and a resolvable
    formatter configuration. Each failing check
    short-circuits with a human-readable reason (the caller maps this to exit
    code ``2``).
    """
    status = get_working_tree_status(project_dir)
    if not status["success"]:
        detail = (status["stderr"] or "").strip() or status["error"]
        return f"Could not read working tree status: {detail}"
    if not status["clean"]:
        return "Working tree not clean"

    if is_rebase_in_progress(project_dir):
        return "Repository is mid-rebase/merge"

    if get_current_branch_name(project_dir) in _STANDARD_BASES:
        return "Refusing to rebase main/master"

    if get_remote_url(project_dir) is None:
        return "Remote 'origin' not found"

    return check_formatter_config(project_dir, warn_legacy_key=True)


def _resolve_base_branch(
    project_dir: Path, base_branch_arg: str | None
) -> tuple[str | None, str | None]:
    """Return ``(base_branch, error)`` — exactly one side is non-``None``.

    An explicit ``base_branch_arg`` wins verbatim (no detection). Otherwise
    ``detect_base_branch_with_source`` runs; a base named in the issue's
    ``### Base Branch`` is accepted as-is — that section is only used when the
    issue body is trusted, otherwise detection falls back to the PR,
    merge-base or default heuristics — and a base found by those heuristics
    is accepted only when it is ``main``/``master``. Any
    other or undetectable base returns an error asking for ``--base-branch``.
    """
    if base_branch_arg:
        return (base_branch_arg, None)

    detected = detect_base_branch_with_source(project_dir)
    if detected is None:
        return (None, "Could not detect base branch; pass --base-branch")
    branch, source = detected
    if source is BaseBranchSource.ISSUE or branch in _STANDARD_BASES:
        return (branch, None)
    return (
        None,
        f"Base '{branch}' was detected from {source.value}, not named in the "
        "issue; add '### Base Branch' to the issue (only honoured when the issue "
        "body is trusted — see docs/repository-setup/github.md) or pass "
        "--base-branch",
    )


def _check_pr_info_absent_on_base(project_dir: Path, base_branch: str) -> str | None:
    """Return ``None`` if ``pr_info/`` is absent on ``origin/<base>``, else an error.

    Any entry under ``pr_info/`` on the base branch is refused (the base must not
    already carry ``pr_info/``). A failed listing (e.g. missing
    ``origin/<base>``) is an error too — never read as "absent".
    """
    listing = list_tree(project_dir, f"origin/{base_branch}", "pr_info")
    if not listing["success"]:
        detail = (listing["stderr"] or "").strip() or listing["error"]
        return f"Could not list pr_info/ on origin/{base_branch}: {detail}"
    return f"pr_info/ present on origin/{base_branch}" if listing["entries"] else None


# --- LLM steps ---

_CONFLICT_PROMPT_HEADER = "Rebase Conflict Resolution"
_REGRESSION_PROMPT_HEADER = "Rebase Regression Fix"

_ABSENT_SIDE_NOTE = "(absent — file does not exist on this side)"

_MARKER_RETRY_PROMPT = (
    "Conflict markers remain in: {files}. Edit these files so they contain the "
    "final merged content with no conflict markers. Same tools and rules as before."
)

# Stage labels mirror the wording of the "Rebase Conflict Resolution" prompt.
_STAGE_LABELS: tuple[tuple[int, str], ...] = (
    (1, "common ancestor (merge base)"),
    (2, "ours (base branch)"),
    (3, "theirs (feature branch)"),
)


def _prompt_in_session(
    prompt: str,
    session_id: str | None,
    *,
    project_dir: Path,
    provider: str,
    env_vars: dict[str, str],
    mcp_config: str | None,
    settings_file: str | None,
    step_name: str,
) -> tuple[str, str | None]:
    """Send one prompt in the resumable rebase LLM session.

    Issues a single ``prompt_llm`` call (``session_id=None`` starts the
    session; a previous id resumes it), then best-effort persists the exchange
    under ``.mcp-coder/rebase_sessions``. LLM errors/timeouts propagate to the
    orchestrator, which maps them to a needs-human exit.

    Returns:
        ``(response_text, new_session_id)`` — the caller threads the session
        id into the next call. A provider that reports no session id (the turn
        was not recorded, e.g. langchain drops an id nothing was stored under)
        never clears the id passed in: that conversation is still on disk, so
        the next step resumes it rather than silently starting a blank one.
    """
    branch_name = get_branch_name_for_logging(project_dir)
    response = prompt_llm(
        prompt,
        provider=provider,
        session_id=session_id,
        # Tool-using site (conflict/regression edits): inactivity budget, not wall-clock.
        timeout=LLM_INACTIVITY_TIMEOUT_SECONDS,
        env_vars=env_vars,
        project_dir=str(project_dir),
        mcp_config=mcp_config,
        settings_file=settings_file,
        branch_name=branch_name,
    )
    try:
        store_session(
            response_data=response,
            prompt=prompt,
            store_path=str(project_dir / ".mcp-coder" / "rebase_sessions"),
            step_name=step_name,
            branch_name=branch_name,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to store rebase session: %s", exc)
    new_session_id = response.get("session_id")
    if new_session_id is None:
        logger.warning(
            "Step %s returned no resumable session id; keeping the current one",
            step_name,
        )
        new_session_id = session_id
    return response.get("text", "") or "", new_session_id


def _build_conflict_prompt(project_dir: Path, files: list[str]) -> str:
    """Build the conflict-resolution prompt with three-stage content inlined.

    Each conflicted file contributes a block: its path, then the common
    ancestor (merge base) / ours / theirs contents in fenced blocks. A side
    absent from the index (delete/modify conflict) renders an absence note
    instead of content.

    Returns:
        The assembled conflict-resolution prompt string.
    """
    blocks: list[str] = []
    for file in files:
        parts = [f"### `{file}`"]
        for stage, label in _STAGE_LABELS:
            content = _show_stage(project_dir, stage, file)
            if content is None:
                parts.append(f"**{label}:** {_ABSENT_SIDE_NOTE}")
            else:
                parts.append(f"**{label}:**\n```\n{content}\n```")
        blocks.append("\n\n".join(parts))
    template = get_prompt(str(PROMPTS_FILE_PATH), _CONFLICT_PROMPT_HEADER)
    return template.replace("[conflict_context]", "\n\n".join(blocks))


def _build_regression_fix_prompt(
    regression_text: str, markers: list[str] | None = None
) -> str:
    """Build the regression-fix prompt with the failure-key text inlined.

    With ``markers``, the prompt tells the LLM to pass the same pytest marker
    filter the deterministic checks used; without, the placeholder is removed.

    Returns:
        The assembled regression-fix prompt string.
    """
    filter_text = ""
    if markers:
        filter_text = (
            "When you run `mcp__mcp-tools-py__run_pytest_check`, pass "
            f"markers={json.dumps(markers)} so tests that reach external "
            "services are excluded."
        )
    template = get_prompt(str(PROMPTS_FILE_PATH), _REGRESSION_PROMPT_HEADER)
    return template.replace("[regression_output]", regression_text).replace(
        "[pytest_marker_filter]", filter_text
    )


def _format_failure_keys(keys: set[FailureKey]) -> str:
    """Render failure keys as sorted, one-per-line text ("" for an empty set).

    Sorted output is required for determinism: besides feeding the regression
    prompt, this string doubles as the stall-guard comparison value.

    Returns:
        The sorted, newline-joined text rendering of the keys, or an empty
        string for an empty set.
    """
    return "\n".join(f"{key[0]}: {' '.join(key[1:])}" for key in sorted(keys))


# --- Orchestrator --------------------------------------------------------------

_MAX_SAME_FILE_CONFLICTS = 3  # /rebase abort rule 4
_MAX_FIX_ATTEMPTS = 2  # /rebase abort rule 5


@dataclass(frozen=True)
class RebaseRunResult:
    """Outcome of one ``run_rebase_workflow`` call."""

    exit_code: int  # 0 success/no-op, 1 aborted, 2 error / push rejected
    reason: str  # human-readable; never "" on a non-zero exit
    push_rejected: bool = False  # True only for the force-push rejection
    branch_check: BranchCheck | None = None  # Set only when this check stopped the run


def _end(
    exit_code: int,
    reason: str,
    *,
    push_rejected: bool = False,
    branch_check: BranchCheck | None = None,
) -> RebaseRunResult:
    """Log the end of the run and build the result.

    Exit ``1`` and the force-push rejection log ``Aborted: <reason>`` at OUTPUT
    level, any other exit ``2`` logs the reason as an error, and exit ``0``
    logs it at OUTPUT level.

    Returns:
        The ``RebaseRunResult`` for ``exit_code`` / ``reason``.
    """
    if exit_code == 1 or push_rejected:
        logger.log(OUTPUT, "Aborted: %s", reason)
    elif exit_code == 2:
        logger.error("%s", reason)
    else:
        logger.log(OUTPUT, "%s", reason)
    return RebaseRunResult(exit_code, reason, push_rejected, branch_check)


def run_rebase_workflow(
    project_dir: Path,
    provider: str,
    base_branch: str | None = None,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    markers: list[str] | None = None,
) -> RebaseRunResult:
    """Orchestrate the automated rebase (Python-driven).

    Composes the deterministic shell: pre-flight guards -> base-branch guard ->
    ``pr_info/``-on-base guard -> no-op short-circuit -> branch-moved check ->
    baseline checks -> Python-executed rebase with a conflict loop (LLM edits
    content only) -> regression verification and bounded LLM fix loop -> git
    corroboration gate -> second branch-moved check (with restore) ->
    Python-owned force-push (with restore on rejection) -> ``finally`` abort
    safety net.

    See the exit-code contract in ``summary.md``.

    ``markers`` (pytest ``-m`` expressions) filter every check run and are
    passed on to the regression-fix prompt; ``None`` runs the full suite.

    Returns:
        A ``RebaseRunResult``: ``exit_code`` ``0`` (success or no-op), ``1``
        (aborted -> needs-human) or ``2`` (error / push rejected /
        ``origin/<branch>`` has commits this checkout does not have), a
        human-readable ``reason``, and ``push_rejected`` set only when the
        force-push was rejected.
    """
    logger.log(OUTPUT, "Starting automated rebase...")

    err = _preflight(project_dir)
    if err:
        return _end(2, f"Pre-flight failed: {err}")

    base, base_err = _resolve_base_branch(project_dir, base_branch)
    if base_err:
        return _end(2, f"Base-branch guard failed: {base_err}")
    # Guaranteed by _resolve_base_branch when base_err is falsy.
    assert base is not None  # noqa: S101  # nosec B101

    fetch_remote(project_dir, "origin")

    missing_err = check_base_branch_on_origin(project_dir, base)
    if missing_err:
        return _end(2, f"Base-branch guard failed: {missing_err}")

    pr_info_err = _check_pr_info_absent_on_base(project_dir, base)
    if pr_info_err:
        return _end(2, f"pr_info/ guard failed: {pr_info_err}")

    needed, reason = needs_rebase(project_dir, base)
    if not needed:
        # needs_rebase signals real failures (missing origin/<base>, fetch
        # failure, detached HEAD, ...) via an "error: " reason prefix; those are
        # errors (exit 2), not a genuine up-to-date no-op (exit 0).
        if reason.startswith("error:"):
            return _end(2, f"Rebase check failed for origin/{base}: {reason}")
        return _end(0, f"Already current with origin/{base}; nothing to do")

    pre_sha = get_latest_commit_sha(project_dir)
    if pre_sha is None:
        return _end(2, "Could not resolve HEAD commit before rebase")

    # needs_rebase has just fetched, so the tracking ref is current.
    branch_check = _check_branch_not_moved(project_dir, pre_sha)
    if branch_check in ("moved", "error"):
        return _end(
            2,
            "Branch check failed; nothing rebased or pushed",
            branch_check=branch_check,
        )

    logger.log(OUTPUT, "Running baseline checks (pytest, pylint, mypy)...")
    try:
        baseline = _run_all_checks(project_dir, markers)
    except CheckRunError as exc:
        # No git mutation has happened yet — plain infrastructure error.
        return _end(2, f"Baseline checks failed to run: {exc}")
    if baseline:
        logger.log(
            OUTPUT,
            "%d pre-existing failure(s) in baseline — these will not block the rebase",
            len(baseline),
        )

    try:
        session_id: str | None = None
        env_vars = prepare_llm_environment(project_dir)
        conflict_counts: Counter[str] = Counter()
        stop = 0

        logger.log(
            OUTPUT,
            "Rebasing %s onto origin/%s...",
            get_branch_name_for_logging(project_dir),
            base,
        )
        result: RebaseResult = rebase_start(project_dir, f"origin/{base}")
        while result["status"] != "completed":
            if result["status"] == "error":
                detail = (result["stderr"] or "").strip() or result["error"]
                return _end(1, f"git rebase failed unexpectedly: {detail}")
            info = get_conflict_blob_info(project_dir)
            if not info["success"]:
                return _end(1, f"could not read conflicts: {info['error']}")
            files = [entry["path"] for entry in info["entries"]]
            if not files:
                if not has_staged_changes(project_dir):
                    # Resolved commit became empty (all changes already on base).
                    logger.log(
                        OUTPUT,
                        "Skipping commit made redundant by rebase (already on base)...",
                    )
                    result = rebase_skip(project_dir)
                    continue
                return _end(
                    1,
                    "rebase stopped without conflicted files: "
                    f"{(result['stderr'] or '').strip()}",
                )
            binary = next(
                (entry["path"] for entry in info["entries"] if entry["is_binary"]),
                None,
            )
            if binary:
                return _end(1, f"binary conflict in {binary}")
            conflict_counts.update(files)
            repeated = [
                f
                for f, count in conflict_counts.items()
                if count >= _MAX_SAME_FILE_CONFLICTS
            ]
            if repeated:
                return _end(
                    1,
                    f"{repeated[0]} conflicted at "
                    f"{conflict_counts[repeated[0]]} rebase stops",
                )
            pr_info_files = [f for f in files if f.startswith("pr_info/")]
            for file in pr_info_files:
                # Keep the feature side; removed if the feature branch deleted it.
                if not resolve_take_theirs_or_remove(project_dir, file)["success"]:
                    return _end(1, f"could not auto-resolve {file}")
            others = [f for f in files if f not in pr_info_files]
            if others:
                logger.log(
                    OUTPUT, "Resolving %d conflicted file(s) via LLM...", len(others)
                )
                stop += 1
                _, session_id = _prompt_in_session(
                    _build_conflict_prompt(project_dir, others),
                    session_id,
                    project_dir=project_dir,
                    provider=provider,
                    env_vars=env_vars,
                    mcp_config=mcp_config,
                    settings_file=settings_file,
                    step_name=f"conflict_{stop}",
                )
                unresolved = [
                    f for f in others if _has_conflict_markers(project_dir, f)
                ]
                if unresolved:
                    # One retry per stop, resuming the same session.
                    _, session_id = _prompt_in_session(
                        _MARKER_RETRY_PROMPT.format(files=", ".join(unresolved)),
                        session_id,
                        project_dir=project_dir,
                        provider=provider,
                        env_vars=env_vars,
                        mcp_config=mcp_config,
                        settings_file=settings_file,
                        step_name=f"conflict_{stop}_retry",
                    )
                    unresolved = [
                        f for f in unresolved if _has_conflict_markers(project_dir, f)
                    ]
                if unresolved:
                    return _end(
                        1, f"conflict markers remain in {', '.join(unresolved)}"
                    )
            result = _stage_all_and_continue(project_dir)

        logger.log(OUTPUT, "Verifying no regression...")
        regressions = _run_all_checks(project_dir, markers) - baseline
        attempt = 0
        last_text: str | None = None
        while regressions and attempt < _MAX_FIX_ATTEMPTS:
            text = _format_failure_keys(regressions)
            if text == last_text:
                break  # stall guard: the LLM changed nothing observable
            last_text = text
            attempt += 1
            logger.log(
                OUTPUT,
                "Fixing %d regression(s) (attempt %d/%d)...",
                len(regressions),
                attempt,
                _MAX_FIX_ATTEMPTS,
            )
            _, session_id = _prompt_in_session(
                _build_regression_fix_prompt(text, markers),
                session_id,
                project_dir=project_dir,
                provider=provider,
                env_vars=env_vars,
                mcp_config=mcp_config,
                settings_file=settings_file,
                step_name=f"fix_{attempt}",
            )
            run_formatters(project_dir)
            # Result ignored: nothing to commit is harmless (re-check runs anyway;
            # identical regressions then hit the stall guard or attempt cap).
            commit_all_changes(
                f"fix: resolve regressions from rebase onto origin/{base}", project_dir
            )
            regressions = _run_all_checks(project_dir, markers) - baseline
        if regressions:
            note = _restore_note(project_dir, pre_sha)
            return _end(1, f"{len(regressions)} unfixed regression(s){note}")

        if not _rebase_success_shape(project_dir, pre_sha):
            # Reset is safe here: the rebase completed, so the finally net
            # won't act — same never-leave-rebased-unpushed invariant as the
            # other post-rebase failure paths.
            note = _restore_note(project_dir, pre_sha)
            return _end(1, f"git state does not corroborate a successful rebase{note}")

        # A fetch during the checks or LLM steps could have outdated the first check.
        branch_check = _check_branch_not_moved(project_dir, pre_sha)
        if branch_check in ("moved", "error"):
            note = _restore_note(project_dir, pre_sha)
            return _end(
                2,
                f"Branch check failed; nothing pushed{note}",
                branch_check=branch_check,
            )

        logger.log(OUTPUT, "Force-pushing (with lease)...")
        push_result = git_push(project_dir, force_with_lease=True)
        if push_result["success"]:
            return _end(0, f"Rebased and force-pushed onto origin/{base}")

        logger.error("Force-push rejected/failed: %s", push_result.get("error"))
        note = _restore_note(project_dir, pre_sha)  # never leave unpushed commits
        return _end(2, f"force-push rejected{note}", push_rejected=True)
    except CheckRunError as exc:
        # Verification/re-check infrastructure failure: the rebase already
        # completed, so the finally net cannot restore — explicit reset.
        note = _restore_note(project_dir, pre_sha)
        logger.error("Verification checks failed to run: %s", exc)
        return _end(1, f"Verification checks failed to run: {exc}{note}")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # LLM failure/timeout or unexpected error. Mid-rebase: the finally net
        # aborts. Post-rebase (regression-fix phase): explicit reset — same
        # never-leave-rebased-unpushed invariant as the paths above. Unknown
        # rebase state: neither (logged by the probe).
        logger.error("Rebase failed: %s", exc)
        detail = str(exc) or type(exc).__name__
        if _rebase_in_progress_or_none(project_dir) is False:
            return _end(1, f"{detail}{_restore_note(project_dir, pre_sha)}")
        return _end(1, detail)
    finally:
        if _rebase_in_progress_or_none(project_dir):
            _abort_rebase(project_dir)
