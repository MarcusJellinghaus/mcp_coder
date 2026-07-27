"""Automated ``mcp-coder rebase`` workflow — deterministic shell (Issue #1066).

Python owns the deterministic shell around a single LLM session: pre-flight
guards, the outcome→exit-code decision, the force-push, and a ``finally`` safety
net. This module currently holds only the two pure decision functions; git
helpers, guards, and the orchestrator are added in later steps.

The exit-code contract cross-checks two signals and never trusts either alone:
the LLM's self-reported outcome marker and the actual git repository state (git
is authoritative, worst-case-wins).
"""

import logging
import re
from pathlib import Path
from typing import Any, Callable, NamedTuple

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.mcp_tools_py import (
    MypyResult,
    PylintResult,
    run_mypy_check,
    run_pylint_check,
    run_pytest_check,
)
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
from mcp_coder.utils.subprocess_runner import execute_command
from mcp_coder.workflow_utils.base_branch import detect_base_branch

logger = logging.getLogger(__name__)

_OUTCOME_RE = re.compile(r"^\s*REBASE_OUTCOME:\s*(.+?)\s*$", re.MULTILINE)
_REASON_RE = re.compile(r"^\s*REBASE_REASON:\s*(.+?)\s*$", re.MULTILINE)

_VALID_OUTCOMES = {"success", "aborted"}


def _parse_outcome_marker(response_text: str) -> tuple[str | None, str | None]:
    """Extract ``(outcome, reason)`` from the LLM response.

    Last match wins for both markers.

    Returns:
        A ``(outcome, reason)`` tuple. ``outcome`` is ``"success"`` |
        ``"aborted"`` | ``None`` (unparseable or an unrecognized value).
        ``reason`` is the ``REBASE_REASON`` text, or ``None`` when absent or
        ``"n/a"``.
    """
    outcome: str | None = None
    outcome_matches = _OUTCOME_RE.findall(response_text)
    if outcome_matches:
        candidate = outcome_matches[-1].strip().lower()
        if candidate in _VALID_OUTCOMES:
            outcome = candidate

    reason: str | None = None
    reason_matches = _REASON_RE.findall(response_text)
    if reason_matches:
        candidate_reason = reason_matches[-1].strip()
        if candidate_reason and candidate_reason.lower() != "n/a":
            reason = candidate_reason

    return outcome, reason


def _evaluate_pre_push(
    *,
    mid_rebase: bool,
    marker_outcome: str | None,
    rebase_success_shape: bool,
) -> str:
    """Return ``"push"`` or ``"abort"`` (worst-case-wins, git is authoritative)."""
    if mid_rebase:
        return "abort"  # unfinished / crashed session
    if marker_outcome == "aborted":
        return "abort"  # trust the self-report
    if not rebase_success_shape:
        return "abort"  # git can't corroborate success
    return "push"  # marker success/unparseable AND git confirms


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


# --- Check baseline / comparison ---


class CheckRunError(Exception):
    """A check failed to RUN (infrastructure), as opposed to reporting failures."""


FailureKey = tuple[str, ...]
"""``("pytest", nodeid)`` | ``("pylint" | "mypy", file, code, message)``.

Line numbers never enter a key: a rebase shifts lines, and merely-moved
findings must not read as regressions (regression = verification − baseline).
"""

_PYTEST_NON_FAILING_OUTCOMES = ("passed", "skipped", "xfailed", "xpassed")


def _pytest_failure_keys(results: dict[str, Any]) -> set[FailureKey]:
    """Reduce a pytest result dict to a set of failure keys.

    Failing outcomes (``failed``/``error``/unrecognized) and failed collectors
    become keys. ``skipped``/``xfailed``/``xpassed`` tests and skipped
    collectors (module-level ``importorskip``) do not: a rebase can pull new
    self-skipping tests in from the base branch, and a skip the LLM cannot
    "fix" must not read as a regression.

    ``error_info`` is deliberately ignored — the library sets it for ANY
    non-zero pytest exit, including exit 1 (ordinary failures) and exit 2
    (collection errors, report still parsed). Genuine infrastructure failures
    take the crash path (``success=False``, no ``test_results``).

    Raises:
        CheckRunError: If pytest failed to run.
    """
    if results.get("success") is not True or results.get("test_results") is None:
        raise CheckRunError(
            f"failed to run: {results.get('error') or 'no test results produced'}"
        )
    report = results["test_results"]
    keys: set[FailureKey] = {
        ("pytest", test.nodeid)
        for test in report.tests or []
        if test.outcome not in _PYTEST_NON_FAILING_OUTCOMES
    }
    keys |= {
        ("pytest", collector.nodeid)
        for collector in report.collectors or []
        if collector.outcome == "failed"
    }
    return keys


def _pylint_failure_keys(result: PylintResult) -> set[FailureKey]:
    """Reduce a ``PylintResult`` to line-insensitive failure keys.

    Raises:
        CheckRunError: If pylint failed to run (``result.error`` set).
    """
    if result.error:
        raise CheckRunError(f"failed to run: {result.error}")
    return {("pylint", m.path, m.message_id, m.message) for m in result.messages}


