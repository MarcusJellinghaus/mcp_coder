# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

### Step 1: Create `session_launch.py`

- [x] Implement: Create `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — copy `launch_vscode`, `prepare_and_launch_session`, `process_eligible_issues`, `regenerate_session_files` verbatim from `orchestrator.py` with trimmed imports and `__all__` (see [step_1.md](./steps/step_1.md))
- [x] Quality checks: run pylint (error/fatal), mypy — fix any import errors found, no logic changes
- [x] Git commit message: `refactor: extract session launch functions into session_launch.py`

### Step 2: Move `_get_configured_repos` to `config.py`, Update `cleanup.py`

- [x] Implement: Add `load_config` and `from .helpers import get_repo_full_name` to `config.py`, paste `_get_configured_repos` verbatim at end of `config.py`, update `cleanup.py` import from `.orchestrator` → `.config` (see [step_2.md](./steps/step_2.md))
- [x] Quality checks: run pylint (error/fatal), mypy, pytest (excluding integration markers) — fix any import errors, no logic changes
- [x] Git commit message: `refactor: move _get_configured_repos to config.py, update cleanup.py import`

### Step 3: Create `session_restart.py`

- [x] Implement: Create `src/mcp_coder/workflows/vscodeclaude/session_restart.py` — copy `BranchPrepResult`, `_prepare_restart_branch`, `_build_cached_issues_by_repo`, `restart_closed_sessions`, `handle_pr_created_issues` verbatim from `orchestrator.py`; import `_get_configured_repos` from `.config`, import `launch_vscode`/`regenerate_session_files` from `.session_launch`; `__all__` contains only the two public functions (see [step_3.md](./steps/step_3.md))
- [x] Quality checks: run pylint (error/fatal), mypy, pytest (excluding integration markers) — fix any import errors, no logic changes
- [x] Git commit message: `refactor: extract session restart functions into session_restart.py`

### Step 4: Update `__init__.py` — Docstring + Re-exports

- [ ] Implement: Replace short `__init__.py` docstring with full ~310-line docstring from `orchestrator.py`; replace `from .orchestrator import (...)` block with imports from `.session_launch`, `.session_restart`, and `.helpers`; add `regenerate_session_files` to `__all__` (see [step_4.md](./steps/step_4.md))
- [ ] Quality checks: run pylint (error/fatal), mypy, pytest (excluding integration markers) — fix any import errors, no logic changes
- [ ] Git commit message: `refactor: update __init__.py re-exports and add package docstring`

### Step 5: Delete `orchestrator.py` and Update `.large-files-allowlist`

- [ ] Implement: Verify no remaining `orchestrator` imports in `src/`; delete `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`; remove its entry from `.large-files-allowlist` (see [step_5.md](./steps/step_5.md))
- [ ] Quality checks: run `tools\lint_imports.bat`, `tools\tach_check.bat`, pytest — note that `test_orchestrator_*.py` failures are expected and accepted (test restructuring is a separate follow-up issue)
- [ ] Git commit message: `refactor: delete orchestrator.py, remove from large-files-allowlist`

---

## Pull Request

- [ ] Review all changes for correctness — verify functions moved verbatim, imports are accurate, no logic changes introduced
- [ ] Confirm `__init__.py` public API is consistent (`__all__` updated, `regenerate_session_files` omission fixed)
- [ ] Confirm `.large-files-allowlist` entry for `orchestrator.py` is removed
- [ ] Confirm `test_orchestrator_*.py` failures are documented as expected (follow-up issue scope)
- [ ] Write PR summary describing the split: `orchestrator.py` → `session_launch.py` + `session_restart.py` + updates to `config.py`, `cleanup.py`, `__init__.py`
