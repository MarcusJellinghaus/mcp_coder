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

### Step 1: Rename _update_issue_labels_in_cache to public function
See [step_1.md](./steps/step_1.md)

- [ ] Rename `_update_issue_labels_in_cache` to `update_issue_labels_in_cache` in `issue_cache.py`
- [ ] Run pylint on `src/mcp_coder/utils/github_operations/issue_cache.py`
- [ ] Run pytest on `tests/utils/github_operations/test_issue_cache.py`
- [ ] Run mypy on `src/mcp_coder/utils/github_operations/`
- [ ] Prepare commit message for Step 1

### Step 2: Refactor core.py - Remove _get_coordinator() and use direct imports
See [step_2.md](./steps/step_2.md)

- [ ] Delete `_get_coordinator()` function from `core.py`
- [ ] Delete `from types import ModuleType` import
- [ ] Add direct imports for `get_config_values` and `load_labels_config`
- [ ] Remove `_update_issue_labels_in_cache` from `issue_cache` import (unused in core.py)
- [ ] Replace all `coordinator.get_config_values` calls with direct `get_config_values` calls
- [ ] Replace all `coordinator.load_labels_config` calls with direct `load_labels_config` calls
- [ ] Run pylint on `src/mcp_coder/cli/commands/coordinator/core.py`
- [ ] Run pytest on `tests/cli/commands/coordinator/test_core.py`
- [ ] Run mypy on `src/mcp_coder/cli/commands/coordinator/`
- [ ] Prepare commit message for Step 2

### Step 3: Refactor commands.py - Remove _get_coordinator usage and use direct imports
See [step_3.md](./steps/step_3.md)

- [ ] Remove `_get_coordinator` from `.core` import
- [ ] Add direct imports for all functions used via coordinator pattern
- [ ] Replace all `coordinator = _get_coordinator()` patterns with direct calls
- [ ] Replace `coordinator._update_issue_labels_in_cache` with `update_issue_labels_in_cache`
- [ ] Run pylint on `src/mcp_coder/cli/commands/coordinator/commands.py`
- [ ] Run pytest on `tests/cli/commands/coordinator/test_commands.py`
- [ ] Run mypy on `src/mcp_coder/cli/commands/coordinator/`
- [ ] Prepare commit message for Step 3

### Step 4: Update coordinator __init__.py - Remove test-only re-exports
See [step_4.md](./steps/step_4.md)

- [ ] Remove test-only re-export imports (IssueBranchManager, IssueManager, JenkinsClient, etc.)
- [ ] Remove `_update_issue_labels_in_cache` and `CacheData` exports
- [ ] Update `__all__` list to only include public API
- [ ] Run pylint on `src/mcp_coder/cli/commands/coordinator/__init__.py`
- [ ] Run pytest on `tests/cli/commands/coordinator/`
- [ ] Run mypy on `src/mcp_coder/cli/commands/coordinator/`
- [ ] Prepare commit message for Step 4

### Step 5: Update test_core.py - Fix patch locations
See [step_5.md](./steps/step_5.md)

- [ ] Update patch locations from `...coordinator.<name>` to `...coordinator.core.<name>`
- [ ] Run pylint on `tests/cli/commands/coordinator/test_core.py`
- [ ] Run pytest on `tests/cli/commands/coordinator/test_core.py`
- [ ] Run mypy on `tests/cli/commands/coordinator/`
- [ ] Prepare commit message for Step 5

### Step 6: Update test_commands.py - Fix patch locations
See [step_6.md](./steps/step_6.md)

- [ ] Update patch locations from `...coordinator.<name>` to `...coordinator.commands.<name>`
- [ ] Update `_update_issue_labels_in_cache` patches to `update_issue_labels_in_cache` (renamed)
- [ ] Run pylint on `tests/cli/commands/coordinator/test_commands.py`
- [ ] Run pytest on `tests/cli/commands/coordinator/test_commands.py`
- [ ] Run mypy on `tests/cli/commands/coordinator/`
- [ ] Prepare commit message for Step 6

### Step 7: Run all checks and verify
See [step_7.md](./steps/step_7.md)

- [ ] Run full pylint check on coordinator package
- [ ] Run full mypy check on coordinator package
- [ ] Run full pytest on coordinator tests
- [ ] Run full test suite for regression check
- [ ] Verify all acceptance criteria from summary.md are met
- [ ] Prepare final commit message for Step 7

---

## Pull Request

- [ ] Review all changes across modified files
- [ ] Verify no regressions in existing functionality
- [ ] Create PR summary with overview of changes
- [ ] Link to Issue #365 in PR description
