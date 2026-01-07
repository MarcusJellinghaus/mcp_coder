# Step 2: Update Command Templates

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 2.

Task: Update the command templates in command_templates.py to install type stubs in the project environment before running mcp-coder commands.

Reference: pr_info/steps/step_2.md for detailed specifications.
```

## Overview

Update all 8 command templates (4 Windows + 4 Linux) to ensure type stubs are installed in the project environment before mcp-coder commands execute.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/coordinator/command_templates.py` | Modify 8 template strings |

## WHAT

### Linux Templates (4 templates)

**Change**: Replace `uv sync --extra dev` with `uv sync --extra types`

Templates to modify:
1. `DEFAULT_TEST_COMMAND`
2. `CREATE_PLAN_COMMAND_TEMPLATE`
3. `IMPLEMENT_COMMAND_TEMPLATE`
4. `CREATE_PR_COMMAND_TEMPLATE`

**Example change in `IMPLEMENT_COMMAND_TEMPLATE`**:

Before:
```bash
uv sync --extra dev
```

After:
```bash
uv sync --extra types
```

### Windows Templates (4 templates)

**Change**: Add `uv sync --extra types` step before mcp-coder command execution

Templates to modify:
1. `DEFAULT_TEST_COMMAND_WINDOWS`
2. `CREATE_PLAN_COMMAND_WINDOWS`
3. `IMPLEMENT_COMMAND_WINDOWS`
4. `CREATE_PR_COMMAND_WINDOWS`

**Pattern for Windows templates** - Add this block before `echo command execution`:

```batch
echo Install type stubs in project environment ====================
cd %WORKSPACE%\repo
uv sync --extra types

echo switch to python execution environment =====================
cd %VENV_BASE_DIR%
```

## HOW

### Linux Template Changes

For each Linux template, find and replace:
```
uv sync --extra dev
```
With:
```
uv sync --extra types
```

### Windows Template Changes

For each Windows template, insert the type stub installation block. The insertion point is **before** the `echo command execution` line.

**Example for `IMPLEMENT_COMMAND_WINDOWS`**:

Before:
```batch
@echo ON

echo current WORKSPACE directory===================================
cd %WORKSPACE%

echo switch to python execution environment =====================
cd %VENV_BASE_DIR%

echo python environment ================================
...
set DISABLE_AUTOUPDATER=1

echo command execution  =====================================
mcp-coder --log-level {log_level} implement ...
```

After:
```batch
@echo ON

echo current WORKSPACE directory===================================
cd %WORKSPACE%

echo Install type stubs in project environment ====================
cd %WORKSPACE%\repo
uv sync --extra types

echo switch to python execution environment =====================
cd %VENV_BASE_DIR%

echo python environment ================================
...
set DISABLE_AUTOUPDATER=1

echo command execution  =====================================
mcp-coder --log-level {log_level} implement ...
```

## ALGORITHM (for Windows template modification)

```
1. Locate "echo current WORKSPACE directory" line
2. After "cd %WORKSPACE%" line, insert:
   - "echo Install type stubs in project environment =="
   - "cd %WORKSPACE%\repo"
   - "uv sync --extra types"
   - blank line
3. Keep remaining template structure unchanged
```

## DATA

### Templates Summary

| Template | Platform | Change Type |
|----------|----------|-------------|
| `DEFAULT_TEST_COMMAND` | Linux | Replace `--extra dev` → `--extra types` |
| `CREATE_PLAN_COMMAND_TEMPLATE` | Linux | Replace `--extra dev` → `--extra types` |
| `IMPLEMENT_COMMAND_TEMPLATE` | Linux | Replace `--extra dev` → `--extra types` |
| `CREATE_PR_COMMAND_TEMPLATE` | Linux | Replace `--extra dev` → `--extra types` |
| `DEFAULT_TEST_COMMAND_WINDOWS` | Windows | Add `uv sync --extra types` block |
| `CREATE_PLAN_COMMAND_WINDOWS` | Windows | Add `uv sync --extra types` block |
| `IMPLEMENT_COMMAND_WINDOWS` | Windows | Add `uv sync --extra types` block |
| `CREATE_PR_COMMAND_WINDOWS` | Windows | Add `uv sync --extra types` block |

## Verification

### Unit Tests

Add/update tests in `tests/cli/commands/coordinator/test_commands.py`:

```python
def test_linux_templates_use_types_extra():
    """Verify Linux templates use --extra types instead of --extra dev."""
    from mcp_coder.cli.commands.coordinator.command_templates import (
        DEFAULT_TEST_COMMAND,
        CREATE_PLAN_COMMAND_TEMPLATE,
        IMPLEMENT_COMMAND_TEMPLATE,
        CREATE_PR_COMMAND_TEMPLATE,
    )
    
    linux_templates = [
        DEFAULT_TEST_COMMAND,
        CREATE_PLAN_COMMAND_TEMPLATE,
        IMPLEMENT_COMMAND_TEMPLATE,
        CREATE_PR_COMMAND_TEMPLATE,
    ]
    
    for template in linux_templates:
        assert "uv sync --extra types" in template
        assert "uv sync --extra dev" not in template


def test_windows_templates_install_type_stubs():
    """Verify Windows templates include type stub installation."""
    from mcp_coder.cli.commands.coordinator.command_templates import (
        DEFAULT_TEST_COMMAND_WINDOWS,
        CREATE_PLAN_COMMAND_WINDOWS,
        IMPLEMENT_COMMAND_WINDOWS,
        CREATE_PR_COMMAND_WINDOWS,
    )
    
    windows_templates = [
        DEFAULT_TEST_COMMAND_WINDOWS,
        CREATE_PLAN_COMMAND_WINDOWS,
        IMPLEMENT_COMMAND_WINDOWS,
        CREATE_PR_COMMAND_WINDOWS,
    ]
    
    for template in windows_templates:
        assert "uv sync --extra types" in template
        assert "cd %WORKSPACE%\\repo" in template or "cd %WORKSPACE%/repo" in template
```

## Notes

- Windows templates use `%WORKSPACE%\repo` (backslash) for consistency with existing code
- The `uv sync` command is run in the project directory (`repo/`), not the execution environment
- After installing type stubs, the script returns to the execution environment (`VENV_BASE_DIR`)
