# Plan Review Log 1 — Issue #926

**Branch**: 926-feat-icoder-show-mcp-coder-utils-version-on-startup
**Date started**: 2026-04-28

## Round 1 — 2026-04-28

**Findings**:
- Step 2 banner test target was wishy-washy ("if X exists extend, otherwise add new")
- Step 1 commit message did not flag the side-effect that mcp-coder lookup also becomes graceful via the new helper
- Step 1 fixture conflict (helper tests must live outside `_mock_externals` scope) — already handled in plan
- Step 3 import-removal lint guarantee — pylint/ruff cannot validate removal; tests are the real guard (already covered)
- Test rename to `test_info_shows_versions` (plural) — already in plan
- `RuntimeInfo` field-ordering change — safe, kwargs-only callers
- Absence of a final "verify everything" step — correctly absent per planning principles

**Decisions**:
- Accept (fix): commit step 2 to a single concrete test path
- Accept (fix): add a one-line reviewer note in step 1 about graceful mcp-coder lookup
- Skip (already correct): items 3-7 above need no change

**User decisions**: none — no design or requirements questions raised this round

**Changes**:
- `pr_info/steps/step_2.md`: removed conditional language; committed to `tests/icoder/ui/test_app.py` with a concrete test function `test_banner_renders_mcp_coder_utils_version`. Evidence: grep of `tests/icoder/**/*.py` for `mcp-coder|mcp_coder_version|banner` showed no existing banner assertion; `test_app.py` mirrors src structure for `src/mcp_coder/icoder/ui/app.py`.
- `pr_info/steps/step_1.md`: appended one-line reviewer note that routing `mcp-coder` through `_get_package_version` makes its lookup graceful (previously raised `PackageNotFoundError`).

**Status**: committed
