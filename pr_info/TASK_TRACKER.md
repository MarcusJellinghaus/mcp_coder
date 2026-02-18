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

### Step 1: Add `all_cached_issues` Optional Parameter to `process_eligible_issues` + Unit Test

See [step_1.md](./steps/step_1.md) for full details.

- [ ] Read `tests/workflows/vscodeclaude/test_orchestrator_launch.py` and `src/mcp_coder/workflows/vscodeclaude/session_launch.py` in full before making changes
- [ ] Add test class `TestProcessEligibleIssuesPrefetchedIssues` with test `test_pre_fetched_issues_bypasses_get_all_cached_issues` to `test_orchestrator_launch.py`
- [ ] Add `all_cached_issues: list[IssueData] | None = None` optional parameter to `process_eligible_issues` in `session_launch.py`
- [ ] Replace unconditional `get_all_cached_issues` call with conditional guard (only call when `all_cached_issues is None`)
- [ ] Run pylint, fix all issues found
- [ ] Run pytest, confirm new test passes and no existing tests are broken
- [ ] Run mypy, fix all issues found
- [ ] Prepare git commit message for Step 1

### Step 2: Pass Pre-Fetched Issues from Caller in `execute_coordinator_vscodeclaude`

See [step_2.md](./steps/step_2.md) for full details.

- [ ] Read `src/mcp_coder/cli/commands/coordinator/commands.py` in full before making changes
- [ ] Derive `repo_full_name` and `all_cached_issues` from `cached_issues_by_repo` in the per-repo loop
- [ ] Add error log when `repo_full_name` is empty or not in `cached_issues_by_repo`
- [ ] Pass `all_cached_issues=all_cached_issues` as keyword argument to `process_eligible_issues`
- [ ] Run pylint, fix all issues found
- [ ] Run pytest, confirm no tests are broken
- [ ] Run mypy, fix all issues found
- [ ] Prepare git commit message for Step 2

---

## Pull Request

- [ ] Review all changes against [summary.md](./steps/summary.md) and [Decisions.md](./steps/Decisions.md)
- [ ] Confirm `get_all_cached_issues` is called only once per `--cleanup` run (not twice)
- [ ] Confirm backward compatibility: existing callers with no `all_cached_issues` argument still work
- [ ] Write PR title and summary describing the fix for issue #468
