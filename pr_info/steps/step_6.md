# Step 6: Final Verification

## Objective
Verify complete workflow implementation.

## Context
Reference `summary.md`. Final validation - unit tests only, no integration tests.

## WHERE
- Modify: `tests/workflows/test_define_labels.py`
- Optionally: Add usage notes to README

## WHAT

No new code - verification only.

## HOW
- Run full test suite
- Verify script can be imported
- Manual smoke test if desired

## ALGORITHM
```
Verification:
1. Run pytest tests/workflows/test_define_labels.py -v
2. All unit tests should pass (12+ tests)
3. Verify script imports without errors
4. Optional: Manual test with --dry-run flag
```

## DATA
- **Test markers**: `@pytest.mark.integration`
- **Environment**: Requires `GITHUB_TOKEN`
- **Verification**: Check label names, colors, descriptions match spec

## LLM Prompt
```
Reference: pr_info/steps/summary.md, pr_info/steps/step_1-5.md, pr_info/steps/decisions.md

Step 6: Final verification (no integration tests).

Tasks:
1. Run all unit tests: pytest tests/workflows/test_define_labels.py -v
2. Verify 12+ tests pass (9 for calculate_label_changes, 3 for apply_labels, 4+ for CLI)
3. Test script imports: python -c "from workflows.define_labels import main"
4. Manual smoke test (optional): python workflows/define_labels.py --dry-run --log-level DEBUG
5. Verify batch file works: workflows\define_labels.bat --help

No integration tests required - comprehensive unit test coverage is sufficient.
```
