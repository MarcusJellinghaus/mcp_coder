# Plan Review Log — Run 1

**Issue**: #555 — Catch connection/auth errors with helpful hints and optional truststore support
**Date**: 2026-03-23
**Branch**: 555-catch-connection-auth-errors-with-helpful-hints-and-optional-truststore-support

## Round 1 — 2026-03-23

**Findings**:
- F1 (critical): Step 4 Gemini except block missing `is_google_auth_error()` check — would misclassify server errors as auth errors
- F2 (accept): `(*GOOGLE_CLIENT_ERRORS,)` unpacking pattern needs a code comment for clarity
- F3-F9, F11-F15 (accept): Sound design — exception hierarchy, step sizing, test compatibility, DRY helpers all correct
- F10 (question): Gemini tests skip when SDK not installed — is this acceptable?
- F11 (accept): Dual `ensure_truststore()` placement is intentional redundancy with idempotent guard

**Decisions**:
- F1: Accept — fixed Step 4 code snippets to include `is_google_auth_error()` check
- F2: Accept — added inline comments explaining the unpacking pattern in Step 3
- F3-F9, F11-F15: Accept as-is — no changes needed
- F10: User decided skipping is the right approach (transparent). Added testing principle to `.claude/knowledge_base/python.md`

**User decisions**:
- F10: "Skipping is good — it's transparent." Applied broadly: tests for optional resources should skip, not fake.

**Changes**:
- `pr_info/steps/step_4.md`: Added `is_google_auth_error()` check in all Gemini except blocks
- `pr_info/steps/step_3.md`: Added comments explaining `(*GOOGLE_CLIENT_ERRORS,)` pattern
- `.claude/knowledge_base/python.md`: Added testing principle for optional resources

**Status**: Committed (ed0d218)

## Round 2 — 2026-03-23

**Findings**:
- Verified F1 fix: `is_google_auth_error()` check consistent across all Step 4 code snippets
- Verified F2 fix: unpacking comment in Step 3 is accurate
- No new critical or accept findings

**Decisions**: No changes needed

**User decisions**: N/A

**Changes**: None

**Status**: No changes needed

## Final Status

- **Rounds run**: 2
- **Commits produced**: 1 (ed0d218)
- **Plan status**: Ready for approval
- **Key fix**: Step 4 Gemini `is_google_auth_error()` check added to prevent misclassifying server errors as auth errors
