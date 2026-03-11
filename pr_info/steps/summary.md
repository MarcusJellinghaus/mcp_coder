# Issue #506: Add Documentation Structure Setup to repository-setup.md

## Summary

Two small changes to close a documentation gap and fix a bug:

1. **Bug fix**: `.claude/commands/implementation_review.md` references `docs/architecture/ARCHITECTURE.md` (wrong case) — the actual file is `docs/architecture/architecture.md`
2. **Documentation addition**: `docs/repository-setup.md` has no mention of documentation structure setup, even though `/implementation_review` depends on `docs/architecture/architecture.md` existing

## Architectural / Design Changes

**None.** This issue is purely documentation — no code, no tests, no architectural changes. Both modifications are to Markdown files only.

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `.claude/commands/implementation_review.md` | Bug fix | Fix `ARCHITECTURE.md` → `architecture.md` (case mismatch) |
| `docs/repository-setup.md` | Content addition | Add checklist item + "Architecture Documentation" section in Mandatory Setup |

## Files NOT Modified

No source code, tests, or configuration files are touched. No new files are created.

## Implementation Steps

| Step | Description | TDD? |
|------|-------------|------|
| 1 | Fix case mismatch in `implementation_review.md` | No (Markdown only) |
| 2 | Add documentation structure guidance to `repository-setup.md` | No (Markdown only) |
