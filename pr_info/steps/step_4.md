# Step 4: Evaluate and Remove Redundant Tests

## Summary Reference
See [summary.md](summary.md) for overall context.
See [Decisions.md](Decisions.md) - Decision 9 for rationale.

## Objective
Review the 5 tests in `TestMultiPhaseTaskTracker` and remove any that are redundant, now that all tests pass.

---

## WHERE: File Path

| Action | File Path |
|--------|-----------|
| Modify | `tests/workflow_utils/test_task_tracker.py` |

---

## WHAT: Tests to Evaluate

| Test | Potential Redundancy |
|------|---------------------|
| `test_find_implementation_section_includes_all_phases` | Core test - **KEEP** |
| `test_get_incomplete_tasks_across_phases` | Core test - **KEEP** |
| `test_get_step_progress_includes_all_phases` | Core test - **KEEP** |
| `test_phase_headers_recognized_as_continuations` | May duplicate test 1 |
| `test_backward_compatibility_single_phase` | May be covered by existing 56+ tests |

---

## HOW: Evaluation Criteria

For each candidate test, ask:
1. Does another test already verify the same behavior?
2. Would removing this test reduce confidence in the implementation?
3. Does this test catch edge cases that others miss?

---

## Verification

After removing any tests:
```bash
pytest tests/workflow_utils/test_task_tracker.py -v
```

All remaining tests must pass.

---

## LLM Prompt for Step 4

```
You are implementing Step 4 of issue #156: Evaluate and Remove Redundant Tests.

CONTEXT:
- See pr_info/steps/step_4.md for this step's details
- All 5 tests in TestMultiPhaseTaskTracker are now passing

TASK:
1. Review the 5 tests for redundancy
2. Remove tests that duplicate coverage from other tests
3. Run pytest to verify remaining tests still pass

CANDIDATES FOR REMOVAL:
- test_phase_headers_recognized_as_continuations (may duplicate test 1)
- test_backward_compatibility_single_phase (may be covered by existing tests)

REQUIREMENTS:
- Only remove tests if clearly redundant
- Keep tests if they provide unique value
- Run quality checks after changes
```
