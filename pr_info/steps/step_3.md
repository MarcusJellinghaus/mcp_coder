# Step 3: Revert workflow files + remove unused NOTICE imports

> **Context**: See `pr_info/steps/summary.md` for full issue context.

## Goal

Revert all `logger.log(NOTICE, ...)` calls to `logger.info(...)` in workflow files, remove NOTICE imports from those files, and remove unused NOTICE imports from 4 additional files.

## WHERE (12 files)

### Workflow files with log call reverts (8 files):

- `src/mcp_coder/workflows/create_plan.py` — 18 calls
- `src/mcp_coder/workflows/create_pr/core.py` — 8 calls
- `src/mcp_coder/workflows/implement/core.py` — 18 calls
- `src/mcp_coder/workflows/implement/prerequisites.py` — 1 call
- `src/mcp_coder/workflows/implement/task_processing.py` — 4 calls
- `src/mcp_coder/workflows/vscodeclaude/cleanup.py` — 2 calls
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` — 3 calls

### Files with unused NOTICE import only (4 files):

- `src/mcp_coder/utils/github_operations/issues/branch_manager.py`
- `src/mcp_coder/utils/github_operations/issues/manager.py`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py`
- `src/mcp_coder/workflows/vscodeclaude/session_restart.py`

## WHAT

Same patterns as Step 2:
1. Replace every `logger.log(NOTICE, ...)` with `logger.info(...)`
2. Remove `NOTICE` from import lines
3. For the 4 unused-import-only files, just remove `NOTICE` from the import line

## HOW

Identical to Step 2 patterns:

```python
# Log call revert:
logger.log(NOTICE, "message", arg)  →  logger.info("message", arg)

# Import cleanup:
from mcp_coder.utils.log_utils import NOTICE  →  (remove line)
from mcp_coder.utils.log_utils import NOTICE, log_function_call  →  from mcp_coder.utils.log_utils import log_function_call
```

## ALGORITHM (per file)

```
1. Read file
2. Find import line containing NOTICE
3. Remove NOTICE from import (or remove line if sole import)
4. Find all logger.log(NOTICE, ...) calls (if any)
5. Replace each with logger.info(...)
6. Save file
```

## DATA

No data structure changes. Only the log level of emitted messages changes (NOTICE→INFO).

## Verification

After all 12 files are edited, run:
1. `mcp__tools-py__run_pylint_check`
2. `mcp__tools-py__run_mypy_check`
3. `mcp__tools-py__run_pytest_check` with `extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`

All checks must pass. Then commit.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for full context.

Implement Step 3: Revert workflow files from NOTICE logging to INFO logging, and remove unused NOTICE imports.

For each of the 8 workflow files listed in step_3.md:
1. Read the file
2. Replace all logger.log(NOTICE, ...) calls with logger.info(...)
3. Remove the NOTICE import
4. Save the file

For each of the 4 unused-import-only files:
1. Read the file
2. Remove NOTICE from the import line (or remove entire line if sole import)
3. Save the file

Files with log call reverts:
- src/mcp_coder/workflows/create_plan.py (18 calls)
- src/mcp_coder/workflows/create_pr/core.py (8 calls)
- src/mcp_coder/workflows/implement/core.py (18 calls)
- src/mcp_coder/workflows/implement/prerequisites.py (1 call)
- src/mcp_coder/workflows/implement/task_processing.py (4 calls)
- src/mcp_coder/workflows/vscodeclaude/cleanup.py (2 calls)
- src/mcp_coder/workflows/vscodeclaude/workspace.py (3 calls)

Files with unused import removal only:
- src/mcp_coder/utils/github_operations/issues/branch_manager.py
- src/mcp_coder/utils/github_operations/issues/manager.py
- src/mcp_coder/workflows/vscodeclaude/session_launch.py
- src/mcp_coder/workflows/vscodeclaude/session_restart.py

After all edits, run all three code quality checks (pylint, mypy, pytest). Fix any issues.

Commit with message: "Revert workflow files from NOTICE logging to INFO, remove unused NOTICE imports"
```
