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

### Step 1: Extract `_list_issues_no_error_handling()` from `list_issues()`
- [ ] Implementation: extract private method + delegation in `manager.py`, add 3 tests in `test_issue_manager_core.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Handle API failure in `get_all_cached_issues()` with snapshot restore
- [ ] Implementation: call `_list_issues_no_error_handling` in `_fetch_and_merge_issues`, add snapshot/try-except in `get_all_cached_issues()`, update `mock_cache_issue_manager` fixture, add 4 tests in `test_issue_cache.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Add `last_full_refresh` field and use it for full refresh threshold
- [ ] Implementation: add `last_full_refresh` to `CacheData`, update `_load_cache_file`, change `_fetch_and_merge_issues` return to `tuple[List[IssueData], bool]`, update `get_all_cached_issues()`, add 5 tests in `test_issue_cache.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
