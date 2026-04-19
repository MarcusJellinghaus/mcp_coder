# Plan Review Log — Issue #813 (Run 2)

## Round 1 — 2026-04-19

**Findings**:
1. (Critical) Steps 2/3 can't produce independent clean commits — step 2 source changes break test @patch targets not updated until step 3
2. (Improvement) Missing `tach.toml` `depends_on` entries in step 5 — vague "verify with tach check" instead of explicit list
3. (Improvement) `.importlinter` layered_architecture inconsistent with `tach.toml` — shim on same layer as utils instead of below
4. (Informational) `__init__` symbol count stale (says 6, actually 10 of 29)
5. (Nit) Step 2 should note which files DON'T need changes — skipped (cosmetic)
6. (Informational) Architecture docs will become stale — skipped (out of scope)
7. (Nit) `test_git_encoding_stress.py` dead import should be definitive, not "check if used"

**Decisions**:
- Finding 1 → accepted: moved 7 test files from step 3 to step 2 (test @patch updates alongside source changes)
- Finding 2 → accepted: listed 6 modules needing `depends_on` for `mcp_workspace_git`
- Finding 3 → accepted: placed shim on separate layer below utils in layered_architecture
- Finding 4 → accepted: updated symbol count to "10 of 29"
- Finding 5 → skipped (cosmetic, plan is clear enough)
- Finding 6 → skipped (out of scope)
- Finding 7 → accepted: changed to definitive "unused in this file"

**User decisions**: None needed (all findings were straightforward).

**Changes**:
- step_2.md: Added principle note, added 7 test files section, updated algorithm and LLM prompt
- step_3.md: Reduced scope to remaining tests + delete old tests + smoke test, fixed is_git_repository ambiguity
- step_5.md: Listed explicit `depends_on` entries, fixed layered_architecture placement
- summary.md: Updated step descriptions, fixed symbol count

**Status**: pending commit
