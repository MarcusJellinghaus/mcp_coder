# Step 2: Revert CLI command files — `logger.log(NOTICE, ...)` → `logger.info(...)`

> **Context**: See `pr_info/steps/summary.md` for full issue context.

## Goal

Revert all `logger.log(NOTICE, ...)` calls to `logger.info(...)` in CLI command files, and remove the now-unused `NOTICE` imports.

## WHERE (7 files)

- `src/mcp_coder/cli/commands/check_branch_status.py` — 7 calls
- `src/mcp_coder/cli/commands/define_labels.py` — 4 calls
- `src/mcp_coder/cli/commands/prompt.py` — 3 calls
- `src/mcp_coder/cli/commands/set_status.py` — 1 call
- `src/mcp_coder/cli/commands/coordinator/commands.py` — 2 calls
- `src/mcp_coder/cli/commands/coordinator/core.py` — 4 calls
- `src/mcp_coder/cli/commands/coordinator/issue_stats.py` — 1 call

## WHAT

For each file:
1. Replace every `logger.log(NOTICE, ...)` with `logger.info(...)`
2. Remove `NOTICE` from the import line (remove entire import if NOTICE was the only import from that module)

## HOW

### Pattern A — `logger.log(NOTICE, "message")` → `logger.info("message")`

```python
# BEFORE:
logger.log(NOTICE, "Processing %s", item)

# AFTER:
logger.info("Processing %s", item)
```

### Pattern B — Import cleanup

```python
# BEFORE (NOTICE is only import):
from ...utils.log_utils import NOTICE

# AFTER:
# (line removed entirely)

# BEFORE (NOTICE alongside other imports):
from ...utils.log_utils import NOTICE, log_function_call

# AFTER:
from ...utils.log_utils import log_function_call
```

## ALGORITHM (per file)

```
1. Read file
2. Find import line containing NOTICE
3. Remove NOTICE from import (or remove line if sole import)
4. Find all logger.log(NOTICE, ...) calls
5. Replace each with logger.info(...)
6. Save file
```

## DATA

No data structure changes. Only the log level of emitted messages changes (NOTICE→INFO).

## Verification

After all 7 files are edited, run:
1. `mcp__tools-py__run_pylint_check`
2. `mcp__tools-py__run_mypy_check`
3. `mcp__tools-py__run_pytest_check` with `extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`

All checks must pass. Then commit.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for full context.

Implement Step 2: Revert CLI command files from NOTICE logging to INFO logging.

For each of the 7 CLI command files listed in step_2.md:
1. Read the file
2. Replace all logger.log(NOTICE, ...) calls with logger.info(...)
3. Remove the NOTICE import (remove from import line, or remove entire line if sole import)
4. Save the file

Files to edit:
- src/mcp_coder/cli/commands/check_branch_status.py (7 calls)
- src/mcp_coder/cli/commands/define_labels.py (4 calls)
- src/mcp_coder/cli/commands/prompt.py (3 calls)
- src/mcp_coder/cli/commands/set_status.py (1 call)
- src/mcp_coder/cli/commands/coordinator/commands.py (2 calls)
- src/mcp_coder/cli/commands/coordinator/core.py (4 calls)
- src/mcp_coder/cli/commands/coordinator/issue_stats.py (1 call)

After all edits, run all three code quality checks (pylint, mypy, pytest). Fix any issues.

Commit with message: "Revert CLI commands from NOTICE logging to INFO logging"
```
