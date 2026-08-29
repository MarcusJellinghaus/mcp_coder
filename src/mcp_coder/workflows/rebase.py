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

import logging
from collections import Counter
from pathlib import Path
from typing import NamedTuple

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.storage.session_storage import store_session
from mcp_coder.mcp_tools_py import run_format_code
from mcp_coder.mcp_workspace_git import (
    fetch_remote,
    get_current_branch_name,
    get_latest_commit_sha,
    git_push,
    is_working_directory_clean,
    needs_rebase,
)
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.utils.subprocess_runner import execute_command
from mcp_coder.workflow_steps.constants import LLM_INACTIVITY_TIMEOUT_SECONDS
from mcp_coder.workflow_utils.base_branch import detect_base_branch
from mcp_coder.workflows.rebase_checks import (
    CheckRunError,
    FailureKey,
    _run_all_checks,
)

logger = logging.getLogger(__name__)


class _GitResult(NamedTuple):
    """Minimal git result exposing ``returncode``/``stdout``/``stderr``.

    Mirrors the subset of ``subprocess.CompletedProcess`` that the rebase
    callers inspect, decoupling them from the ``mcp-coder-utils``
    ``CommandResult`` (whose field is ``return_code``).
    """

    returncode: int
    stdout: str
    stderr: str


