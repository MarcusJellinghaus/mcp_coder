# Step 4: Update Documentation

## Objective
Update documentation to reflect new `--ci-timeout` and `--fix [N]` parameters.

## Context
Read `pr_info/steps/summary.md` first for full context.

This step updates:
- Slash command default behavior
- CLI reference documentation
- Usage examples
- Exit code documentation

**Prerequisites**: Steps 1-3 must be complete (full implementation).

## WHERE: File Locations

### Documentation Files
```
.claude/commands/check_branch_status.md
  - Update command to use --ci-timeout 180
  - Add usage examples

docs/cli-reference.md
  - Document --ci-timeout parameter
  - Document --fix [N] enhancement
  - Add exit code table
  - Add usage examples
```

## WHAT: Documentation Updates

### Slash Command File
```markdown
.claude/commands/check_branch_status.md
  - Change command from:
    mcp-coder check branch-status --llm-truncate
  - To:
    mcp-coder check branch-status --ci-timeout 180 --llm-truncate
  - Add examples section
  - Document retry behavior
```

### CLI Reference File
```markdown
docs/cli-reference.md
  - Add --ci-timeout parameter documentation
  - Update --fix parameter documentation
  - Add exit codes table
  - Add comprehensive usage examples
  - Add workflow integration examples
```

## HOW: Documentation Structure

### Slash Command Update
```markdown
## Usage

Call the underlying CLI command with LLM-optimized output and CI waiting:

```bash
mcp-coder check branch-status --ci-timeout 180 --llm-truncate
```

## What This Command Does

1. **Wait for CI**: Polls for up to 3 minutes for CI completion
2. **CI Status Check**: Analyzes latest workflow run and retrieves error logs
3. **Rebase Detection**: Checks if branch needs rebasing onto main
4. **Task Validation**: Verifies all implementation tasks are complete
5. **GitHub Labels**: Reports current workflow status label
6. **Recommendations**: Provides actionable next steps

## Options

- `--ci-timeout 180` - Wait up to 3 minutes for CI to complete
- `--llm-truncate` - LLM-friendly output format
- `--fix` - Auto-fix CI failures (single attempt)
- `--fix N` - Auto-fix with up to N retry attempts

## Examples

### Just check and wait
```bash
mcp-coder check branch-status --ci-timeout 180 --llm-truncate
```

### Check, wait, and auto-fix once
```bash
mcp-coder check branch-status --ci-timeout 180 --llm-truncate --fix
```

### Check, wait, and retry fixes up to 3 times
```bash
mcp-coder check branch-status --ci-timeout 300 --llm-truncate --fix 3
```
```

### CLI Reference Addition
```markdown
## check branch-status

Check comprehensive branch readiness including CI status, rebase requirements, task completion, and GitHub labels.

### Synopsis

```bash
mcp-coder check branch-status [OPTIONS]
```

### Options

- `--project-dir PATH` - Project directory path (default: current directory)
- `--ci-timeout SECONDS` - Wait up to N seconds for CI completion (default: 0 = no wait)
- `--fix [N]` - Fix issues up to N times (default: 0 = no fix, --fix alone = 1)
- `--llm-truncate` - Truncate output for LLM consumption
- `--llm-method METHOD` - LLM method for --fix (claude_code_cli or claude_code_api)
- `--mcp-config PATH` - Path to MCP configuration file
- `--execution-dir PATH` - Working directory for Claude subprocess

### Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | CI passed or graceful exit (no CI configured, API errors) |
| 1 | Failure | CI failed, timeout, or pending status |
| 2 | Error | Technical error (invalid arguments, Git errors) |

### Behavior

#### Without --ci-timeout (Current Behavior)
Performs immediate snapshot check of current CI status without waiting.

#### With --ci-timeout (New)
Polls CI status every 15 seconds until completion or timeout:
- Early exits when CI completes (success or failure)
- Shows progress dots in human mode
- Silent polling in LLM mode (--llm-truncate)
- Returns current status on timeout

#### Without --fix (Read-Only)
Only checks and reports status, no automated fixes attempted.

#### With --fix (Single Fix, Current Behavior Preserved)
Attempts to fix CI failures once, no recheck after fix.

#### With --fix N (Retry Fixes, New)
Attempts to fix CI failures up to N times:
- Waits for CI after each fix attempt
- Stops early if CI passes
- Shows attempt progress ("Fix attempt 2/3...")

### Examples

#### Quick status check
```bash
mcp-coder check branch-status
```

#### Wait for CI to complete (no fixing)
```bash
mcp-coder check branch-status --ci-timeout 300
```

#### Wait and auto-fix once
```bash
mcp-coder check branch-status --ci-timeout 180 --fix
```

#### Wait and retry fixes up to 3 times
```bash
mcp-coder check branch-status --ci-timeout 180 --fix 3
```

#### LLM-optimized with waiting
```bash
mcp-coder check branch-status --ci-timeout 300 --llm-truncate
```

#### Scripting example
```bash
#!/bin/bash
if mcp-coder check branch-status --ci-timeout 300; then
  echo "CI passed, ready to merge"
  exit 0
else
  echo "CI failed or timed out"
  exit 1
fi
```

### Workflow Integration

#### Manual Development Flow
```bash
# 1. Check status and wait for CI
mcp-coder check branch-status --ci-timeout 180

# 2. If CI fails, auto-fix with retry
mcp-coder check branch-status --ci-timeout 180 --fix 3

# 3. If passes, create PR
mcp-coder create-pr
```

#### Automated Script Flow
```bash
# Wait for CI, fix if needed, exit with appropriate code
mcp-coder check branch-status --ci-timeout 300 --fix 2
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "✓ Branch ready"
  # Continue with PR creation or merge
