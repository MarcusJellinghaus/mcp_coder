# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Parse the rich `tools:` block (`skill_tools.py`) + `ClaudeSkill.tools_block`

- [x] Implementation: write `tests/icoder/test_permissions_skill_tools.py` (malformed-vs-absent parametrisation incl. present-but-null, bare-`use:`, advisories, `load_skills` populates `tools_block`), create pure `permissions/skill_tools.py` (`SkillToolsBlock` + `parse_tools_block`), add + populate `ClaudeSkill.tools_block`, update `.importlinter`
- [x] Quality checks: pylint, pytest, mypy, ruff (D/DOC), lint-imports — fix all issues (pylint/ruff/lint-imports green; mypy clean for the new code; pytest could not execute — pre-existing env break: `mcp_workspace.checks.branch_status_rendering` missing, fails identically on unmodified tests)
- [x] Commit message prepared

### Step 2: Build the frame (`skill_frame.py`) + `Base` Literal

- [ ] Implementation: write `tests/icoder/test_permissions_skill_frame.py` (one test per mapping-table row / AC), add `Base` Literal + retype `PermissionFrame.base` in `model.py`, create pure `permissions/skill_frame.py` (`SkillFrame` + `build_frame` + `as_base` + `two_empties` with token classifier and deny-asymmetry rules), update `.importlinter`
- [ ] Quality checks: pylint, pytest, mypy, ruff (D/DOC), lint-imports — fix all issues
- [ ] Commit message prepared

### Step 3: Transport — swap carrier, wire frame-map snapshot, delete `build_legacy_frame`

- [ ] Implementation: migrate listed tests, swap `SendToLLM.allowed_tools` → `skill_name`, `LLMService.stream(*, frame=...)` on Protocol/Real/Fake (drop `enforce_skill_tools`, add `Fake.last_frame`), delete `build_legacy_frame`, add `skill_frames` snapshot + rewrite `AppCore.stream_llm`, thread `skill_name` through `ui/app.py`, add `ENFORCE_SKILL_TOOLS` + build per-provider frame map in `cli/commands/icoder.py`, document `permission_warning` in `llm/types.py`, update stale docstrings, update `.importlinter`
- [ ] Quality checks: pylint, pytest, mypy, ruff (D/DOC), lint-imports — fix all issues
- [ ] Commit message prepared

### Step 4: Blocked-skill handling — refuse to run + mark in autocomplete

- [ ] Implementation: write listed tests, add `Command.disabled_reason`, add `CommandRegistry.get`, give `register_skill_commands` optional `disabled_reasons`, pass `{name: blocked_reason}` from frame map in `cli/commands/icoder.py`, add pre-dispatch refusal guard to `AppCore.handle_input`, mark disabled rows (label-only, stay enabled) in `command_autocomplete.update_matches`
- [ ] Quality checks: pylint, pytest, mypy, ruff (D/DOC), lint-imports — fix all issues
- [ ] Commit message prepared

### Step 5: Startup feedback — list broken skills + loud degraded-config line

- [ ] Implementation: write listed tests, add pure `format_startup_permission_notices` to `runtime_banner.py`, expose `broken_skills` + `permission_degraded` on `AppCore`, hoist + pass `permission_degraded` from `cli/commands/icoder.py`, render notices in `ui/app.py` `on_mount` (outside the `runtime_info` branch, re-query `OutputLog`); verify every issue #1061 acceptance criterion is covered across Steps 1–5
- [ ] Quality checks: pylint, pytest, mypy, ruff (D/DOC), lint-imports — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Address PR review feedback
- [ ] Write PR summary
