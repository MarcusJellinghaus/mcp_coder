# Step 6: Print Migration — Coordinator and vscodeclaude Commands

## LLM Prompt
> Read `pr_info/steps/summary.md` for full context. Implement Step 6: Migrate status/error print() calls in coordinator commands and vscodeclaude files. Keep data-producing prints (status tables) as-is. Run all three code quality checks after changes. Do a final grep for any remaining NOTICE references across the entire codebase and fix them.

## WHERE
- `src/mcp_coder/cli/commands/coordinator/commands.py` — migrate prints
- `tests/` — grep for any remaining `NOTICE` references and update

## WHAT

### 6a. Coordinator commands (`commands.py`)

**Import OUTPUT:**
```python
from ....utils.log_utils import OUTPUT
```

**`execute_coordinator_test()`** (~3 prints):
```python
# BEFORE
print(f"Created default config file at {config_path}")
print("Please update it with your Jenkins and repository information.")
print(output)  # format_job_output result

# AFTER
logger.log(OUTPUT, "Created default config file at %s", config_path)
logger.log(OUTPUT, "Please update it with your Jenkins and repository information.")
logger.log(OUTPUT, "%s", output)  # job output is status, not pipeable data
```

Error prints:
```python
# BEFORE
print(f"Error: {e}", file=sys.stderr)

# AFTER
logger.error("%s", e)
```

**`execute_coordinator_run()`** (~5 prints):
```python
# BEFORE
print(f"Created default config file at {config_path}")
print("Please update it with your Jenkins and repository information.")
print("No repositories configured in config file", file=sys.stderr)
print(f"Error: Failed to process issue #{issue['number']}: {e}", file=sys.stderr)
print(f"Error: {e}", file=sys.stderr)

# AFTER
logger.log(OUTPUT, "Created default config file at %s", config_path)
logger.log(OUTPUT, "Please update it with your Jenkins and repository information.")
logger.error("No repositories configured in config file")
logger.error("Failed to process issue #%s: %s", issue['number'], e)
logger.error("%s", e)
```

**`execute_coordinator_vscodeclaude()`** (~8 prints):
```python
# Config creation prints → logger.log(OUTPUT, ...)
# Error prints → logger.error()
# Summary prints → logger.log(OUTPUT, ...)
# Restarted session prints → logger.log(OUTPUT, ...)
# Intervention mode banner → logger.log(OUTPUT, ...)
```

The intervention mode banner in `_handle_intervention_mode()`:
```python
# BEFORE
print("\n" + "!" * 60)
print("INTERVENTION MODE - Automation disabled")
print("!" * 60)
print(f"Issue: #{args.issue}")
print(f"Branch: {branch_name or 'main'}")
print("!" * 60 + "\n")
print(f"Started intervention session: #{session['issue_number']}")

# AFTER
logger.log(OUTPUT, "!" * 60)
logger.log(OUTPUT, "INTERVENTION MODE - Automation disabled")
logger.log(OUTPUT, "!" * 60)
logger.log(OUTPUT, "Issue: #%s", args.issue)
logger.log(OUTPUT, "Branch: %s", branch_name or "main")
logger.log(OUTPUT, "!" * 60)
logger.log(OUTPUT, "Started intervention session: #%s", session['issue_number'])
```

**Keep as print():**
- `display_status_table()` in `vscodeclaude/status.py` — data output (tabulate table)

### 6b. Final NOTICE grep and cleanup

Search the entire codebase for remaining `NOTICE` references:
- Source files: `src/mcp_coder/`
- Test files: `tests/`
- Config/docs that reference the log level name

Common places to check:
- `tests/cli/test_main.py` — likely has `NOTICE` in test assertions
- `tests/cli/commands/test_check_branch_status.py` — may reference `NOTICE`
- Any test file importing `NOTICE` from `mcp_coder.utils`
- Comments or docstrings mentioning NOTICE

**Fix pattern:**
```python
# BEFORE (in tests)
from mcp_coder.utils import NOTICE
from mcp_coder.utils.log_utils import NOTICE

# AFTER
from mcp_coder.utils import OUTPUT
from mcp_coder.utils.log_utils import OUTPUT
```

### 6c. Verify completeness

After all changes:
1. Run `grep -r "NOTICE" src/ tests/` — should return zero results (except possibly in unrelated string content)
2. Run all three code quality checks
3. Verify no `import sys` left unused after print migrations

## DATA
- No new data structures

## HOW — Integration Points
- Same pattern as Step 5: `from ....utils.log_utils import OUTPUT` (4-level relative import for coordinator)
- `sys` import may become unnecessary in some files — remove if unused

## Commit Message
```
refactor(coordinator): migrate prints to logging, remove NOTICE refs

- Coordinator command prints → logger.log(OUTPUT, ...) / logger.error()
- vscodeclaude command prints → logging
- Remove all remaining NOTICE references across codebase
- Final cleanup pass for unused imports
```
