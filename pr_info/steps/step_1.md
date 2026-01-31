# Step 1: Move Test Files and Delete Old Directory

## Context
See [summary.md](summary.md) for full context. This step moves all 13 vscodeclaude test files from `tests/utils/vscodeclaude/` to `tests/workflows/vscodeclaude/`.

## WHERE: File Paths

**Source directory:** `tests/utils/vscodeclaude/`
**Target directory:** `tests/workflows/vscodeclaude/`

## WHAT: Files to Move

All 13 files:
1. `__init__.py`
2. `test_cleanup.py`
3. `test_config.py`
4. `test_helpers.py`
5. `test_issues.py`
6. `test_orchestrator_compatibility.py`
7. `test_orchestrator_launch.py`
8. `test_orchestrator_regenerate.py`
9. `test_orchestrator_sessions.py`
10. `test_sessions.py`
11. `test_status.py`
12. `test_types.py`
13. `test_workspace.py`

## HOW: Using MCP Filesystem Tools

```
mcp__filesystem__move_file(
    source_path="tests/utils/vscodeclaude/<filename>",
    destination_path="tests/workflows/vscodeclaude/<filename>"
)
```

## ALGORITHM

```
1. For each file in tests/utils/vscodeclaude/:
   - Call mcp__filesystem__move_file(source, destination)
2. Verify tests/utils/vscodeclaude/ is empty
3. Delete tests/utils/vscodeclaude/ directory
4. Confirm tests/workflows/vscodeclaude/ contains all 13 files
```

## DATA: Expected Results

- 13 files moved successfully
- `tests/utils/vscodeclaude/` directory no longer exists
- `tests/workflows/vscodeclaude/` contains all test files

## Cleanup

Delete empty directory: `tests/utils/vscodeclaude/`

---

## LLM Prompt

```
Review pr_info/steps/summary.md and pr_info/steps/step_1.md.

Move all 13 test files from tests/utils/vscodeclaude/ to tests/workflows/vscodeclaude/ using mcp__filesystem__move_file.

Files to move:
- __init__.py
- test_cleanup.py
- test_config.py
- test_helpers.py
- test_issues.py
- test_orchestrator_compatibility.py
- test_orchestrator_launch.py
- test_orchestrator_regenerate.py
- test_orchestrator_sessions.py
- test_sessions.py
- test_status.py
- test_types.py
- test_workspace.py

After moving all files, delete the tests/utils/vscodeclaude/ directory.

Do not modify any file contents - this is a pure move operation.
```
