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

### Step 1: Create Test Data and Add Unit Tests (TDD)
- [ ] Create test data file `tests/workflow_utils/test_data/multi_phase_tracker.md` (see [step_1.md](steps/step_1.md))
- [ ] Add `TestMultiPhaseTaskTracker` class to `tests/workflow_utils/test_task_tracker.py` (see [step_1.md](steps/step_1.md))
- [ ] Add test `test_find_implementation_section_includes_all_phases` (see [step_1.md](steps/step_1.md))
- [ ] Add test `test_get_incomplete_tasks_across_phases` (see [step_1.md](steps/step_1.md))
- [ ] Add test `test_get_step_progress_includes_all_phases` (see [step_1.md](steps/step_1.md))
- [ ] Add test `test_phase_headers_recognized_as_continuations` (see [step_1.md](steps/step_1.md))
- [ ] Add test `test_backward_compatibility_single_phase` (see [step_1.md](steps/step_1.md))
- [ ] Run new tests to verify they FAIL (TDD approach) (see [step_1.md](steps/step_1.md))
- [ ] Prepare git commit message for Step 1 (see [step_1.md](steps/step_1.md))

### Step 2: Update `_find_implementation_section()` to Handle Phase Headers
- [ ] Open `src/mcp_coder/workflow_utils/task_tracker.py` (see [step_2.md](steps/step_2.md))
- [ ] Locate the `_find_implementation_section()` function (see [step_2.md](steps/step_2.md))
- [ ] Update header parsing logic to recognize "phase" headers as continuations (see [step_2.md](steps/step_2.md))
- [ ] Run all tests to verify they PASS (see [step_2.md](steps/step_2.md))
- [ ] Prepare git commit message for Step 2 (see [step_2.md](steps/step_2.md))

### Step 3: Run Quality Checks and Verify Backward Compatibility
- [ ] Run pytest on `tests/workflow_utils/test_task_tracker.py` (see [step_3.md](steps/step_3.md))
- [ ] Run pytest on `tests/test_integration_task_tracker.py` (see [step_3.md](steps/step_3.md))
- [ ] Run pylint on modified files (see [step_3.md](steps/step_3.md))
- [ ] Run mypy on modified files (see [step_3.md](steps/step_3.md))
- [ ] Fix any issues found by quality checks (see [step_3.md](steps/step_3.md))
- [ ] Verify real-world examples from issue #156 work correctly (see [step_3.md](steps/step_3.md))
- [ ] Prepare git commit message for Step 3 (see [step_3.md](steps/step_3.md))

---

## Pull Request

- [ ] Review all implementation steps are complete (Steps 1-3)
- [ ] Run final code quality checks across entire codebase
- [ ] Verify all acceptance criteria from issue #156 are met
- [ ] Create pull request with summary of changes
- [ ] Link pull request to issue #156

---

## Progress Summary

**Total Steps:** 3  
**Estimated Time:** ~1 hour

| Step | Description | Status |
|------|-------------|--------|
| 1 | Create test data and unit tests (TDD) | 📋 Not started |
| 2 | Update `_find_implementation_section()` | 📋 Not started |
| 3 | Run quality checks and verify | 📋 Not started |
