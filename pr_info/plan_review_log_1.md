# Plan Review Log — Issue #661

## Round 1 — 2026-04-06
**Findings**:
- [CRITICAL] Step 6 missing `_handle_workflow_failure` wrapper detail in implement/core.py (~10 call sites)
- [CRITICAL] Step 6 missing call-site volume note for create_pr/core.py (~8 calls)
- [ACCEPT] Step 2 NOTE inaccurately claims parser changes break CLI command tests
- [ACCEPT] Step 6 too large (6 source + 6 test files) — should split
- [ACCEPT] `post_issue_comments` in `create_plan` is YAGNI but acceptable for interface consistency
- [ACCEPT] Test file ownership between steps 5 and 6 unclear for `test_failure_handling.py`
- [SKIP] `get_config_values` return type handling (`== "True"`) — matches existing patterns
- [SKIP] Function signatures, test file paths, step ordering all verified correct
- [SKIP] Doc files referenced in step 8 exist

**Decisions**:
- Accept: Fix step 2 NOTE (straightforward)
- Accept: Split step 6 into 6a (workflow cores) and 6b (CLI commands) — **user chose option A**
- Accept: Add wrapper/call-site detail to step 6a
- Accept: Clarify test file ownership in step 5
- Accept: Keep `post_issue_comments` in create_plan for interface consistency (simpler than special-casing)
- Skip: Config value string comparison — existing pattern

**User decisions**:
- Q: Split step 6 into 6a/6b or keep as one? → **A: Split (option A)**

**Changes**:
- step_2.md: Replaced inaccurate NOTE about test breakage
- step_6.md: Converted to step 6a (workflow cores only), added wrapper/call-site detail
- step_6b.md: Created new file for CLI command changes
- step_5.md: Added test ownership clarification note
- summary.md: Updated step table with 6a/6b split

**Status**: changes applied, proceeding to round 2

## Round 2 — 2026-04-06
**Findings**:
- [CRITICAL] Step 2 NOTE references "Step 6a" but should say "Step 6b" (CLI changes are in 6b)
- [ACCEPT] Step 6a missing `tests/workflows/create_pr/test_failure_handling.py` from file list
- [SKIP] All other changes from round 1 verified correct

**Decisions**:
- Accept: Fix step 2 NOTE reference (straightforward)
- Accept: Add missing test file to step 6a (straightforward)

**User decisions**: None needed

**Changes**:
- step_2.md: Changed "Step 6a" to "Step 6b" in NOTE
- step_6.md: Added `test_failure_handling.py` to WHERE and TESTS sections

**Status**: changes applied, proceeding to round 3

## Round 3 — 2026-04-06
**Findings**: None — both fixes verified correct, formatting clean.
**Status**: no changes needed

## Round 4 — 2026-04-06
**Findings**:
- [CRITICAL] Steps 4→5 (old numbering) break mypy between commits — `helpers.py` calls `handle_workflow_failure(update_labels=...)` which would be a wrong keyword after step 4 renames the parameter
- [ACCEPT] Summary "Before" says comments are posted "always" — actually conditional on issue number, just not gated by a flag
- [ACCEPT] Step 7 `load_repo_config` return type `dict[str, Optional[str]]` needs updating to `dict[str, str | bool | None]` for new bool values
- [SKIP] `create_pr/core.py` backward-compat aliases — function references, signature-independent
- [SKIP] `load_repo_config` returning unused keys — acceptable for config validation

**Decisions**:
- Accept: Merge steps 4+5 into single step 4 (failure_handling.py + create_pr/helpers.py)
- Accept: Fix summary "Before" wording
- Accept: Add return type note to step 7

**User decisions**:
- Q: Merge steps 4+5? → **A: Agreed**

**Changes**:
- `step_4.md`: Merged old steps 4+5 (failure_handling + create_pr/helpers)
- `step_5.md`: Deleted old step 5, replaced with old step 6a (workflow cores) renumbered
- `step_6.md`: Replaced with old step 6b (CLI commands) renumbered
- `step_6b.md`: Deleted (content moved to step_6.md)
- `step_7.md`: Added return type note
- `summary.md`: Fixed "Before" wording, updated step table (8 steps → 8 files, 7 steps)

**Status**: changes applied, proceeding to round 5

## Final Status

Review complete. 4 rounds, 3 rounds with changes. Plan is ready for approval.

Changes across all rounds:
- `pr_info/steps/step_2.md` — fixed inaccurate NOTE
- `pr_info/steps/step_4.md` — merged old steps 4+5 (failure handling + create-pr helpers)
- `pr_info/steps/step_5.md` — renumbered from old step 6a (workflow cores)
- `pr_info/steps/step_6.md` — renumbered from old step 6b (CLI commands)
- `pr_info/steps/step_7.md` — added return type note
- `pr_info/steps/summary.md` — fixed wording, updated step table
