# Summary: Split test files for vscodeclaude orchestrator (#463)

## Overview

Rename and restructure orchestrator test files to mirror the source structure created in #458, where `orchestrator.py` was split into `session_launch.py`, `session_restart.py`, and `issues.py`.

## Architectural / Design Changes

**No architectural changes.** This is a pure test file restructuring:

- **Source code**: Unchanged. The source split (`session_launch.py`, `session_restart.py`, `issues.py`) was completed in #458.
- **Test structure**: Test files are renamed/split to mirror source modules. No test logic changes.
- **Imports**: Already updated in #458 to point to new source locations. Each new test file gets the subset of imports its class needs.
- **One class rename**: `TestOrchestration` → `TestSessionRestart` (name alignment only).

### Before → After mapping

| Source module | Old test file | New test file |
|---|---|---|
| `session_launch.py` | `test_orchestrator_launch.py` | `test_session_launch.py` |
| `session_launch.py` | `test_orchestrator_regenerate.py` | `test_session_launch_regenerate.py` |
| `session_launch.py` | `test_orchestrator_launch_process_issues.py` | `test_session_launch_process_issues.py` |
| `session_restart.py` | `test_orchestrator_sessions.py` (TestOrchestration) | `test_session_restart.py` |
| `session_restart.py` | `test_orchestrator_sessions.py` (TestPrepareRestartBranch) | `test_session_restart_prepare_branch.py` |
| `session_restart.py` | `test_orchestrator_sessions.py` (TestRestartClosedSessionsBranchHandling) | `test_session_restart_closed_sessions.py` |
| `session_restart.py` | `test_orchestrator_sessions.py` (TestBranchHandlingIntegration) | `test_session_restart_branch_integration.py` |
| `session_restart.py` | `test_orchestrator_cache.py` | `test_session_restart_cache.py` |
| `issues.py` | `test_orchestrator_documentation.py` | `test_issues_branch_requirements.py` |

## Files modified

| File | Action |
|---|---|
| `tests/workflows/vscodeclaude/test_orchestrator_launch.py` | Rename → `test_session_launch.py` |
| `tests/workflows/vscodeclaude/test_orchestrator_regenerate.py` | Rename → `test_session_launch_regenerate.py` |
| `tests/workflows/vscodeclaude/test_orchestrator_launch_process_issues.py` | Rename → `test_session_launch_process_issues.py` |
| `tests/workflows/vscodeclaude/test_orchestrator_cache.py` | Rename → `test_session_restart_cache.py` |
| `tests/workflows/vscodeclaude/test_orchestrator_documentation.py` | Rename → `test_issues_branch_requirements.py` |
| `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` | Split into 4 files, then delete |
| `tests/workflows/vscodeclaude/test_session_restart.py` | Create (from TestOrchestration class) |
| `tests/workflows/vscodeclaude/test_session_restart_prepare_branch.py` | Create (from TestPrepareRestartBranch class) |
| `tests/workflows/vscodeclaude/test_session_restart_closed_sessions.py` | Create (from TestRestartClosedSessionsBranchHandling class) |
| `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py` | Create (from TestBranchHandlingIntegration class) |
| `.large-files-allowlist` | Remove `test_orchestrator_sessions.py` entry |

## Constraints

- **Move, don't change**: Tests are moved as-is, no logic changes.
- **Only adjust imports and class names**: Per refactoring guide.
- **750-line threshold**: All resulting files must be under 750 lines, except `test_session_restart.py` (~980 lines) which is added to `.large-files-allowlist` (further splitting is a separate issue).
- **No duplicates**: Original files deleted after move.

## Implementation steps

- **Step 1**: Rename 5 simple test files (no content changes)
- **Step 2**: Split `test_orchestrator_sessions.py` into 4 files, delete original, update allowlist
