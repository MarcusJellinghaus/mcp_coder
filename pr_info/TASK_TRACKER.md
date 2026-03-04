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

### Step 1: Add --committed-only Flag to Parser
_See [step_1.md](./steps/step_1.md) for full details._

- [x] Add `--committed-only` argument to `compact_diff_parser` in `src/mcp_coder/cli/parsers.py` (`add_git_tool_parsers()`)
- [x] Add test class `TestCompactDiffCommittedOnlyFlag` with 3 test cases to `tests/cli/commands/test_git_tool.py`
- [x] Run pylint, pytest, mypy — fix all issues found
- [x] Prepare git commit message for Step 1

---

### Step 2: Write Tests for Uncommitted Changes Display (TDD)
_See [step_2.md](./steps/step_2.md) for full details._

- [x] Add test class `TestCompactDiffUncommittedChanges` with 6 failing test cases to `tests/cli/commands/test_git_tool.py`
- [x] Run pylint and mypy on test file — fix all issues found (tests are expected to fail at this stage)
- [x] Prepare git commit message for Step 2

---

### Step 3: Implement Uncommitted Changes Display Logic
_See [step_3.md](./steps/step_3.md) for full details._

- [x] Add import `from ...utils.git_operations.diffs import get_git_diff_for_commit` to `src/mcp_coder/cli/commands/git_tool.py`
- [x] Modify `execute_compact_diff()` to append uncommitted changes when `--committed-only` is not set
- [x] Update all existing `argparse.Namespace` calls in `test_git_tool.py` that test `execute_compact_diff` to include `committed_only=False` (prevents `AttributeError`)
- [x] Run pylint, pytest, mypy — fix all issues found; all Step 2 tests should now pass
- [x] Prepare git commit message for Step 3

---

### Step 4: Write Tests for Exclude Patterns on Uncommitted Changes (TDD)
_See [step_4.md](./steps/step_4.md) for full details._

- [ ] Add 4 new test methods to `TestCompactDiffUncommittedChanges` for exclude pattern filtering
- [ ] Add 1 helper function test `test_apply_exclude_patterns_to_uncommitted_diff_helper`
- [ ] Run pylint and mypy on test file — fix all issues found (tests are expected to fail at this stage)
- [ ] Prepare git commit message for Step 4

---

### Step 5: Implement Exclude Pattern Filtering for Uncommitted Changes
_See [step_5.md](./steps/step_5.md) for full details._

- [ ] Add `import fnmatch` to top-of-file imports in `src/mcp_coder/cli/commands/git_tool.py`
- [ ] Add helper function `_apply_exclude_patterns_to_uncommitted_diff()` before `execute_compact_diff()`
- [ ] Integrate helper into `execute_compact_diff()` to apply exclude patterns to uncommitted diff
- [ ] Run pylint, pytest, mypy — fix all issues found; all Step 4 tests should now pass
- [ ] Prepare git commit message for Step 5

---

### Step 6: Update Documentation
_See [step_6.md](./steps/step_6.md) for full details._

- [ ] Update `docs/cli-reference.md` section `### git-tool compact-diff`: add `--committed-only` to Options list
- [ ] Update description to explain uncommitted changes are shown by default; add Output Structure and Notes subsections
- [ ] Update Examples section with new use cases showing `--committed-only` and exclude pattern combinations
- [ ] Run pylint, pytest, mypy — fix all issues found
- [ ] Prepare git commit message for Step 6

---

## Pull Request

- [ ] Review full diff for correctness and completeness (all 6 steps implemented, no regressions)
- [ ] Verify PR summary covers: new `--committed-only` flag, uncommitted changes shown by default, exclude pattern filtering, documentation update, and link to issue #477
- [ ] Confirm all tests pass and quality checks (pylint, pytest, mypy) are clean before submitting PR
