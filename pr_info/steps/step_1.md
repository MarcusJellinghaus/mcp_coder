# Step 1: Migrate .mcp.json to KV format and add search_reference_files permission

## Context
See [summary.md](summary.md) for overall context. This step migrates all 4 `--reference-project` values in `.mcp.json` from the deprecated `name=path` format to the new `name=...,path=...,url=...` KV format, and adds the new `mcp__workspace__search_reference_files` tool permission.

## Part A: Migrate .mcp.json reference-project args

### WHERE
- `.mcp.json` — the `workspace.args` array

### WHAT
Replace 4 string values (1:1, no structural changes):

| Old value | New value |
|-----------|-----------|
| `p_workspace=${USERPROFILE}\\Documents\\GitHub\\mcp-workspace` | `name=p_workspace,path=${USERPROFILE}\\Documents\\GitHub\\mcp-workspace,url=https://github.com/MarcusJellinghaus/mcp-workspace` |
| `p_config=${USERPROFILE}\\Documents\\GitHub\\mcp-config` | `name=p_config,path=${USERPROFILE}\\Documents\\GitHub\\mcp-config,url=https://github.com/MarcusJellinghaus/mcp-config` |
| `p_coder-utils=${USERPROFILE}\\Documents\\GitHub\\mcp-coder-utils` | `name=p_coder-utils,path=${USERPROFILE}\\Documents\\GitHub\\mcp-coder-utils,url=https://github.com/MarcusJellinghaus/mcp-coder-utils` |
| `p_tools=${USERPROFILE}\\Documents\\GitHub\\mcp-tools-py` | `name=p_tools,path=${USERPROFILE}\\Documents\\GitHub\\mcp-tools-py,url=https://github.com/MarcusJellinghaus/mcp-tools-py` |

### HOW
- Use `mcp__workspace__edit_file` with 4 edits (one per reference-project value)
- Preserve escaped backslashes (`\\`) for Windows paths
- Do not change the surrounding `--reference-project` arg structure

### ALGORITHM
```
for each of the 4 reference-project values:
    replace "name=path" string with "name=...,path=...,url=..." string
```

## Part B: Add search_reference_files permission

### WHERE
- `.claude/settings.local.json` — the `permissions.allow` array

### WHAT
Insert `"mcp__workspace__search_reference_files"` in alphabetical order, after `"mcp__workspace__search_files"`.

### HOW
- Use `mcp__workspace__edit_file` to add the new entry after the `search_files` line
- Maintain alphabetical ordering among `mcp__workspace__*` entries

### ALGORITHM
```
find line: "mcp__workspace__search_files"
insert after it: "mcp__workspace__search_reference_files"
```

## DATA
No runtime data changes. The args array retains the same structure. The permissions array gains one additional string entry.

## Commit
```
chore(config): migrate .mcp.json to KV format and add search_reference_files permission
```

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md, then implement step 1.
Part A: Migrate the 4 --reference-project values in .mcp.json from old format to new KV format.
Part B: Add mcp__workspace__search_reference_files permission to .claude/settings.local.json.
This is config-only — no code quality checks required.
```
