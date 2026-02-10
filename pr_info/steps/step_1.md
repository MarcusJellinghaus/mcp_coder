# Step 1: Update Source Files

## LLM Prompt

```
Reference: pr_info/steps/summary.md and this step file.

Fix the .vscodeclaude_status extension regression by replacing `.vscodeclaude_status.md` 
with `.vscodeclaude_status.txt` in the source files listed below.
```

## WHERE: Files to Modify

1. `src/mcp_coder/workflows/vscodeclaude/workspace.py`
2. `src/mcp_coder/workflows/vscodeclaude/templates.py`

## WHAT: Changes Required

### workspace.py

| Location | Function | Change |
|----------|----------|--------|
| ~Line 277 | `update_gitignore()` | Idempotency check string |
| ~Line 497 | `create_status_file()` | Output filename |

### templates.py

| Location | Constant | Change |
|----------|----------|--------|
| `TASKS_JSON_TEMPLATE` | Status file path in args | `.md` → `.txt` |
| `GITIGNORE_ENTRY` | Gitignore pattern | `.md` → `.txt` |

## HOW: Integration Points

No integration changes. These are string literal replacements only.

## ALGORITHM

```
1. Open workspace.py
2. Replace ".vscodeclaude_status.md" with ".vscodeclaude_status.txt" (2 occurrences)
3. Open templates.py
4. Replace ".vscodeclaude_status.md" with ".vscodeclaude_status.txt" (2 occurrences)
5. Save both files
```

## DATA: Expected State After

- `workspace.py`: `update_gitignore()` checks for `.txt`, `create_status_file()` writes `.txt`
- `templates.py`: `TASKS_JSON_TEMPLATE` references `.txt`, `GITIGNORE_ENTRY` contains `.txt`

## Verification

After this step, existing tests will fail because they still expect `.md`. This is expected and will be fixed in Step 2.
