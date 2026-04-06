# Step 2: Split test_orchestrator_sessions.py into 4 files

## References
- [Summary](./summary.md)
- Issue #463

## Goal
Split `test_orchestrator_sessions.py` (~2,253 lines, 4 classes) into 4 separate test files — one per class. Delete the original. Update `.large-files-allowlist`.

## WHERE — File operations

Source: `tests/workflows/vscodeclaude/test_orchestrator_sessions.py`

| Class in source | Target file | Class rename? |
|---|---|---|
| `TestOrchestration` (~955 lines) | `test_session_restart.py` | Yes → `TestSessionRestart` |
| `TestPrepareRestartBranch` (~253 lines) | `test_session_restart_prepare_branch.py` | No |
| `TestRestartClosedSessionsBranchHandling` (~562 lines) | `test_session_restart_closed_sessions.py` | No |
| `TestBranchHandlingIntegration` (~456 lines) | `test_session_restart_branch_integration.py` | No |

Also modify: `.large-files-allowlist` — remove `test_orchestrator_sessions.py`, add `test_session_restart.py`

## WHAT — Operations per new file
- Module docstring
- Import block (subset of original file's imports needed by that class)
- The class copied verbatim (except `TestOrchestration` → `TestSessionRestart`)
- No logic changes

## HOW — Integration
- Each new file is a standalone pytest module
- Imports come from `mcp_coder.workflows.vscodeclaude.session_restart` (and related modules)
- conftest.py fixtures remain shared via `tests/workflows/vscodeclaude/conftest.py`

## ALGORITHM
```
read test_orchestrator_sessions.py
identify import block and 4 class boundaries
for each class:
    create new file with: docstring + needed imports + class body
    if class is TestOrchestration: rename to TestSessionRestart
delete test_orchestrator_sessions.py
update .large-files-allowlist: remove test_orchestrator_sessions.py, add test_session_restart.py
run_checks()  # all code quality checks per CLAUDE.md
```

## DATA — Expected result
- 4 new files (3 under 750 lines; `test_session_restart.py` ~980 lines, added to allowlist)
- 0 original orchestrator test files remaining
- All tests pass (same count as before)

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for context.

Split tests/workflows/vscodeclaude/test_orchestrator_sessions.py into 4 files, one per class:

1. TestOrchestration → test_session_restart.py (rename class to TestSessionRestart)
2. TestPrepareRestartBranch → test_session_restart_prepare_branch.py
3. TestRestartClosedSessionsBranchHandling → test_session_restart_closed_sessions.py
4. TestBranchHandlingIntegration → test_session_restart_branch_integration.py

For each new file:
- Add the module docstring
- Include only the imports needed by that class
- Copy the class verbatim (only rename TestOrchestration → TestSessionRestart)
- No logic changes

After creating all 4 files:
- Delete test_orchestrator_sessions.py
- Update `.large-files-allowlist`: remove `test_orchestrator_sessions.py`, add `test_session_restart.py` (~980 lines with imports, further splitting is a separate issue)

Run format_code before committing. Run all code quality checks per CLAUDE.md (pytest, pylint, mypy, lint_imports, vulture, ruff, format_code). All checks must pass.
```
