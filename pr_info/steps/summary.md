# Issue #399: VSCodeClaude Status File Format Change

## Summary

Replace the markdown-formatted `.vscodeclaude_status.md` file with a plain text `.vscodeclaude_status.txt` file and add auto-open functionality via VS Code tasks.

## Architectural / Design Changes

### Before
- Status file: `.vscodeclaude_status.md` (Markdown table format)
- Single VS Code task in `tasks.json` (startup script only)
- Gitignore checks for `.md` extension

### After
- Status file: `.vscodeclaude_status.txt` (Plain text banner format)
- Two VS Code tasks in `tasks.json` (startup script + auto-open status file)
- Gitignore checks for `.txt` extension

### Design Decisions

1. **Plain text banner format**: Matches the existing `BANNER_TEMPLATE` pattern already used in startup scripts, ensuring visual consistency.

2. **Simplified template**: Removed unused fields (Branch, Started timestamp) to match the issue's specified format. The status file now mirrors what's shown in the terminal banner.

3. **Intervention handling**: Instead of a separate `INTERVENTION_ROW` template (markdown table row), intervention mode adds a simple `Mode:   ⚠️ INTERVENTION` line to the banner.

4. **Auto-open task**: Uses VS Code's `${workspaceFolder}` variable to open the status file, running in parallel with the startup script task.

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | Modify | Update `STATUS_FILE_TEMPLATE`, `GITIGNORE_ENTRY`, `TASKS_JSON_TEMPLATE`, remove `INTERVENTION_ROW` |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | Modify | Update `create_status_file()` filename and params, update `update_gitignore()` idempotency check |
| `.gitignore` | Modify | Add `.vscodeclaude_status.txt` (keep `.md` for backward compatibility) |
| `tests/workflows/vscodeclaude/test_workspace.py` | Modify | Update tests for new `.txt` extension and format |

## Implementation Steps Overview

| Step | Description | Files |
|------|-------------|-------|
| 1 | Update templates (STATUS_FILE_TEMPLATE, GITIGNORE_ENTRY, TASKS_JSON_TEMPLATE) | `templates.py` |
| 2 | Update workspace functions and project gitignore | `workspace.py`, `.gitignore` |
| 3 | Update tests for new format | `test_workspace.py` |

## Risk Assessment

- **Low risk**: Changes are isolated to vscodeclaude workflow
- **Backward compatibility**: Old `.md` files in existing sessions will remain (gitignored), new sessions get `.txt`
- **No breaking changes**: Function signatures remain unchanged
