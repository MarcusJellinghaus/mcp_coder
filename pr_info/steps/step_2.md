# Step 2: Add search_reference_files permission

## Context
See [summary.md](summary.md) for overall context. This step adds the new `mcp__workspace__search_reference_files` tool permission introduced by mcp-workspace#92.

## WHERE
- `.claude/settings.local.json` — the `permissions.allow` array

## WHAT
Insert `"mcp__workspace__search_reference_files"` in alphabetical order, after `"mcp__workspace__search_files"`.

## HOW
- Use `mcp__workspace__edit_file` to add the new entry after the `search_files` line
- Maintain alphabetical ordering among `mcp__workspace__*` entries

## ALGORITHM
```
find line: "mcp__workspace__search_files"
insert after it: "mcp__workspace__search_reference_files"
```

## DATA
No runtime data changes. The permissions array gains one additional string entry.

## Commit
```
chore(config): add search_reference_files permission
```

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md, then implement step 2.
Add mcp__workspace__search_reference_files permission to .claude/settings.local.json.
This is config-only — no code quality checks required.
```