def _mypy_failure_keys(result: MypyResult) -> set[FailureKey]:
    """Reduce a ``MypyResult`` to line-insensitive failure keys (errors only).

    Raises:
        CheckRunError: If mypy failed to run (``result.error`` set).
    """
    if result.error:
        raise CheckRunError(f"failed to run: {result.error}")
    return {
        ("mypy", m.file, m.code or "", m.message)
        for m in result.messages
        if m.severity == "error"
    }


def _run_all_checks(project_dir: Path) -> set[FailureKey]:
    """Run pytest, pylint and mypy and union their failure keys.

    Findings (failed tests, lint messages, type errors) become keys; a check
    that fails to *run* raises ``CheckRunError`` naming the checker.

    Raises:
        CheckRunError: If any check fails to run.
    """
    checkers: list[tuple[str, Callable[[], set[FailureKey]]]] = [
        ("pytest", lambda: _pytest_failure_keys(run_pytest_check(project_dir))),
        ("pylint", lambda: _pylint_failure_keys(run_pylint_check(project_dir))),
        ("mypy", lambda: _mypy_failure_keys(run_mypy_check(project_dir))),
    ]
    keys: set[FailureKey] = set()
    for name, run_checker in checkers:
        try:
            keys |= run_checker()
        except CheckRunError as exc:
            raise CheckRunError(f"{name}: {exc}") from exc
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise CheckRunError(f"{name}: {exc}") from exc
    return keys


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


# --- LLM session + orchestrator ------------------------------------------------

# Inactivity budget (max seconds with no stdout line from the LLM, NOT total
# runtime), matching the create_plan prompts and kept below the CI step cap.
_SESSION_TIMEOUT = 600

_REBASE_PROMPT_HEADER = "Automated Rebase"


def _run_rebase_session(
    project_dir: Path,
    base_branch: str,
    provider: str,
    mcp_config: str | None,
    settings_file: str | None,
    execution_dir: Path | None,
) -> str:
    """Run the single LLM rebase session.

    Loads the ``Automated Rebase`` prompt, appends the resolved base branch as
    context (so the LLM rebases onto ``origin/<base>``), and issues exactly one
    ``prompt_llm`` call with a ~600s inactivity budget. Any LLM error/timeout is
    left to propagate to the orchestrator, which maps it to a needs-human exit.

    Returns:
        The LLM response text (empty string when the response carries no text).
    """
    env_vars = prepare_llm_environment(project_dir)
    branch_name = get_branch_name_for_logging(project_dir)
    prompt_template = get_prompt(str(PROMPTS_FILE_PATH), _REBASE_PROMPT_HEADER)
    prompt = (
        f"{prompt_template}\n\n"
        "---\n"
        "## Rebase context\n"
        f"Rebase the current branch onto `origin/{base_branch}`.\n"
    )
    response = prompt_llm(
        prompt,
        provider=provider,
        session_id=None,
        timeout=_SESSION_TIMEOUT,
        env_vars=env_vars,
        execution_dir=str(execution_dir) if execution_dir else None,
        mcp_config=mcp_config,
        settings_file=settings_file,
        branch_name=branch_name,
    )
    return response.get("text", "") or ""


def run_rebase_workflow(
    project_dir: Path,
    provider: str,
    base_branch: str | None = None,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    execution_dir: Path | None = None,
) -> int:
    """Orchestrate the automated rebase.

    Composes the deterministic shell: pre-flight guards -> base-branch guard ->
    ``pr_info/``-on-base guard -> no-op short-circuit -> single LLM session ->
    worst-case-wins decision -> Python-owned force-push (with restore on
    rejection) -> ``finally`` abort safety net.

    See the exit-code contract in ``summary.md``.

    Returns:
        ``0`` (success or no-op), ``1`` (aborted -> needs-human), or ``2``
        (error / push rejected).
    """
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
        logger.info("Already current with origin/%s (%s); nothing to do", base, reason)
        return 0

    pre_sha = get_latest_commit_sha(project_dir)
    if pre_sha is None:
        logger.error("Could not resolve HEAD commit before rebase")
        return 2

    try:
        text = _run_rebase_session(
            project_dir, base, provider, mcp_config, settings_file, execution_dir
        )
        outcome, marker_reason = _parse_outcome_marker(text)
        decision = _evaluate_pre_push(
            mid_rebase=_is_rebase_in_progress(project_dir),
            marker_outcome=outcome,
            rebase_success_shape=_rebase_success_shape(project_dir, pre_sha),
        )
        if decision == "abort":
            logger.error("Rebase aborted (needs human): %s", marker_reason or reason)
            return 1

        result = git_push(project_dir, force_with_lease=True)
        if result["success"]:
            logger.info("Rebased and force-pushed onto origin/%s", base)
            return 0

        logger.error("Force-push rejected/failed: %s", result.get("error"))
        _reset_hard(project_dir, pre_sha)  # never leave unpushed rebased commits
        return 2
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # LLMTimeoutError is a subclass, so one branch covers timeout + errors.
        logger.error("Rebase session failed: %s", exc)
        return 1  # needs-human; the finally net makes this retry-safe
    finally:
        if _is_rebase_in_progress(project_dir):
            _abort_rebase(project_dir)
