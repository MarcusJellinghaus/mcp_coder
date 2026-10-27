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

### Step 1: Move `TestCommandTemplates` → `test_command_templates.py`
See [step_1.md](./steps/step_1.md)

- [x] Implementation: precondition + baseline counts, dry-run then move class, fix imports in both files, verify collect counts (test_core.py 49, test_command_templates.py 32)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Move `TestGetCacheRefreshMinutes` → `tests/utils/test_user_config_cache_refresh.py`
See [step_2.md](./steps/step_2.md)

- [x] Implementation: dry-run then move class to new file, set destination imports, drop unused import + stale docstring bullet in test_core.py, verify collect counts (test_core.py 45, new file 4)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Move cache classes → `tests/test_mcp_workspace_github_cache.py`
See [step_3.md](./steps/step_3.md)

- [x] Implementation: dry-run then move `TestCacheFilePath`, `TestCacheFileOperations`, `TestStalenessLogging` in one call, verify method-local `RepoIdentifier` imports, set destination imports, drop unused imports + 2 stale bullets in test_core.py, verify collect counts (test_core.py 37, new file 8)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Move eligibility classes → `test_core_eligibility.py`
See [step_4.md](./steps/step_4.md)

- [x] Implementation: dry-run then move `TestGetEligibleIssues`, `TestGetCachedEligibleIssues` in one call, verify class-level fixtures, set destination imports, drop unused imports + 2 stale bullets in test_core.py, remove stale allowlist entry if flagged, verify collect counts (test_core.py 32, new file 5)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: Move dispatch classes → `test_core_dispatch.py`; final verification
See [step_5.md](./steps/step_5.md)

- [x] Implementation: dry-run then move `TestDispatchWorkflow`, `TestDispatchWorkflowSilentFallthroughGuard` in one call, verify parametrize decorators, set destination imports, reduce test_core.py to final state, ensure allowlist entry removed, verify all final collect counts
- [x] Quality checks: pylint, pytest, mypy (plus ruff, lint-imports, tach, vulture, file size, compact diff review) — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review full diff against base branch — only moved blocks, import changes, new-file headers, deleted docstring bullets, allowlist line
- [ ] PR summary prepared
