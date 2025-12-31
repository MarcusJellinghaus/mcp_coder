# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**

1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**

- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Extend `list_issues()` with `since` Parameter
- [x] Implement extended `list_issues()` method with optional `since` parameter in `src/mcp_coder/utils/github_operations/issue_manager.py`
- [x] Add comprehensive tests in `tests/utils/github_operations/test_issue_manager.py`
- [x] Run pylint check and fix all issues found
- [x] Run pytest and fix all failing tests
- [x] Run mypy and fix all type issues
- [x] Prepare git commit message for Step 1 implementation

### Step 2: Implement Core Cache Logic
- [x] Implement `get_cached_eligible_issues()` function in `src/mcp_coder/cli/commands/coordinator.py`
- [x] Implement helper functions: `_load_cache_file`, `_save_cache_file`, `_get_cache_file_path`, `_log_stale_cache_entries`
- [x] Create comprehensive tests in `tests/utils/test_coordinator_cache.py` (new file)
- [x] Run pylint check and fix all issues found
- [x] Run pytest and fix all failing tests
- [x] Run mypy and fix all type issues
- [x] Prepare git commit message for Step 2 implementation

### Step 3: Configuration, CLI Flag, and Integration
- [ ] Add `--force-refresh` CLI flag to coordinator run command
- [ ] Implement `get_cache_refresh_minutes()` configuration reading function
- [ ] Integrate `get_cached_eligible_issues()` into `execute_coordinator_run()` workflow
- [ ] Add integration tests to existing `tests/cli/commands/test_coordinator.py`
- [ ] Run pylint check and fix all issues found
- [ ] Run pytest and fix all failing tests
- [ ] Run mypy and fix all type issues
- [ ] Prepare git commit message for Step 3 implementation

### Pull Request
- [ ] Review all implementation steps are complete
- [ ] Run full test suite and ensure all tests pass
- [ ] Run final code quality checks (pylint, mypy, pytest)
- [ ] Prepare comprehensive PR summary and description
