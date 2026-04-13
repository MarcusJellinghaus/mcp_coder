# Plan Review Log — Run 1

**Issue:** #785 — config: harden type parsing with centralized schema and config validation
**Date:** 2026-04-13
**Reviewer:** Supervisor agent

## Round 1 — 2026-04-13

**Findings**:
- **Critical**: Steps 2+3 are intertwined — Step 2 changes return types but Step 3 updates callers. Between commits, `True == "True"` evaluates to `False` (silent runtime bug).
- **Critical**: Step 2 deletes `_get_standard_env_var` but `_get_source_annotation` still calls it until Step 5. Breaks pylint/mypy between Steps 2-4.
- **Critical**: Step 2's `get_cache_refresh_minutes` test for `"not_a_number"` — schema validation raises ValueError before function runs. Plan says "update that test case" but doesn't specify fix.
- **Accept**: `tests/config/test_mlflow_config.py` missing from Step 3 (has 9 tests with string mocks for mlflow.enabled).
- **Accept**: Langchain env var override test needs concrete guidance (not vague "mock directly").
- **Accept**: "~15 test files" claim is actually ~11.
- **Accept**: Step 5 verify tests use `by_label` dict pattern that assumes one entry per label — breaks with per-field entries.
- **Skip**: Line numbers off by 1-2 in places (close enough).
- **Skip**: "No new files created" claim confirmed correct.

**Decisions**:
- Merge Steps 2+3 into single Step 2 (planning principle: merge intertwined steps) — **accepted**
- Keep `_get_standard_env_var` alive until verify rewrite step deletes it — **accepted**
- Add `tests/config/test_mlflow_config.py` to merged Step 2 — **accepted**
- Add explicit `get_cache_refresh_minutes` "not_a_number" test fix — **accepted**
- Improve langchain test guidance — **accepted**
- Update test file count ~15 → ~11 — **accepted**
- Add `by_label` pattern breakage note to verify step — **accepted**

**User decisions**: None needed (all straightforward improvements).

**Changes**:
- `step_2.md`: Rewritten with merged Steps 2+3 content. `_get_standard_env_var` kept alive, mlflow tests added, cache_refresh test fix specified.
- `step_3.md`: Replaced with old Step 4 content (int/list/langchain). Langchain test guidance improved.
- `step_4.md`: Replaced with old Step 5 content (verify rewrite). Added `_get_standard_env_var` deletion, `by_label` note.
- `step_5.md`: Deleted.
- `summary.md`: Updated steps table (5→4), test count (~15→~11).

**Status**: Committed (pending)

## Round 2 — 2026-04-13

**Findings**:
- No critical findings.
- All round 1 fixes verified: step merge correct, cross-references clean, `_get_standard_env_var` lifecycle correct, all test guidance present.
- Step 2 is the largest step but merge is justified (broken intermediate state). Changes are mechanical with low risk.
- `mlflow_config_loader.py` still passes explicit env vars for `tracking_uri`/`experiment_name` — this is fine (explicit takes precedence over schema lookup).

**Decisions**: No changes needed.

**User decisions**: None.

**Changes**: None.

**Status**: No changes — loop exits.

## Final Status

- **Rounds run**: 2
- **Plan changes**: Round 1 merged steps 2+3, fixed deletion timing, added test guidance. Round 2 confirmed all clean.
- **Plan is ready for approval.** 4 steps, all cross-references correct, no remaining issues.

