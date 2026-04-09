# Plan Review Log — Issue #310 (Split implement/core.py)

Review run 1 — 2026-04-09

## Round 1 — 2026-04-09
**Findings**:
- (critical) test_ci_check.py has ~28 @patch decorators and direct imports targeting core.* for CI symbols — completely missing from the plan. Tests would break after step 2.
- (critical) caplog logger name strings in TestPollForCiCompletionHeartbeat need updating from core → ci_operations in step 3. Plan only mentioned @patch paths.
- (accept) Step 4 is pure verification with no tangible results — violates planning principles.
- (accept) Dict/logging cleanup guidance in step 3 was ambiguous.
- (confirmed) _short_sha correctly belongs in ci_operations (all 7 call sites are CI functions).
- (confirmed) FINALISATION_PROMPT content and substitution placeholders are correct.
- (confirmed) Import cleanup list for core.py is comprehensive and correct.
- (confirmed) __init__.py exports unaffected.

**Decisions**:
- F1 (test_ci_check.py): Accept — add to step 2 (must be same commit to keep tests green)
- F2 (caplog): Accept — add to step 3
- F9 (step 4): Accept — merge into step 3
- F10 (Dict/logging): Accept — clarify in step 3

**User decisions**: None needed — all findings were straightforward.

**Changes**:
- step_2.md: Added test_ci_check.py to WHERE; replaced "verify no other files" subsection with detailed @patch update instructions; updated ALGORITHM and Tests sections
- step_3.md: Updated title; added caplog logger name update note; clarified import cleanup; merged step 4 verification tasks; updated ALGORITHM, Tests, and LLM Prompt
- step_4.md: Deleted (merged into step 3)
- summary.md: Added test_ci_check.py to Files Modified; cleaned up implementation steps

**Status**: Changes applied, proceeding to round 2.

## Round 2 — 2026-04-09
**Findings**:
- All round 1 changes verified correctly applied
- step_4.md confirmed deleted
- No internal inconsistencies or dangling references
- Each step verified to leave tests green
- Minor imprecisions noted (28 vs "~30+" @patch count, extra symbols in example list) — harmless, won't affect implementation

**Decisions**: No changes needed.

**User decisions**: None.

**Changes**: None.

**Status**: No changes needed.

## Final Status

- **Rounds**: 2
- **Commits**: 1 (plan updates from round 1)
- **Plan status**: Ready for approval
- **Key changes made**: Added missing test_ci_check.py updates to step 2, added caplog logger name fix to step 3, merged verification step 4 into step 3 (now 3 steps total)