elif [ $EXIT_CODE -eq 1 ]; then
  echo "✗ CI failed after fixes"
  # Notify team or create issue
else
  echo "✗ Technical error"
  # Alert on configuration/Git issues
fi
```

### Notes

- **Polling Strategy**: Fixed 15-second intervals, no maximum timeout limit
- **Early Exit**: Stops immediately when CI completes (success or failure)
- **API Errors**: Treated as graceful exit (code 0) to avoid blocking workflows
- **No CI Configured**: Returns code 0 (graceful exit)
- **Progress Feedback**: Controlled by --llm-truncate (dots in human mode, silent in LLM mode)
```

## DATA: Documentation Content

### Key Information to Include

#### Parameter Descriptions
```
--ci-timeout SECONDS
  Default: 0 (no wait)
  Range: 0 to unlimited (trust user)
  Behavior: Poll every 15s until completion or timeout
  
--fix [N]
  Default: 0 (no fix)
  Values:
    - Not provided or 0: No fixing
    - --fix or --fix 1: Fix once, no recheck
    - --fix N (N ≥ 2): Fix up to N times with rechecks
```

#### Exit Code Table
```
0 = Success (CI passed) or Graceful Exit (no CI, API errors)
1 = Failure (CI failed, timeout, pending)
2 = Technical Error (invalid args, Git errors)
```

#### Polling Behavior
```
- Interval: 15 seconds
- Early exit: On completion (success or failure)
- Timeout: Returns current status with code 1
- No CI: Returns code 0 (graceful)
- API errors: Returns code 0 (graceful)
```

#### Retry Behavior
```
fix_attempts=1:
  - Fix once
  - No recheck (backward compatible)

fix_attempts≥2:
  - Fix → Wait for new CI run → Wait for completion → Check result
  - Early exit if CI passes
  - Continue until all attempts exhausted
  - Always wait after last fix to know final status
```

## Implementation Details

### File 1: `.claude/commands/check_branch_status.md`

#### Update Command Line
Find:
```bash
mcp-coder check branch-status --llm-truncate
```

Replace with:
```bash
mcp-coder check branch-status --ci-timeout 180 --llm-truncate
```

#### Add Examples Section
Add after "What This Command Does":
```markdown
## Options

- `--ci-timeout 180` - Wait up to 3 minutes for CI to complete
- `--llm-truncate` - LLM-friendly output format
- `--fix` - Auto-fix CI failures (single attempt)
- `--fix N` - Auto-fix with up to N retry attempts

## Examples

### Just check and wait (recommended for LLM)
```bash
mcp-coder check branch-status --ci-timeout 180 --llm-truncate
```

### Check, wait, and auto-fix once
```bash
mcp-coder check branch-status --ci-timeout 180 --llm-truncate --fix
```

### Check, wait, and retry fixes up to 3 times
```bash
mcp-coder check branch-status --ci-timeout 300 --llm-truncate --fix 3
```

### Quick check without waiting (old behavior)
```bash
mcp-coder check branch-status --llm-truncate
```
```

#### Update Rationale Section
Find:
```markdown
**Rationale**: LLM-driven context benefits from waiting for complete results.
```

Update to:
```markdown
**Rationale**: LLM-driven context benefits from waiting for complete results. The 180-second timeout provides a balance between responsiveness and allowing typical CI runs to complete. No `--fix` by default to let LLM analyze failures and suggest targeted fixes.
```

### File 2: `docs/cli-reference.md`

#### Find check branch-status Section

Locate the existing `check branch-status` section and completely replace it with the comprehensive documentation shown in the "CLI Reference Addition" section above.

## Validation Criteria

### Documentation Quality
- ✅ All parameters documented clearly
- ✅ Exit codes table included
- ✅ Usage examples cover all scenarios
- ✅ Backward compatibility mentioned
- ✅ Scripting examples included

### Accuracy
- ✅ Default values correct
- ✅ Behavior descriptions match implementation
- ✅ Examples tested and working

### Completeness
- ✅ Slash command updated
- ✅ CLI reference updated
- ✅ Examples for common use cases
- ✅ Integration guidance provided

## LLM Implementation Prompt

```
Please read pr_info/steps/summary.md for full context.

Implement Step 4: Update Documentation

TASK:
1. Update .claude/commands/check_branch_status.md:
   - Change command to use --ci-timeout 180
   - Add Options section documenting new parameters
   - Add Examples section with 4 examples
   - Update rationale

2. Update docs/cli-reference.md:
   - Find the "check branch-status" section
   - Replace with comprehensive documentation including:
     * Synopsis
     * Options (all parameters)
     * Exit Codes table
     * Behavior section (4 scenarios)
     * Examples (6 examples)
     * Workflow Integration (2 examples)
     * Notes section

3. Follow the implementation details in pr_info/steps/step_4.md exactly

VERIFICATION:
1. Read both updated files
2. Verify all examples are accurate
3. Verify exit codes match implementation (0/1/2)
4. Verify default values are correct

Success criteria:
- Both files updated completely
- All examples accurate and tested
- Documentation clear and comprehensive
```

## Dependencies
- Steps 1-3 must be complete (full implementation)

## Next Step
After this step completes successfully, the implementation is complete. Proceed to final testing and verification.

## Manual Verification

```bash
# Test all documented examples work
mcp-coder check branch-status
mcp-coder check branch-status --ci-timeout 180
mcp-coder check branch-status --ci-timeout 180 --fix
mcp-coder check branch-status --ci-timeout 180 --fix 3
mcp-coder check branch-status --ci-timeout 300 --llm-truncate

# Verify help text matches documentation
mcp-coder check branch-status --help

# Test exit codes
mcp-coder check branch-status --ci-timeout 60
echo $?  # Should be 0 or 1 based on CI status
```
