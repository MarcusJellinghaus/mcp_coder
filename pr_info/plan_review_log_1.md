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

**Status**: Ready to commit
