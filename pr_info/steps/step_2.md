# Step 2: Update Linux Templates

## Reference
See `pr_info/steps/summary.md` for full context.

## WHERE

**File to modify:** `src/mcp_coder/cli/commands/coordinator.py`

**Templates to update:**
- `DEFAULT_TEST_COMMAND` (~line 25)
- `CREATE_PLAN_COMMAND_TEMPLATE` (~line 145)
- `IMPLEMENT_COMMAND_TEMPLATE` (~line 155)
- `CREATE_PR_COMMAND_TEMPLATE` (~line 165)

**Test file:** `tests/cli/commands/test_coordinator.py`

## WHAT

### 1. `DEFAULT_TEST_COMMAND`

**Add near the start (after tool verification):**
```bash
export DISABLE_AUTOUPDATER=1
```

**Add MCP verification steps:**
```bash
claude --mcp-config .mcp.json --strict-mcp-config mcp list
claude --mcp-config .mcp.json --strict-mcp-config -p "What is 1 + 1?"
mcp-coder --log-level {log_level} prompt "Which MCP server can you use?"
mcp-coder --log-level {log_level} prompt --timeout 300 "For testing, please create a file, edit it, read it to verify, delete it, and tell me whether these actions worked well with the MCP server." --project-dir /workspace/repo --mcp-config .mcp.json
```

**Add at end:**
```bash
echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs
```

### 2. `CREATE_PLAN_COMMAND_TEMPLATE`

**Add after git pull:**
```bash
export DISABLE_AUTOUPDATER=1
```

**Change `.mcp.linux.json` to `.mcp.json`**

**Add `--update-labels` flag:**
```bash
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir /workspace/repo --mcp-config .mcp.json --update-labels
```

**Add at end:**
```bash
echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs
```

### 3. `IMPLEMENT_COMMAND_TEMPLATE`

**Add after git pull:**
```bash
export DISABLE_AUTOUPDATER=1
```

**Change `.mcp.linux.json` to `.mcp.json`**

**Add `--update-labels` flag:**
```bash
mcp-coder --log-level {log_level} implement --project-dir /workspace/repo --mcp-config .mcp.json --update-labels
```

**Add at end:**
```bash
echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs
```

### 4. `CREATE_PR_COMMAND_TEMPLATE`

**Add after git pull:**
```bash
export DISABLE_AUTOUPDATER=1
```

**Change `.mcp.linux.json` to `.mcp.json`**

**Add `--update-labels` flag:**
```bash
mcp-coder --log-level {log_level} create-pr --project-dir /workspace/repo --mcp-config .mcp.json --update-labels
```

**Add at end:**
```bash
echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs
```

## HOW

Direct string modification of template constants. No imports or integration points needed.

## TEST UPDATES

Update `tests/cli/commands/test_coordinator.py`:

### Test: `test_execute_coordinator_test_uses_default_test_command`

Add assertions:
```python
assert "export DISABLE_AUTOUPDATER=1" in command
assert "ls -la .mcp-coder" in command  # Archive listing
```

### Test: `test_dispatch_workflow_create_plan`

Update assertion to check for `.mcp.json` (not `.mcp.linux.json`):
```python
assert ".mcp.json" in command
assert "--update-labels" in command
assert "export DISABLE_AUTOUPDATER=1" in command
```

### Test: `test_dispatch_workflow_implement`

Add assertions:
```python
assert ".mcp.json" in command
assert "--update-labels" in command
assert "export DISABLE_AUTOUPDATER=1" in command
```

### Test: `test_dispatch_workflow_create_pr`

Add assertions:
```python
assert ".mcp.json" in command
assert "--update-labels" in command
assert "export DISABLE_AUTOUPDATER=1" in command
```

## DATA

No new data structures. Template strings are modified in place.

---

## LLM Prompt for Step 2

```
Implement Step 2 from pr_info/steps/step_2.md

Context: See pr_info/steps/summary.md for the full issue context.

Task: Update the 4 Linux templates in src/mcp_coder/cli/commands/coordinator.py:
1. DEFAULT_TEST_COMMAND - Add DISABLE_AUTOUPDATER, MCP verification steps, archive listing
2. CREATE_PLAN_COMMAND_TEMPLATE - Add DISABLE_AUTOUPDATER, --update-labels flag, change .mcp.linux.json to .mcp.json, archive listing
3. IMPLEMENT_COMMAND_TEMPLATE - Add DISABLE_AUTOUPDATER, --update-labels flag, change .mcp.linux.json to .mcp.json, archive listing
4. CREATE_PR_COMMAND_TEMPLATE - Add DISABLE_AUTOUPDATER, --update-labels flag, change .mcp.linux.json to .mcp.json, archive listing

Then update tests in tests/cli/commands/test_coordinator.py to verify the new template content.

Run all code quality checks after changes.
```
