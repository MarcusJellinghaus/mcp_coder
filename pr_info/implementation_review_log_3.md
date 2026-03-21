# Implementation Review Log — Run 3

**Issue**: #530 — feat: add supervised implementation review skill
**Date**: 2026-03-21
**Reviewer**: Claude (Supervisor)

## Round 1 — 2026-03-21

### Findings

1. **`settings.local.json` missing trailing newline**: The diff shows the file now ends without a newline (`\ No newline at end of file`). This is a minor formatting issue but can produce noisy diffs in the future.

2. **`DISCUSSION_SECTION_WINDOWS` hardcodes `/discuss` instead of using `followup_cmd`**: The `DISCUSSION_SECTION_WINDOWS` template (templates.py line 125) hardcodes `echo Running: /discuss` and `mcp-coder prompt "/discuss"`. The workspace code conditionally includes/excludes this section based on `followup_cmd is not None`, but when it is included, the actual followup command value from config is never passed into the template. Currently this works because the only non-null followup_command in labels.json is `/discuss`, but if another followup command were added, the template would still render `/discuss`.

3. **`INTERACTIVE_SECTION_LINUX` template comment is misleading for Windows path**: The added comment on templates.py says "Callers must pass followup_command='' (not None) to avoid rendering 'None'", but the Windows code path doesn't use `INTERACTIVE_SECTION_LINUX` at all — it uses `INTERACTIVE_SECTION_WINDOWS` which has no `{followup_command}` placeholder. The comment is only relevant for the Linux path (which is not yet implemented). The comment is accurate for the Linux template but could confuse readers since the surrounding diff context is about a Windows change.

4. **Linux path not updated for `followup_cmd=None` handling**: The Linux code path (currently `raise NotImplementedError`) will eventually need the same `followup_cmd` null-handling. The `STARTUP_SCRIPT_LINUX` template has `{interactive_section}` but `INTERACTIVE_SECTION_LINUX` embeds `{followup_command}` directly. When Linux is implemented, passing `None` as `followup_command` would render `"None"` in the script. The comment added in this PR acknowledges this, but no guard exists yet.

5. **Test `test_omits_discussion_section_when_followup_command_null` — good coverage**: The new test properly verifies that when `followup_command` is `None`, the discussion section is omitted and the interactive section is still present. Good addition.

6. **Test `test_creates_script_with_mcp_coder_prompt` changed to `status-01:created`**: This was necessary because `status-07:code-review` now has `followup_command=None`, which means the discussion section (containing `--session-id %SESSION_ID%`) would be absent. The test needs a status that has a non-null followup command to verify the mcp-coder prompt discussion flow. Correct fix.

7. **`implementation_review_supervisor.md` has no YAML frontmatter**: The other command files (e.g., `implementation_finalise.md`, `implementation_needs_rework.md`, `plan_approve.md`) have YAML frontmatter with `workflow-stage`, `suggested-next`, and `allowed-tools`. The new supervisor command file has no frontmatter at all.

8. **`commit-pusher.md` agent file**: New agent with `permissionMode: acceptEdits`. This is a configuration file for subagent delegation — looks correct for its purpose.

### Decisions

1. **Missing trailing newline in `settings.local.json`** — **ACCEPT**. Easy fix, prevents noisy future diffs.

2. **Hardcoded `/discuss` in `DISCUSSION_SECTION_WINDOWS`** — **SKIP**. Per YAGNI principle: currently all non-null followup commands are `/discuss`. Making this configurable would be building for a hypothetical future requirement. If a new followup command is added later, this can be updated then.

3. **Comment on `INTERACTIVE_SECTION_LINUX` is slightly misleading in context** — **SKIP**. Per "prefer readable code over comments" principle: the comment is technically accurate for the Linux template it decorates. It doesn't affect correctness. Cosmetic concern.

4. **Linux path not updated for `followup_cmd=None`** — **SKIP**. Per YAGNI: Linux path is explicitly `NotImplementedError`. The comment acknowledges the issue. When Linux is implemented (Step 17), this will be addressed.

5. **New test `test_omits_discussion_section_when_followup_command_null`** — no action needed, good test.

6. **Test status change to `status-01:created`** — no action needed, correct adaptation.

7. **Missing YAML frontmatter in `implementation_review_supervisor.md`** — **ACCEPT**. This is a consistency issue with the other command files. Adding frontmatter with `workflow-stage: code-review` and `suggested-next` would align it with the pattern established by the other commands.

8. **`commit-pusher.md`** — no action needed, looks correct.

### Accepted Items for Implementation

- **Item 1**: Add trailing newline to `.claude/settings.local.json`
- **Item 7**: Add YAML frontmatter to `.claude/commands/implementation_review_supervisor.md` consistent with other command files

### Changes Made

1. **`.claude/settings.local.json`**: Restored trailing newline at end of file.
2. **`.claude/commands/implementation_review_supervisor.md`**: Added YAML frontmatter (`workflow-stage: code-review`, `suggested-next: implementation_approve or implementation_needs_rework`) to match the pattern used by other command files.

### Verification

- Pylint: PASS (no issues)
- Pytest: PASS (2428/2428)
- Mypy: PASS (no type errors)

**Status**: Changes applied, awaiting commit.

---

## Final Status

**Review complete.** Two minor issues found and fixed:
1. Missing trailing newline in `settings.local.json`
2. Missing YAML frontmatter in `implementation_review_supervisor.md`

Six items were reviewed and skipped as out-of-scope per engineering principles (YAGNI, cosmetic, speculative). No major issues or refactoring needed.

All code quality checks pass. The source code changes in `workspace.py`, `templates.py`, `labels.json`, and `test_workspace.py` are well-structured with proper test coverage for the new `followup_command=null` behavior.
