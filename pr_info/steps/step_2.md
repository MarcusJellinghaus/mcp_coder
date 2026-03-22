# Step 2: Update `templates.py` + `issues.py` + docstrings

> **Context**: Read `pr_info/steps/summary.md` for the full design. This step updates templates, the eligibility check, and docstrings in cleanup.py/__init__.py.

## 2a. Update `src/mcp_coder/workflows/vscodeclaude/templates.py`

**WHERE**: `src/mcp_coder/workflows/vscodeclaude/templates.py`

**WHAT**: Remove old templates, add new ones, update main script template.

### Remove

- `DISCUSSION_SECTION_WINDOWS` — replaced by `AUTOMATED_RESUME_SECTION_WINDOWS` / `INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS`
- `INTERACTIVE_SECTION_WINDOWS` — becomes dead code (no flow uses bare resume without command)

### Modify

- `AUTOMATED_SECTION_WINDOWS`: Change placeholder from `{initial_command}` to `{command}`. Keep step label but make it parameterized: `=== Step {step_number}: Automated Analysis ===`.

- `STARTUP_SCRIPT_WINDOWS`: Replace `{automated_section}\n\n{discussion_section}\n\n{interactive_section}` with single `{command_sections}` placeholder. The workspace.py code will build all sections and join them.

### Add three new templates

1. **`INTERACTIVE_ONLY_SECTION_WINDOWS`** — Single-command flow (no step labels, no session ID):
```bat
echo.
echo Running: {command} {issue_number}
echo.

claude "{command} {issue_number}"
```

2. **`AUTOMATED_RESUME_SECTION_WINDOWS`** — Middle commands in multi-command flow:
```bat
echo.
echo === Step {step_number}: Automated Session ===
echo Running: {command}
echo.

mcp-coder prompt "{command}" --session-id %SESSION_ID% --mcp-config .mcp.json --timeout {timeout}

if errorlevel 1 (
    echo.
    echo WARNING: Step {step_number} encountered an error.
    echo Continuing to next step...
    echo.
)
```

3. **`INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS`** — Last command in multi-command flow:
```bat
echo.
echo === Step {step_number}: Interactive Session ===
echo You can now interact with Claude directly.
echo The conversation context from previous steps is preserved.
echo.

claude --resume %SESSION_ID% "{command}"
```

### Delete unused Linux templates

Remove `STARTUP_SCRIPT_LINUX`, `AUTOMATED_SECTION_LINUX`, `INTERACTIVE_SECTION_LINUX`, and `INTERVENTION_SECTION_LINUX`. They are dead code (Linux raises `NotImplementedError` in `workspace.py`). Can be recreated when Linux support is implemented.

**DATA**: All templates are raw string constants. No functions or return values.

## 2b. Update `src/mcp_coder/workflows/vscodeclaude/issues.py`

**WHERE**: `src/mcp_coder/workflows/vscodeclaude/issues.py` — function `is_status_eligible_for_session()`

**WHAT**: Change eligibility check from `initial_command` to `commands`.

**ALGORITHM**:
```python
def is_status_eligible_for_session(status: str) -> bool:
    config = get_vscodeclaude_config(status)
    if config is None:
        return False
    return len(config.get("commands", [])) > 0
```

**HOW**: The function signature and return type are unchanged. Only the body changes (2 lines shorter).

Update the docstring to say "with commands" instead of "with non-null initial_command".

## 2c. Update docstrings in `cleanup.py` and `__init__.py`

**WHERE**:
- `src/mcp_coder/workflows/vscodeclaude/cleanup.py` — `get_stale_sessions()` docstring
- `src/mcp_coder/workflows/vscodeclaude/__init__.py` — module docstring

**WHAT**: Replace references to `initial_command` with `commands`:
- cleanup.py docstring: `"Ineligible (bot statuses or pr-created - no initial_command)"` → `"Ineligible (bot statuses or pr-created - no commands)"`
- __init__.py docstring: `"Sessions are created for issues at human_action statuses with initial_command"` → `"Sessions are created for issues at human_action statuses with commands"`
- __init__.py docstring: `"Eligible statuses: ..."` line — keep the same status list, just fix the criteria description

### Verification

Run eligibility tests to confirm the logic change works:
```
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-k", "test_issues"])
```

Note: `test_workspace.py` will fail at this point because workspace.py still references the old templates. That's expected — step 3 fixes it.
