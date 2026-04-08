# Step 5: Delete `icoder.bat` + Update Documentation

> **Context:** Read `pr_info/steps/summary.md` for full issue context.

## Goal

Hard-delete `icoder.bat` (no deprecation stub) and update all 6 files that reference it.

## WHERE

- **Delete:** `icoder.bat`
- **Modify:** `docs/environments/environments.md` (line 63)
- **Modify:** `docs/repository-setup/claude-code.md` (line 122)
- **Modify:** `docs/repository-setup/README.md` (line 78)
- **Modify:** `docs/repository-setup/internal.md` (lines 16-17)
- **Modify:** `icoder_local.bat` (line 5)
- **Modify:** `repo_architecture_plan/mcp_monorepo_plan.md` (line 114)

## WHAT — Exact Changes

### 1. Delete `icoder.bat`
Hard delete. No stub.

### 2. `docs/environments/environments.md` (line 63)
**Before:**
```
> All launcher scripts (`claude.bat`, `claude_local.bat`, `icoder.bat`, `icoder_local.bat`) print MCP server versions ...
```
**After:**
```
> All launcher scripts (`claude.bat`, `claude_local.bat`, `icoder_local.bat`) print MCP server versions ...
```

### 3. `docs/repository-setup/claude-code.md` (line 122)
**Before:**
```
Set by the launcher scripts (`claude.bat`, `claude_local.bat`, `icoder.bat`, `icoder_local.bat`) before Claude Code starts:
```
**After:**
```
Set by the launcher scripts (`claude.bat`, `claude_local.bat`, `icoder_local.bat`) or `mcp-coder icoder` before Claude Code starts:
```

### 4. `docs/repository-setup/README.md` (line 78)
**Before:**
```
| `icoder.bat` / `icoder_local.bat` | I | — | — | mcp-coder repo only |
```
**After:**
```
| `icoder_local.bat` | I | — | — | mcp-coder repo only |
```

### 5. `docs/repository-setup/internal.md` (lines 16-17)
**Before:**
```
| `icoder.bat` | Launches the `mcp-coder icoder` interactive command (this repo) |
| `icoder_local.bat` | Same, using local venv for testing source changes |
```
**After:**
```
| `icoder_local.bat` | Launches iCoder using local venv for testing source changes |
```

### 6. `icoder_local.bat` (line 5)
**Before:**
```
REM Same two-env discovery as icoder.bat, plus editable-install verification
```
**After:**
```
REM Two-env discovery with editable-install verification
```

### 7. `repo_architecture_plan/mcp_monorepo_plan.md` (line 114)
**Before:**
```
| `icoder` / `icoder.bat` | mcp_coder | launcher batfile → `mcp-coder icoder` | stays in `packages/mcp-coder/` |
```
**After:**
```
| `icoder` | mcp_coder | `mcp-coder icoder` (self-sufficient) | stays in `packages/mcp-coder/` |
```

## Tests

No new tests — this is a mechanical deletion + doc update step. All existing tests must continue to pass (icoder.bat was never tested by Python tests).

## Commit

```
chore: retire icoder.bat, update docs

mcp-coder icoder is now self-sufficient — icoder.bat is no longer
needed. icoder_local.bat stays (dev edition with editable-install
check). Updated 6 files that referenced icoder.bat.

Closes #724.
```
