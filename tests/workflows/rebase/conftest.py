"""Shared git fixtures/helpers for the rebase workflow tests.

Kept local to ``tests.workflows.rebase`` so the tests satisfy the Test Module
Independence contract (no imports from ``tests.utils``). ``git_repo_with_files``
and ``patched`` are injected via pytest conftest discovery; ``setup_git_config``
and the orchestrator shim-result constants/helpers are imported directly.
"""

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from git import Repo

from mcp_coder.workflow_steps import rebase as rebase_step_module
from mcp_coder.workflows import rebase as rebase_module
from mcp_coder.workflows.rebase import (
    _check_pr_info_absent_on_base,
    _preflight,
    _rebase_success_shape,
    run_rebase_workflow,
)
from mcp_coder.workflows.rebase_checks import FailureKey


def setup_git_config(repo: Repo) -> None:
    """Configure git user for a repository (required for commits)."""
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")


@pytest.fixture
def git_repo_with_files(tmp_path: Path) -> tuple[Repo, Path]:
    """Create a git repository with sample committed files.

    Returns:
        The ``Repo`` object and the project directory path.
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    repo = Repo.init(project_dir)
    setup_git_config(repo)

    sample_files = {
        "README.md": "# Test Project\n\nSample project for testing.",
        "main.py": "def main():\n    print('Hello, World!')",
        "config.yml": "debug: false\nport: 8080",
    }
    for name, content in sample_files.items():
        (project_dir / name).write_text(content)

    repo.index.add(list(sample_files.keys()))
    repo.index.commit("Initial commit with sample files")

    return repo, project_dir


# --- run_rebase_workflow orchestrator scaffolding (test_workflow*.py) ---

_REAL_PREFLIGHT = _preflight
_REAL_PR_INFO_GUARD = _check_pr_info_absent_on_base
_REAL_SUCCESS_SHAPE = _rebase_success_shape

_COMPLETED: dict[str, Any] = {
    "success": True,
    "error": None,
    "returncode": 0,
    "stderr": "",
    "status": "completed",
}
_STOPPED: dict[str, Any] = {
    **_COMPLETED,
    "success": False,
    "returncode": 1,
    "stderr": "CONFLICT",
    "status": "stopped_on_conflict",
}
_REBASE_ERROR: dict[str, Any] = {
    **_COMPLETED,
    "success": False,
    "error": "git rebase origin/main failed (exit 128)",
    "returncode": 128,
    "stderr": "boom",
    "status": "error",
}


def _blob_info(*paths: str, binary: tuple[str, ...] = ()) -> dict[str, Any]:
    """Build a successful ``get_conflict_blob_info`` result for ``paths``."""
    return {
        "success": True,
        "error": None,
        "returncode": 0,
        "stderr": "",
        "entries": [
            {"path": p, "stages": [1, 2, 3], "is_binary": p in binary} for p in paths
        ],
    }


_GIT_OK: dict[str, Any] = {
    "success": True,
    "error": None,
    "returncode": 0,
    "stderr": "",
}
_GIT_FAIL: dict[str, Any] = {
    "success": False,
    "error": "git reset --hard failed (exit 128)",
    "returncode": 128,
    "stderr": "fatal: bad revision",
}
_CLEAN_STATUS: dict[str, Any] = {
    "success": True,
    "error": None,
    "returncode": 0,
    "stderr": "",
    "clean": True,
    "staged": [],
    "modified": [],
    "untracked": [],
}
_FAILED_STATUS = {**_CLEAN_STATUS, "success": False, "clean": False}

_REGRESSION: set[FailureKey] = {("pytest", "tests/test_new.py::test_case")}


@pytest.fixture
def patched(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Patch every collaborator to a benign happy-path default.

    Returns a namespace of the recordable mocks so individual tests can tweak
    return values / side effects and assert call arguments.
    """
    # Guards — all pass by default.
    monkeypatch.setattr(rebase_module, "_preflight", lambda _pd: None)
    monkeypatch.setattr(
        rebase_module, "_resolve_base_branch", lambda _pd, _arg: ("main", None)
    )
    monkeypatch.setattr(
        rebase_module, "check_base_branch_on_origin", lambda _pd, _b: None
    )
    monkeypatch.setattr(
        rebase_module, "_check_pr_info_absent_on_base", lambda _pd, _b: None
    )

    fetch = MagicMock(return_value=True)
    needs = MagicMock(return_value=(True, "1 commit behind"))
    latest_sha = MagicMock(return_value="presha")
    monkeypatch.setattr(rebase_module, "fetch_remote", fetch)
    monkeypatch.setattr(rebase_module, "needs_rebase", needs)
    monkeypatch.setattr(rebase_module, "get_latest_commit_sha", latest_sha)

    # LLM session infrastructure — kept offline.
    monkeypatch.setattr(rebase_module, "prepare_llm_environment", lambda _pd: {})
    monkeypatch.setattr(
        rebase_module, "get_branch_name_for_logging", lambda _pd: "feature"
    )
    prompt = MagicMock(return_value=("resolved", "sid-1"))
    monkeypatch.setattr(rebase_module, "_prompt_in_session", prompt)
    monkeypatch.setattr(
        rebase_module,
        "_build_conflict_prompt",
        lambda _pd, files: "CONFLICT:" + ",".join(files),
    )
    monkeypatch.setattr(
        rebase_module, "_build_regression_fix_prompt", lambda text: "FIX:" + text
    )

    # Checks + formatter.
    all_checks = MagicMock(return_value=set())
    formatters = MagicMock(return_value=True)
    monkeypatch.setattr(rebase_module, "_run_all_checks", all_checks)
    monkeypatch.setattr(rebase_module, "run_formatters", formatters)

    # Rebase / conflict-loop shim calls.
    rebase_start = MagicMock(return_value=_COMPLETED)
    rebase_continue = MagicMock(return_value=_COMPLETED)
    rebase_skip = MagicMock(return_value=_COMPLETED)
    blob_info = MagicMock(return_value=_blob_info())
    has_staged = MagicMock(return_value=False)
    stage_all = MagicMock(return_value=True)
    commit_all = MagicMock(
        return_value={"success": True, "commit_hash": "abc1234", "error": None}
    )
    resolve_theirs = MagicMock(return_value=_GIT_OK)
    read_stage = MagicMock(
        return_value={**_GIT_OK, "content": "text\n", "is_binary": False}
    )
    monkeypatch.setattr(rebase_module, "rebase_start", rebase_start)
    monkeypatch.setattr(rebase_module, "rebase_continue", rebase_continue)
    monkeypatch.setattr(rebase_module, "rebase_skip", rebase_skip)
    monkeypatch.setattr(rebase_module, "get_conflict_blob_info", blob_info)
    monkeypatch.setattr(rebase_module, "has_staged_changes", has_staged)
    monkeypatch.setattr(rebase_module, "stage_all_changes", stage_all)
    monkeypatch.setattr(rebase_module, "commit_all_changes", commit_all)
    monkeypatch.setattr(rebase_module, "resolve_take_theirs_or_remove", resolve_theirs)
    monkeypatch.setattr(rebase_module, "read_conflict_stage", read_stage)

    # Marker scan + git-state shim calls used by the safety net.
    has_markers = MagicMock(return_value=False)
    mid_rebase = MagicMock(return_value=False)
    success_shape = MagicMock(return_value=True)
    abort = MagicMock(return_value=_GIT_OK)
    reset = MagicMock(return_value=_GIT_OK)
    status = MagicMock(return_value=_CLEAN_STATUS)
    push = MagicMock(return_value={"success": True, "error": None})
    monkeypatch.setattr(rebase_module, "_has_conflict_markers", has_markers)
    monkeypatch.setattr(rebase_module, "is_rebase_in_progress", mid_rebase)
    monkeypatch.setattr(rebase_module, "_rebase_success_shape", success_shape)
    monkeypatch.setattr(rebase_module, "rebase_abort", abort)
    monkeypatch.setattr(rebase_step_module, "reset_hard", reset)
    monkeypatch.setattr(rebase_module, "get_working_tree_status", status)
    monkeypatch.setattr(rebase_module, "git_push", push)

    return SimpleNamespace(
        prompt=prompt,
        all_checks=all_checks,
        formatters=formatters,
        rebase_start=rebase_start,
        rebase_continue=rebase_continue,
        rebase_skip=rebase_skip,
        blob_info=blob_info,
        has_staged=has_staged,
        stage_all=stage_all,
        commit_all=commit_all,
        resolve_theirs=resolve_theirs,
        read_stage=read_stage,
        has_markers=has_markers,
        mid_rebase=mid_rebase,
        success_shape=success_shape,
        abort=abort,
        reset=reset,
        status=status,
        push=push,
        needs=needs,
        fetch=fetch,
    )


def _run(tmp_path: Path, base_branch: str | None = None) -> int:
    return run_rebase_workflow(tmp_path, provider="claude", base_branch=base_branch)


def _start_conflict_loop(patched_ns: SimpleNamespace) -> None:
    """Make the initial rebase stop with a conflict (mid-rebase)."""
    patched_ns.rebase_start.return_value = _STOPPED
    patched_ns.mid_rebase.return_value = True
