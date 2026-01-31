# Issue #363: Move vscodeclaude Tests to Mirror New Source Structure

## Overview

Pure file reorganization to align test directory structure with source code structure after issue #358 moved source from `utils/` to `workflows/`.

## Architectural / Design Changes

**None.** This is a pure file move operation with no code changes:
- No new modules or classes
- No API changes
- No import path changes (already updated in #358)
- No logic modifications

## Directory Structure Change

```
BEFORE:
tests/
├── utils/
│   └── vscodeclaude/        # ← Tests here (wrong location)
│       ├── __init__.py
│       └── test_*.py (12 files)
└── workflows/
    └── (other test files)

AFTER:
tests/
├── utils/
│   └── (vscodeclaude/ deleted)
└── workflows/
    └── vscodeclaude/        # ← Tests here (mirrors source)
        ├── __init__.py
        └── test_*.py (12 files)
```

## Files to Move

| From | To |
|------|-----|
| `tests/utils/vscodeclaude/__init__.py` | `tests/workflows/vscodeclaude/__init__.py` |
| `tests/utils/vscodeclaude/test_cleanup.py` | `tests/workflows/vscodeclaude/test_cleanup.py` |
| `tests/utils/vscodeclaude/test_config.py` | `tests/workflows/vscodeclaude/test_config.py` |
| `tests/utils/vscodeclaude/test_helpers.py` | `tests/workflows/vscodeclaude/test_helpers.py` |
| `tests/utils/vscodeclaude/test_issues.py` | `tests/workflows/vscodeclaude/test_issues.py` |
| `tests/utils/vscodeclaude/test_orchestrator_compatibility.py` | `tests/workflows/vscodeclaude/test_orchestrator_compatibility.py` |
| `tests/utils/vscodeclaude/test_orchestrator_launch.py` | `tests/workflows/vscodeclaude/test_orchestrator_launch.py` |
| `tests/utils/vscodeclaude/test_orchestrator_regenerate.py` | `tests/workflows/vscodeclaude/test_orchestrator_regenerate.py` |
| `tests/utils/vscodeclaude/test_orchestrator_sessions.py` | `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` |
| `tests/utils/vscodeclaude/test_sessions.py` | `tests/workflows/vscodeclaude/test_sessions.py` |
| `tests/utils/vscodeclaude/test_status.py` | `tests/workflows/vscodeclaude/test_status.py` |
| `tests/utils/vscodeclaude/test_types.py` | `tests/workflows/vscodeclaude/test_types.py` |
| `tests/utils/vscodeclaude/test_workspace.py` | `tests/workflows/vscodeclaude/test_workspace.py` |

## Folders to Delete

- `tests/utils/vscodeclaude/` (entire directory after files moved)

## Folders to Create

- `tests/workflows/vscodeclaude/` (created automatically by move operation)

## Acceptance Criteria

- [x] Directory `tests/workflows/vscodeclaude/` created
- [x] All 13 test files moved
- [x] `tests/utils/vscodeclaude/` deleted entirely
- [x] `mcp__code-checker__run_pytest_check` passes
- [x] `mcp__code-checker__run_pylint_check` passes
- [x] `mcp__code-checker__run_mypy_check` passes

## Implementation Steps

1. **Step 1**: Move all 13 test files and delete old directory
2. **Step 2**: Run verification checks (pytest, pylint, mypy)

## Notes

- No TDD needed - this is file reorganization, not new functionality
- Imports already point to correct location (`mcp_coder.workflows.vscodeclaude`)
- Follow [Safe Refactoring Guide](docs/processes-prompts/refactoring-guide.md)
