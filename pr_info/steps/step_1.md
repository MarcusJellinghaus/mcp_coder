# Step 1: Update settings.local.json permissions

**Ref:** See `pr_info/steps/summary.md` for full context.

## WHERE

- `.claude/settings.local.json`

## WHAT

Update the `permissions.allow` array:

**Remove these 4 entries:**
- `Bash(git diff:*)`
- `Bash(git log:*)`
- `Bash(git status:*)`
- `Bash(mcp-coder git-tool:*)`

**Add these 4 entries** (in alphabetical order among the existing `mcp__workspace__*` entries):
- `mcp__workspace__git_diff`
- `mcp__workspace__git_log`
- `mcp__workspace__git_merge_base`
- `mcp__workspace__git_status`

## HOW

Direct JSON edit. The `permissions.allow` array is alphabetically sorted — maintain that convention.

**Keep unchanged:** `Bash(git fetch:*)`, `Bash(git ls-tree:*)` — these have no MCP equivalent.

## DATA

No data structures. JSON config file only.

## Tests

No tests — this is a JSON config change with no code.

## Verification

After editing, confirm:
1. The JSON is valid (no syntax errors)
2. The 4 removed entries are gone
3. The 4 new entries are present
4. Alphabetical ordering is maintained

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_1.md.

Update .claude/settings.local.json: remove the 4 Bash git permissions listed in the step
and add the 4 MCP workspace git tool permissions. Maintain alphabetical order in the allow array.
Verify the JSON is valid after editing.
```
