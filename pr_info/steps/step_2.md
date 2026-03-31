# Step 2: Skill File + Settings Update

> **Context**: See `pr_info/steps/summary.md` for full overview of issue #647.
> **Depends on**: Step 1 (CLI command exists and is wired).

## Goal

Create the `implement_direct` skill and add its permission to settings.

## WHERE

- **Create**: `.claude/skills/implement_direct/SKILL.md`
- **Modify**: `.claude/settings.local.json`

## WHAT

### Skill file `.claude/skills/implement_direct/SKILL.md`:

**Frontmatter** (as specified in issue):
```yaml
---
name: implement-direct
disable-model-invocation: true
argument-hint: [issue-number]
allowed-tools: Bash(mcp-coder gh-tool *)
---
```

Note: Other tool permissions (MCP workspace, pylint, pytest, mypy) come from `settings.local.json` — they don't need to be in the skill's `allowed-tools`.

**Prompt body** instructs Claude to:

1. Fetch issue details via `gh issue view $ARGUMENTS`
2. Checkout/create issue branch via `mcp-coder gh-tool checkout-issue-branch <number>`
3. Read relevant code, understand context
4. Implement changes directly (no `pr_info/`, no `TASK_TRACKER.md`)
5. Run quality checks: pylint, pytest, mypy, ruff
6. Run `./tools/format_all.sh`
7. Suggest follow-up steps:
   - `/commit_push`
   - `mcp-coder gh-tool set-status status-07:code-review`
   - `/check_branch_status`
   - `/implementation_review`

Include scope guidance: recommend `/create_plan` → `/implement` workflow for complex features.

### Settings update `.claude/settings.local.json`:

Add to `permissions.allow` array:
```json
"Skill(implement_direct)"
```

Also update the existing `gh-tool` permission to use a wildcard pattern (matching the existing `git-tool` pattern):
```
"Bash(mcp-coder gh-tool get-base-branch)" → "Bash(mcp-coder gh-tool:*)"
```
This covers all current and future `gh-tool` subcommands (including `checkout-issue-branch`) with a single entry.

## HOW

- The skill file is pure markdown — no code, no tests needed
- Settings is a JSON edit — add one line to the allow list, update one existing line
- Place the new permission near the other `Skill(...)` entries for readability

## TESTS

No automated tests for this step — it's a markdown skill file and a JSON config entry. Verify manually:
- Skill file has correct frontmatter fields
- Settings file is valid JSON after edit

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement Step 2:

1. Create `.claude/skills/implement_direct/SKILL.md` with the frontmatter and prompt
   as described in the step file and the original issue #647.
2. Add `Skill(implement_direct)` to `.claude/settings.local.json` permissions.
3. Update `"Bash(mcp-coder gh-tool get-base-branch)"` to `"Bash(mcp-coder gh-tool:*)"` in settings.

No code quality checks needed for this step (no Python changes).
Verify the settings JSON is valid after editing.
```
