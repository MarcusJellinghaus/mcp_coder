# Step 5: Update Coordinator Templates

## LLM Prompt
```
Implement Step 5 from the MCP Config File Selection Support plan (see pr_info/steps/summary.md).

Update the coordinator command templates to include --mcp-config parameter with the Linux-specific configuration file path.

No tests needed for this step (templates are static strings).
Use MCP tools exclusively as per CLAUDE.md requirements.
```

## Objective
Hardcode `--mcp-config /workspace/repo/.mcp.linux.json` in coordinator command templates for Jenkins container environment.

## WHERE

**File to modify:**
- `src/mcp_coder/cli/commands/coordinator.py`

**Affected constants:**
- All command template strings that invoke mcp-coder

## WHAT

### Command Templates to Update

Based on the issue description, update templates that call mcp-coder commands:

```python
CREATE_PLAN_COMMAND_TEMPLATE = """..."""
IMPLEMENT_COMMAND_TEMPLATE = """..."""
CREATE_PR_COMMAND_TEMPLATE = """..."""
# Any other templates that invoke mcp-coder
```

### Pattern to Apply

Add `--mcp-config /workspace/repo/.mcp.linux.json` to mcp-coder command invocations.

## HOW

### Integration Points

1. **Locate command templates** in coordinator.py
2. **Find mcp-coder command lines** within templates
3. **Insert --mcp-config parameter** after other flags

### Template Structure
```python
# Before
"""mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir /workspace/repo"""

# After
"""mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir /workspace/repo --mcp-config /workspace/repo/.mcp.linux.json"""
```

## ALGORITHM

### For Each Command Template:
```
1. Read current template string
2. Locate mcp-coder command line(s)
3. Find position after --project-dir argument
4. Insert: --mcp-config /workspace/repo/.mcp.linux.json
5. Verify template formatting (no syntax errors)
```

## Implementation Details

### Expected Template Locations

**CREATE_PLAN_COMMAND_TEMPLATE:**
```python
CREATE_PLAN_COMMAND_TEMPLATE = """git checkout main
git pull
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir /workspace/repo --mcp-config /workspace/repo/.mcp.linux.json
"""
```

**IMPLEMENT_COMMAND_TEMPLATE:**
```python
IMPLEMENT_COMMAND_TEMPLATE = """git checkout -b {branch_name}
mcp-coder --log-level {log_level} implement {issue_number} --project-dir /workspace/repo --mcp-config /workspace/repo/.mcp.linux.json
"""
```

**CREATE_PR_COMMAND_TEMPLATE:**
```python
CREATE_PR_COMMAND_TEMPLATE = """mcp-coder --log-level {log_level} create-pr {issue_number} --project-dir /workspace/repo --mcp-config /workspace/repo/.mcp.linux.json
"""
```

### Rationale for Hardcoded Path

**Why `/workspace/repo/.mcp.linux.json`?**
- Jenkins container mounts repo at `/workspace/repo`
- Linux-specific config needed for container environment
- Different from local development (uses default `.mcp.json`)

**Why not make it configurable?**
- KISS principle - templates are for specific environment
- No use case for variable config path in Jenkins
- Reduces complexity and configuration drift

## DATA

### Input Data
```python
# Template variables (existing)
log_level: str
issue_number: str
branch_name: str
```

### Output Data
```python
# Formatted command strings (examples)
"mcp-coder --log-level INFO create-plan 161 --project-dir /workspace/repo --mcp-config /workspace/repo/.mcp.linux.json"
"mcp-coder --log-level DEBUG implement 161 --project-dir /workspace/repo --mcp-config /workspace/repo/.mcp.linux.json"
```

### No New Data Structures
- Just string modifications in existing templates

## Implementation Checklist

- [ ] Read coordinator.py to identify all command templates
- [ ] Update CREATE_PLAN_COMMAND_TEMPLATE
- [ ] Update IMPLEMENT_COMMAND_TEMPLATE
- [ ] Update CREATE_PR_COMMAND_TEMPLATE
- [ ] Update any other templates that invoke mcp-coder
- [ ] Verify template syntax (no format string errors)
- [ ] Run pylint/mypy to check for issues

## Validation

### Manual Verification
```python
# Test template formatting works
template = CREATE_PLAN_COMMAND_TEMPLATE
formatted = template.format(log_level="INFO", issue_number="123")
print(formatted)

# Verify --mcp-config appears in output
assert "--mcp-config /workspace/repo/.mcp.linux.json" in formatted
```

### No Automated Tests Needed
- Templates are static strings
- No conditional logic to test
- Verification happens at runtime in Jenkins

## Expected Result
- All coordinator templates include `--mcp-config /workspace/repo/.mcp.linux.json`
- Template formatting still works correctly
- No syntax errors introduced
- Code quality checks pass

## Notes

### Context: Jenkins Environment
These templates run in podman/Jenkins containers where:
- Repo is mounted at `/workspace/repo`
- Linux paths are required (not Windows)
- MCP config specifies Linux executables and paths

### Not Affected
These templates are for automation only. Local development commands still use default behavior (no --mcp-config needed).

## Verification Command
```bash
# Type check and lint
mypy src/mcp_coder/cli/commands/coordinator.py
pylint src/mcp_coder/cli/commands/coordinator.py
```
