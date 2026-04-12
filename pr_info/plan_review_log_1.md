# Plan Review Log — Run 1

**Issue:** #737 — refactor: consolidate formatters into mcp-tools-py
**Date:** 2026-04-12
**Reviewer:** Plan Review Supervisor

## Round 1 — 2026-04-12
**Findings:**
- [CRITICAL] Plan's mcp-tools-py import paths appeared missing — engineer checked library source
- [CRITICAL] Missing tach.toml dependency: `mcp_coder.workflows` needs `mcp_coder.mcp_tools_py`
- [CRITICAL] `test_error_recovery_patterns` also patches `format_code` — missed in step 1
- [ACCEPT] Steps 2+4 violate "each step leaves checks passing" — merge them
- [ACCEPT] Dead `formatter_integration` pytest marker not cleaned up
- [ACCEPT] Keep `black_isolation`/`isort_isolation` contracts as guardrails
- [ACCEPT] Summary says "3 contracts" but step 4 lists 4
- [SKIP] `Any` import removal confirmed correct
- [SKIP] `icoder` missing from `tach_docs.py` diagram — pre-existing, out of scope

**Decisions:**
- Import paths: User updated reference project; re-verified — all 3 import paths confirmed valid
- Isolation contracts: User chose to KEEP `black_isolation`/`isort_isolation`
- tach.toml dep, missed test, step merge, marker cleanup, summary count: accepted as straightforward fixes

**User decisions:**
- Q1: Import paths — user updated reference project, imports confirmed valid
- Q2: Keep isolation contracts (option A)

**Changes:**
- step_1.md: Added tach.toml dependency, `test_error_recovery_patterns` patch, all 5 verification checks
- step_2.md: Rewritten — merged old steps 2+4; keeps isolation contracts; adds marker cleanup
- step_3.md: Renumbered (was step 3, stays step 3)
- step_4.md: Deleted
- summary.md: Rewritten for 3-step structure with all fixes reflected

**Status:** committed

## Round 2 — 2026-04-12
**Findings:**
- [CRITICAL] Step 3 verification section missing `lint_imports_check` and `vulture_check`
- [ACCEPT] All round 1 fixes properly reflected, no regressions
- [ACCEPT] Step boundaries, consistency, completeness all verified

**Decisions:** Accept — add missing checks to step 3

**User decisions:** None needed

**Changes:** step_3.md verification section updated to include all 5 checks

**Status:** committed

## Round 3 — 2026-04-12
**Findings:** None — all verification sections confirmed complete across all 3 steps

**Status:** no changes needed

## Final Status

Plan review complete. 3 rounds, all issues resolved. Plan restructured from 4 steps to 3:
1. Add shim + swap caller + tach.toml dependency
2. Delete formatters package + update all configs/docs
3. Trim pyproject_config.py helpers

Plan is ready for implementation.
