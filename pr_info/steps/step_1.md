# Step 1: Test fixture cleanup — decouple from real tool names

## Context
See `pr_info/steps/summary.md` for full issue context.

Test data in `test_ci_log_parser.py` uses real tool names (`vulture_check.sh`) in CI log fixtures. Replace with realistic-but-fictional names to decouple tests from actual tool names while preserving log format fidelity.

## TDD Note
This step modifies existing test data — the tests themselves verify CI log parsing, not tool names. After renaming, all existing tests must still pass with identical assertions (adjusted for new names).

## WHERE
- `tests/checks/test_ci_log_parser.py`
- `tests/checks/test_branch_status.py`

## WHAT
No new functions. Modify two test data constants:
- `VULTURE_LOG` — replace `vulture` references with fictional tool name
- `FILE_SIZE_LOG` — this one uses `mcp-coder check file-size` which is NOT in scope for replacement (it's not one of the three tools being replaced). **Leave FILE_SIZE_LOG unchanged.**

Update the test method that asserts against the renamed content:
- `test_captures_output_between_endgroup_and_error` — update assertions for new tool name
- `test_vulture_real_log_structure` — update step name argument and assertions

## HOW

### Replacements in VULTURE_LOG constant
| Old | New |
|-----|-----|
| `Run vulture --version && ./tools/vulture_check.sh` | `Run tool-alpha --version && ./tools/tool_alpha.sh` |
| `vulture --version && ./tools/vulture_check.sh` | `tool-alpha --version && ./tools/tool_alpha.sh` |
| `vulture 2.15` | `tool-alpha 2.15` |
| `Checking for dead code...` | `Checking for dead code...` (keep — generic message) |
| `unused function '_mcp_fail' (60% confidence)` | `unused function '_mcp_fail' (60% confidence)` (keep — generic output) |

### Replacements in test assertions
| Method | Old assertion | New assertion |
|--------|--------------|---------------|
| `test_captures_output_between_endgroup_and_error` | `label.startswith("Run vulture")` | `label.startswith("Run tool-alpha")` |
| `test_captures_output_between_endgroup_and_error` | `"vulture 2.15" in lines` | `"tool-alpha 2.15" in lines` |
| `test_vulture_real_log_structure` | step name `"Run vulture --version && ./tools/vulture_check.sh"` | `"Run tool-alpha --version && ./tools/tool_alpha.sh"` |
| `test_vulture_real_log_structure` | `"vulture 2.15" in result` | `"tool-alpha 2.15" in result` |
| `test_error_fallback_with_outside_output` | `"vulture 2.15" in result` | `"tool-alpha 2.15" in result` |

### Replacements in test_branch_status.py

The `TestExtractFailedStepLog` class uses `vulture` / `vulture_check.sh` in test log strings and assertions.

| Location | Old | New |
|----------|-----|-----|
| `test_prefix_match` log string | `Run vulture --version && ./tools/vulture_check.sh` | `Run tool-alpha --version && ./tools/tool_alpha.sh` |
| `test_prefix_match` log string | `vulture output here` | `tool-alpha output here` |
| `test_prefix_match` call | `_extract_failed_step_log(log, "Run vulture")` | `_extract_failed_step_log(log, "Run tool-alpha")` |
| `test_prefix_match` assertion | `"vulture output here" in result` | `"tool-alpha output here" in result` |
| `test_contains_match` log string | `Step 3: Run vulture check` | `Step 3: Run tool-alpha check` |
| `test_contains_match` log string | `vulture found issues` | `tool-alpha found issues` |
| `test_contains_match` call | `_extract_failed_step_log(log, "vulture check")` | `_extract_failed_step_log(log, "tool-alpha check")` |
| `test_contains_match` assertion | `"vulture found issues" in result` | `"tool-alpha found issues" in result` |

### Update docstring
Remove reference to specific CI run number if desired, or keep for traceability. The module docstring mentions "CI run 23438818570" — this is fine to keep as historical context.

## ALGORITHM
```
1. In VULTURE_LOG, replace "vulture" tool references with "tool-alpha" equivalents
2. Update test assertions that match against VULTURE_LOG content
3. Leave FILE_SIZE_LOG and its tests unchanged
4. In test_branch_status.py, replace vulture/vulture_check.sh references with tool-alpha/tool_alpha.sh in TestExtractFailedStepLog
5. Run pytest on both files to verify all tests pass
6. Run pylint, mypy checks
```

## DATA
No data structure changes. Constants remain strings. Test assertions remain boolean checks.

## Verification
```
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-k", "test_ci_log_parser or test_branch_status"])
mcp__tools-py__run_pylint_check()
mcp__tools-py__run_mypy_check()
```

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for full context.

Implement step 1: Replace real tool names with fictional names in test_ci_log_parser.py.

1. Read tests/checks/test_ci_log_parser.py
2. In VULTURE_LOG constant: replace vulture/vulture_check.sh references with tool-alpha/tool_alpha.sh
3. Update test assertions that match against the renamed content
4. Leave FILE_SIZE_LOG and its tests unchanged
5. Read tests/checks/test_branch_status.py
6. In TestExtractFailedStepLog: replace vulture/vulture_check.sh references with tool-alpha/tool_alpha.sh
7. Run all three quality checks (pytest, pylint, mypy)
8. Commit: "test: decouple test fixtures from real tool names (#672)"
```
