# Plan Review Log — Run 1

**Issue:** #500 — Migrate commands to skills format
**Date:** 2026-03-31
**Branch:** 500-migrate-commands-to-skills-format

## Round 1 — 2026-03-31

**Findings**:
- (critical) Colon separator syntax in allowed-tools is deprecated; space separator is correct
- (critical) `plan_approve` and `implementation_needs_rework` have wrong tool name in allowed-tools (`mcp-coder set-status` vs actual `mcp-coder gh-tool set-status`)
- (critical) `Skill(plan_review_supervisor)` confirmed missing from settings.local.json — step 9 addresses this
- (improvement) `issue_create` silently adds `git ls-remote` tool not in original
- (improvement) `plan_update` missing `mcp__workspace__list_directory` in allowed-tools
- (improvement) `implementation_finalise` over-restricted — original has no allowed-tools
- (improvement) Step 10 has unnecessary verification checklist
- (improvement) Step 9 commit message doesn't reflect config + docs scope
- (improvement) Supervisor workflow split boundaries (steps 7, 8) too vague
- (improvement) Supervisor skills given strict allowed-tools but originals are unrestricted
- (improvement) No acceptance criteria to verify content equivalence during migration
- (note) All 18 commands accounted for, no gaps
- (note) Step ordering and dependencies correct
- (note) Step granularity appropriate

**Decisions**:
- accept: Change all colon separators to space separators (deprecated syntax)
- accept: Fix plan_approve/implementation_needs_rework tool name (pre-existing bug)
- accept: Add list_directory to plan_update
- accept: Document git ls-remote addition to issue_create as intentional
- accept: Remove allowed-tools from implementation_finalise (keep unrestricted like original)
- accept: Simplify step 10 — remove verification checklist
- accept: Update step 9 commit message to reflect config + docs
- accept: Add clearer split boundaries for supervisor steps 7, 8
- accept: Add content verification acceptance criteria to steps 1-8
- skip: Supervisor allowed-tools — user confirmed originals are unrestricted, keep as-is
- skip: All note-level findings — correct, no action needed

**User decisions**:
- Q1: Colon vs space separator? → **Space** (colon is deprecated)
- Q2: implementation_finalise tool scope? → **Unrestricted** (no allowed-tools, matches original)
- Q3: Supervisor skills need Skill() in allowed-tools? → **No change** — supervisors stay unrestricted as they are today
- Q4: Content verification during migration? → **Yes** — add acceptance criteria to verify SKILL.md content matches original command body

**Changes**: Updated step_1.md through step_10.md — colon→space separators, tool name fixes, added list_directory, removed implementation_finalise restrictions, updated commit message, simplified step 10, clarified split boundaries, added content verification acceptance criteria

**Status**: pending commit

