# Step 1: Update Windows Templates

## Reference
See `pr_info/steps/summary.md` for full context.

## WHERE

**File to modify:** `src/mcp_coder/cli/commands/coordinator.py`

**Templates to update:**
- `DEFAULT_TEST_COMMAND_WINDOWS` (~line 45)
- `CREATE_PLAN_COMMAND_WINDOWS` (~line 80)
- `IMPLEMENT_COMMAND_WINDOWS` (~line 100)
- `CREATE_PR_COMMAND_WINDOWS` (~line 120)

**Test file:** `tests/cli/commands/test_coordinator.py`

## WHAT

### 1. `DEFAULT_TEST_COMMAND_WINDOWS`

**Add after "Tools in current environment" section:**
```batch
set DISABLE_AUTOUPDATER=1
```

**Add MCP verification steps after existing verification:**
```batch
mcp-coder --log-level {log_level} prompt "Which MCP server can you use?"
mcp-coder --log-level {log_level} prompt --timeout 300 "For testing, please create a file, edit it, read it to verify, delete it, and tell me whether these actions worked well with the MCP server." --project-dir %WORKSPACE%\repo --mcp-config .mcp.json
```

**Add at end:**
```batch
echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs
```

### 2. `CREATE_PLAN_COMMAND_WINDOWS`

**Add after virtual environment activation:**
```batch
set DISABLE_AUTOUPDATER=1
```

**Modify mcp-coder command to add `--update-labels`:**
```batch
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir %WORKSPACE%\\repo --mcp-config .mcp.json --update-labels
```

**Add at end:**
```batch
echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs
```

### 3. `IMPLEMENT_COMMAND_WINDOWS`

**Add after virtual environment activation:**
```batch
set DISABLE_AUTOUPDATER=1
```

**Modify mcp-coder command to add `--update-labels`:**
```batch
mcp-coder --log-level {log_level} implement --project-dir %WORKSPACE%\\repo --mcp-config .mcp.json --update-labels
```

**Add at end:**
```batch
echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs
```

### 4. `CREATE_PR_COMMAND_WINDOWS`

**Add after virtual environment activation:**
```batch
set DISABLE_AUTOUPDATER=1
```

**Modify mcp-coder command to add `--update-labels`:**
```batch
mcp-coder --log-level {log_level} create-pr --project-dir %WORKSPACE%\\repo --mcp-config .mcp.json --update-labels
```

**Add at end:**
```batch
echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs
```

## HOW

Direct string modification of template constants. No imports or integration points needed.

## TEST UPDATES

Update `tests/cli/commands/test_coordinator.py`:

### Test: `test_execute_coordinator_test_windows_template`

Add assertions:
```python
assert "set DISABLE_AUTOUPDATER=1" in command
assert "dir .mcp-coder" in command  # Archive listing
assert "mcp-coder --log-level" in command  # MCP verification with log_level placeholder
```

### Test: `test_dispatch_workflow_create_plan` (when executor_os=windows)

Add assertion:
```python
assert "--update-labels" in command
assert "set DISABLE_AUTOUPDATER=1" in command
```

### Tests for implement and create-pr workflows

Similar assertions for `--update-labels` and `DISABLE_AUTOUPDATER`.

## DATA

No new data structures. Template strings are modified in place.

---

## LLM Prompt for Step 1

```
Implement Step 1 from pr_info/steps/step_1.md

Context: See pr_info/steps/summary.md for the full issue context.

Task: Update the 4 Windows templates in src/mcp_coder/cli/commands/coordinator.py:
1. DEFAULT_TEST_COMMAND_WINDOWS - Add DISABLE_AUTOUPDATER, MCP verification steps, archive listing
2. CREATE_PLAN_COMMAND_WINDOWS - Add DISABLE_AUTOUPDATER, --update-labels flag, archive listing
3. IMPLEMENT_COMMAND_WINDOWS - Add DISABLE_AUTOUPDATER, --update-labels flag, archive listing  
4. CREATE_PR_COMMAND_WINDOWS - Add DISABLE_AUTOUPDATER, --update-labels flag, archive listing

Then update tests in tests/cli/commands/test_coordinator.py to verify the new template content.

Run all code quality checks after changes.
```