def _run_git(project_dir: Path, *args: str) -> _GitResult:
    """Run ``git <args>`` in ``project_dir`` (list form, no shell, ``check=False``).

    Never raises on a non-zero git exit; the caller decides what a failure means.

    Returns:
        A result object so callers can inspect ``.returncode``, ``.stdout``
        and ``.stderr``.
    """
    # Fixed argv, no shell, trusted ``git`` CLI — routed through the
    # subprocess_runner shim (mcp-coder-utils) per the library-isolation contract.
    result = execute_command(["git", *args], cwd=str(project_dir))
    return _GitResult(
        returncode=result.return_code,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _is_rebase_in_progress(project_dir: Path) -> bool:
    """Return True if a rebase is mid-flight.

    Detected purely from the filesystem: git creates ``.git/rebase-merge`` (merge
    backend) or ``.git/rebase-apply`` (apply backend) while a rebase is unfinished.
    """
    git_dir = project_dir / ".git"
    return (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists()


def _abort_rebase(project_dir: Path) -> None:
    """Best-effort ``git rebase --abort`` (never raises).

    Used by the ``finally`` safety net; if no rebase is in progress git simply
    exits non-zero, which ``_run_git`` swallows.
    """
    _run_git(project_dir, "rebase", "--abort")


def _reset_hard(project_dir: Path, sha: str) -> None:
    """Restore pre-rebase state with ``git reset --hard <sha>``."""
    _run_git(project_dir, "reset", "--hard", sha)


def _rebase_success_shape(project_dir: Path, pre_sha: str) -> bool:
    """Return True iff HEAD moved off ``pre_sha``, tree is clean, and not mid-rebase.

    This is the git-side corroboration of a claimed rebase success: no rebase may
    be in progress, the working tree must be clean, and HEAD must differ from the
    pre-rebase commit.
    """
    if _is_rebase_in_progress(project_dir):
        return False
    if not is_working_directory_clean(project_dir):
        return False
    return get_latest_commit_sha(project_dir) != pre_sha


# --- Conflict handling ---


def _conflicted_files(project_dir: Path) -> list[str]:
    """Return the unmerged paths (repo-relative, git's own output order)."""
    result = _run_git(project_dir, "diff", "--name-only", "--diff-filter=U")
    return [line for line in result.stdout.splitlines() if line.strip()]


def _binary_conflict(project_dir: Path) -> str | None:
    """Return the first conflicted path with binary content, or ``None``.

    At a conflict stop, bare ``git diff --numstat`` omits unmerged paths
    (verified against real git), so binary-ness is decided at blob level:
    stage SHAs via ``git ls-files -u``, then ``git diff --numstat <ours>
    <theirs>`` where ``-`` added/deleted columns reliably mean binary.
    """
    listing = _run_git(project_dir, "ls-files", "-u")
    stages: dict[str, dict[int, str]] = {}
    for line in listing.stdout.splitlines():
        # "<mode> <sha> <stage>\t<path>"
        meta, _, path = line.partition("\t")
        fields = meta.split()
        if len(fields) != 3 or not path:
            continue
        stages.setdefault(path, {})[int(fields[2])] = fields[1]
    for path, shas in stages.items():
        # A missing side (delete/modify) falls back to the common ancestor so
        # single-sided binary content is still caught; identical blobs simply
        # produce no diff output.
        ours = shas.get(2) or shas.get(1)
        theirs = shas.get(3) or shas.get(1)
        if not ours or not theirs:
            continue
        numstat = _run_git(project_dir, "diff", "--numstat", ours, theirs)
        for stat_line in numstat.stdout.splitlines():
            columns = stat_line.split("\t")
            if len(columns) >= 2 and columns[0] == "-" and columns[1] == "-":
                return path
    return None


def _resolve_pr_info_conflict(project_dir: Path, file: str) -> bool:
    """Resolve a ``pr_info/`` conflict deterministically (keep the feature side).

    ``git checkout --theirs`` takes the feature version (stage 3); when that
    side does not exist (delete/modify — the feature branch deleted the file)
    the fallback is ``git rm`` so the file stays deleted.

    Returns:
        True when the file is resolved and staged.
    """
    checkout = _run_git(project_dir, "checkout", "--theirs", "--", file)
    if checkout.returncode == 0:
        return _run_git(project_dir, "add", "--", file).returncode == 0
    return _run_git(project_dir, "rm", "--", file).returncode == 0


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
    side (e.g. delete/modify) yields ``None``.
    """
    result = _run_git(project_dir, "show", f":{stage}:{file}")
    if result.returncode != 0:
        return None
    return result.stdout


def _stage_all_and_continue(project_dir: Path) -> _GitResult:
    """Stage everything and run the non-interactive ``rebase --continue``.

    ``git add -A`` is deliberate (no pathspec): per-file adds break on
    delete/modify resolutions and adjacent LLM edits. ``-c core.editor=true``
    keeps the continue from ever blocking on an editor.

    Returns:
        The ``_GitResult`` of the continue; non-zero usually means the next
        commit also conflicts (the loop's continue condition, not an error).
    """
    _run_git(project_dir, "add", "-A")
    return _run_git(project_dir, "-c", "core.editor=true", "rebase", "--continue")


# --- Check baseline / comparison: extracted to rebase_checks.py ---


_STANDARD_BASES = {"main", "master"}


def _preflight(project_dir: Path) -> str | None:
    """Return ``None`` if the repo is safe to rebase, else an error message.

    Checks, in order: a clean working tree, no rebase/merge in progress, HEAD not
    on ``main``/``master``, and an ``origin`` remote present. Each failing check
    short-circuits with a human-readable reason (the caller maps this to exit
    code ``2``).
    """
    if not is_working_directory_clean(project_dir):
        return "Working tree not clean"

    merge_head = project_dir / ".git" / "MERGE_HEAD"
    if _is_rebase_in_progress(project_dir) or merge_head.exists():
        return "Repository is mid-rebase/merge"

    if get_current_branch_name(project_dir) in _STANDARD_BASES:
        return "Refusing to rebase main/master"

    if _run_git(project_dir, "remote", "get-url", "origin").returncode != 0:
        return "Remote 'origin' not found"

    return None


def _resolve_base_branch(
    project_dir: Path, base_branch_arg: str | None
) -> tuple[str | None, str | None]:
    """Return ``(base_branch, error)`` — exactly one side is non-``None``.

    An explicit ``base_branch_arg`` wins verbatim (no detection). Otherwise
    ``detect_base_branch`` runs and only the standard ``main``/``master`` bases
    are accepted automatically; a non-standard or undetectable base returns an
    error asking for an explicit ``--base-branch``.
    """
    if base_branch_arg:
        return (base_branch_arg, None)

    detected = detect_base_branch(project_dir)
    if detected is None:
        return (None, "Could not detect base branch; pass --base-branch")
    if detected in _STANDARD_BASES:
        return (detected, None)
    return (None, f"Non-standard base '{detected}'; pass --base-branch to confirm")


def _check_pr_info_absent_on_base(project_dir: Path, base_branch: str) -> str | None:
    """Return ``None`` if ``pr_info/`` is absent on ``origin/<base>``, else an error.

    Uses ``git ls-tree origin/<base> pr_info``: any non-empty stdout means the
    path exists on the base branch, which is refused (the base must not already
    carry ``pr_info/``).
    """
    result = _run_git(project_dir, "ls-tree", f"origin/{base_branch}", "pr_info")
    if result.stdout.strip():
        return f"pr_info/ present on origin/{base_branch}"
    return None


# --- LLM steps ---

_CONFLICT_PROMPT_HEADER = "Rebase Conflict Resolution"
_REGRESSION_PROMPT_HEADER = "Rebase Regression Fix"

_ABSENT_SIDE_NOTE = "(absent — file does not exist on this side)"

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
    execution_dir: Path | None,
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


def _build_regression_fix_prompt(regression_text: str) -> str:
    """Build the regression-fix prompt with the failure-key text inlined.

    Returns:
        The assembled regression-fix prompt string.
    """
    template = get_prompt(str(PROMPTS_FILE_PATH), _REGRESSION_PROMPT_HEADER)
    return template.replace("[regression_output]", regression_text)


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


def run_rebase_workflow(
    project_dir: Path,
    provider: str,
    base_branch: str | None = None,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    execution_dir: Path | None = None,
) -> int:
    """Orchestrate the automated rebase (Python-driven).

    Composes the deterministic shell: pre-flight guards -> base-branch guard ->
    ``pr_info/``-on-base guard -> no-op short-circuit -> baseline checks ->
    Python-executed rebase with a conflict loop (LLM edits content only) ->
    regression verification and bounded LLM fix loop -> git corroboration
    gate -> Python-owned force-push (with restore on rejection) -> ``finally``
    abort safety net.

    See the exit-code contract in ``summary.md``.

    Returns:
        ``0`` (success or no-op), ``1`` (aborted -> needs-human), or ``2``
        (error / push rejected).
    """
    logger.log(OUTPUT, "Starting automated rebase...")

    err = _preflight(project_dir)
    if err:
        logger.error("Pre-flight failed: %s", err)
        return 2

    base, base_err = _resolve_base_branch(project_dir, base_branch)
    if base_err:
        logger.error("Base-branch guard failed: %s", base_err)
        return 2
    assert base is not None  # nosec B101 — guaranteed by _resolve_base_branch

    fetch_remote(project_dir, "origin")

    pr_info_err = _check_pr_info_absent_on_base(project_dir, base)
    if pr_info_err:
        logger.error("pr_info/ guard failed: %s", pr_info_err)
        return 2

    needed, reason = needs_rebase(project_dir, base)
    if not needed:
        # needs_rebase signals real failures (missing origin/<base>, fetch
        # failure, detached HEAD, ...) via an "error: " reason prefix; those are
        # errors (exit 2), not a genuine up-to-date no-op (exit 0).
        if reason.startswith("error:"):
            logger.error("Rebase check failed for origin/%s: %s", base, reason)
            return 2
        logger.log(OUTPUT, "Already current with origin/%s; nothing to do", base)
        return 0

    pre_sha = get_latest_commit_sha(project_dir)
    if pre_sha is None:
        logger.error("Could not resolve HEAD commit before rebase")
        return 2

    logger.log(OUTPUT, "Running baseline checks (pytest, pylint, mypy)...")
    try:
        baseline = _run_all_checks(project_dir)
    except CheckRunError as exc:
        # No git mutation has happened yet — plain infrastructure error.
        logger.error("Baseline checks failed to run: %s", exc)
        return 2
    if baseline:
        logger.log(
            OUTPUT,
            "%d pre-existing failure(s) in baseline — "
            "these will not block the rebase",
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
        result = _run_git(project_dir, "rebase", f"origin/{base}")
        while result.returncode != 0:  # conflict stop (or unexpected failure)
            if not _is_rebase_in_progress(project_dir):
                logger.log(
                    OUTPUT,
                    "Aborted: git rebase failed unexpectedly: %s",
                    result.stderr.strip() or result.stdout.strip(),
                )
                return 1
            files = _conflicted_files(project_dir)
            if not files:
                if _run_git(project_dir, "diff", "--cached", "--quiet").returncode == 0:
                    # Resolved commit became empty (all changes already on base).
                    logger.log(
                        OUTPUT,
                        "Skipping commit made redundant by rebase "
                        "(already on base)...",
                    )
                    result = _run_git(project_dir, "rebase", "--skip")
                    continue
                logger.log(
                    OUTPUT,
                    "Aborted: rebase stopped without conflicted files: %s",
                    result.stderr.strip() or result.stdout.strip(),
                )
                return 1
            binary = _binary_conflict(project_dir)
            if binary:
                logger.log(OUTPUT, "Aborted: binary conflict in %s", binary)
                return 1
            conflict_counts.update(files)
            repeated = [
                f
                for f, count in conflict_counts.items()
                if count >= _MAX_SAME_FILE_CONFLICTS
            ]
            if repeated:
                logger.log(
                    OUTPUT,
                    "Aborted: %s conflicted at %d rebase stops",
                    repeated[0],
                    conflict_counts[repeated[0]],
                )
                return 1
            pr_info_files = [f for f in files if f.startswith("pr_info/")]
            for file in pr_info_files:
                if not _resolve_pr_info_conflict(project_dir, file):
                    logger.log(OUTPUT, "Aborted: could not auto-resolve %s", file)
                    return 1
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
                    execution_dir=execution_dir,
                    step_name=f"conflict_{stop}",
                )
                unresolved = [
                    f for f in others if _has_conflict_markers(project_dir, f)
                ]
                if unresolved:
                    logger.log(
                        OUTPUT,
                        "Aborted: conflict markers remain in %s",
                        ", ".join(unresolved),
                    )
                    return 1
            result = _stage_all_and_continue(project_dir)

        logger.log(OUTPUT, "Verifying no regression...")
        regressions = _run_all_checks(project_dir) - baseline
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
                _build_regression_fix_prompt(text),
                session_id,
                project_dir=project_dir,
                provider=provider,
                env_vars=env_vars,
                mcp_config=mcp_config,
                settings_file=settings_file,
                execution_dir=execution_dir,
                step_name=f"fix_{attempt}",
            )
            run_format_code(project_dir)
            _run_git(project_dir, "add", "-A")
            # An empty commit exits non-zero — harmless (re-check runs anyway;
            # identical regressions then hit the stall guard or attempt cap).
            _run_git(
                project_dir,
                "commit",
                "-m",
                f"fix: resolve regressions from rebase onto origin/{base}",
            )
            regressions = _run_all_checks(project_dir) - baseline
        if regressions:
            logger.log(
                OUTPUT,
                "Aborted: %d unfixed regression(s); pre-rebase state restored",
                len(regressions),
            )
            _reset_hard(project_dir, pre_sha)
            return 1

        if not _rebase_success_shape(project_dir, pre_sha):
            # Reset is safe here: the rebase completed, so the finally net
            # won't act — same never-leave-rebased-unpushed invariant as the
            # other post-rebase failure paths.
            logger.log(
                OUTPUT,
                "Aborted: git state does not corroborate a successful rebase; "
                "pre-rebase state restored",
            )
            _reset_hard(project_dir, pre_sha)
            return 1

        logger.log(OUTPUT, "Force-pushing (with lease)...")
        push_result = git_push(project_dir, force_with_lease=True)
        if push_result["success"]:
            logger.log(OUTPUT, "Rebased and force-pushed onto origin/%s", base)
            return 0

        logger.error("Force-push rejected/failed: %s", push_result.get("error"))
        _reset_hard(project_dir, pre_sha)  # never leave unpushed rebased commits
        logger.log(OUTPUT, "Aborted: force-push rejected; pre-rebase state restored")
        return 2
    except CheckRunError as exc:
        # Verification/re-check infrastructure failure: the rebase already
        # completed, so the finally net cannot restore — explicit reset.
        _reset_hard(project_dir, pre_sha)
        logger.error("Verification checks failed to run: %s", exc)
        logger.log(OUTPUT, "Aborted: checks failed to run; pre-rebase state restored")
        return 1
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # LLM failure/timeout or unexpected error. Mid-rebase: the finally net
        # aborts. Post-rebase (regression-fix phase): explicit reset — same
        # never-leave-rebased-unpushed invariant as the paths above.
        if not _is_rebase_in_progress(project_dir):
            _reset_hard(project_dir, pre_sha)
        logger.error("Rebase failed: %s", exc)
        logger.log(OUTPUT, "Aborted: %s", exc)
        return 1
    finally:
        if _is_rebase_in_progress(project_dir):
            _abort_rebase(project_dir)
