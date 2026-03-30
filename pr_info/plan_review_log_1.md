# Plan Review Log — Issue #643

**Issue**: fix(vscodeclaude): startup script PATH ordering and missing commands for error statuses
**Reviewer**: Automated plan review supervisor
**Date**: 2026-03-30

## Round 1 — 2026-03-30

**Findings**:
- [critical] Ambiguity: `echo MCP-Coder environment:` line could be extracted from `if` block by implementer
- [critical] WHAT section vague about `MCP_CODER_PROJECT_DIR`/`MCP_CODER_VENV_DIR` placement
- [accept] Test should use substring matching, not exact full-line matching
- [accept] Step 2 test should use `@pytest.mark.parametrize`
- [accept] Step 2 test should verify exact command value `["/check_branch_status"]`
- [skip] Negative test for `status-10:pr-created` — harmless guard rail
- [skip] Step granularity appropriate (2 steps, 2 independent changes)
- [skip] File accuracy correct
- [skip] Step ordering logical

**Decisions**:
- Finding 1: accept — clarified echo stays inside the `if` block (moves with it)
- Finding 2: accept — split WHAT item 7 to explicitly name MCP env var placement
- Finding 3: accept — updated test plan to use substring matching
- Finding 4: accept — added `@pytest.mark.parametrize` recommendation
- Finding 5: accept — changed assertion from "non-empty list" to exact value
- Findings 6-9: skip — no action needed

**User decisions**: None — all findings were straightforward improvements.

**Changes**:
- `pr_info/steps/step_1.md`: clarified WHAT items 4, 7-8; updated test plan and LLM prompt for substring matching
- `pr_info/steps/step_2.md`: updated test plan and LLM prompt for parametrize and exact value assertion

**Status**: ready to commit
