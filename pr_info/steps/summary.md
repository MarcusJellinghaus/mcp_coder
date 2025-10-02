# Refactor LLM Module Structure - Implementation Summary

## Overview
Refactor LLM-related modules to consolidate functionality under a single `llm/` package with clear separation of concerns. This is a **pure refactoring** - no new features, no behavior changes, only code organization improvements.

## Problem Statement
Current issues:
1. **Massive `cli/commands/prompt.py`** (800+ lines) with mixed responsibilities
2. **Business logic in CLI layer** - formatters, serialization, storage coupled to CLI
3. **Poor test organization** - tests scattered and don't mirror code structure
4. **`cli/llm_helpers.py`** contains business logic, not CLI utilities

## Solution
Consolidate all LLM functionality under `src/mcp_coder/llm/` with clear sub-packages:
```
llm/
├── types.py              # Type definitions (from llm_types.py)
├── interface.py          # Public API (from llm_interface.py)
├── serialization.py      # JSON I/O (from llm_serialization.py)
├── formatting/           # Response formatting
│   ├── formatters.py     # Text/verbose/raw formatters
│   └── sdk_serialization.py  # SDK object utilities
├── storage/              # Session persistence
│   ├── session_storage.py    # Store/load sessions
│   └── session_finder.py     # Find latest session
├── session/              # Session management
│   └── resolver.py       # Session ID resolution, parse_llm_method
└── providers/            # Provider implementations (from llm_providers/)
    └── claude/
```

## Architectural Changes

### Module Structure
**Before:**
```
src/mcp_coder/
├── llm_types.py
├── llm_interface.py
├── llm_serialization.py
├── llm_providers/
│   └── claude/
└── cli/
    ├── llm_helpers.py       # Misplaced business logic
    └── commands/
        └── prompt.py         # 800+ lines, mixed concerns
```

**After:**
```
src/mcp_coder/
└── llm/                      # All LLM functionality
    ├── __init__.py           # Public API exports
    ├── types.py
    ├── interface.py
    ├── serialization.py
    ├── formatting/           # NEW: Response formatting
    ├── storage/              # NEW: Session persistence
    ├── session/              # NEW: Session management
    └── providers/
        └── claude/
```

### Separation of Concerns

| Concern | Before | After |
|---------|--------|-------|
| **Type Definitions** | `llm_types.py` (root) | `llm/types.py` |
| **LLM Interface** | `llm_interface.py` (root) | `llm/interface.py` |
| **Serialization** | `llm_serialization.py` (root) | `llm/serialization.py` |
| **Response Formatting** | `cli/commands/prompt.py` (CLI layer) | `llm/formatting/formatters.py` |
| **SDK Utilities** | `cli/commands/prompt.py` (CLI layer) | `llm/formatting/sdk_serialization.py` |
| **Session Storage** | `cli/commands/prompt.py` (CLI layer) | `llm/storage/session_storage.py` |
| **Session Finding** | `cli/commands/prompt.py` (CLI layer) | `llm/storage/session_finder.py` |
| **Session Resolution** | `cli/llm_helpers.py` (wrong layer) | `llm/session/resolver.py` |
| **CLI Orchestration** | `cli/commands/prompt.py` (800+ lines) | `cli/commands/prompt.py` (~100 lines) |

### Test Structure Changes

**Before:**
```
tests/
├── test_llm_types.py
├── test_llm_interface.py
├── test_llm_serialization.py
├── llm_providers/
└── cli/commands/
    ├── test_prompt.py                    # 800+ lines, everything
    └── test_prompt_sdk_utilities.py      # SDK tests in CLI layer
```

**After:**
```
tests/
└── llm/                                  # Mirrors code structure
    ├── test_types.py
    ├── test_interface.py
    ├── test_serialization.py
    ├── formatting/
    │   ├── test_formatters.py            # Extracted from test_prompt.py
    │   └── test_sdk_serialization.py     # Moved from CLI layer
    ├── storage/
    │   ├── test_session_storage.py       # Extracted from test_prompt.py
    │   └── test_session_finder.py        # Extracted from test_prompt.py
    ├── session/
    │   └── test_resolver.py              # Extracted from test_prompt.py
    └── providers/
        └── claude/
```

## Files to Create

### New Source Files
```
src/mcp_coder/llm/__init__.py
src/mcp_coder/llm/formatting/__init__.py
src/mcp_coder/llm/formatting/formatters.py
src/mcp_coder/llm/formatting/sdk_serialization.py
src/mcp_coder/llm/storage/__init__.py
src/mcp_coder/llm/storage/session_storage.py
src/mcp_coder/llm/storage/session_finder.py
src/mcp_coder/llm/session/__init__.py
src/mcp_coder/llm/session/resolver.py
```

### New Test Files
```
tests/llm/__init__.py
tests/llm/formatting/__init__.py
tests/llm/formatting/test_formatters.py
tests/llm/formatting/test_sdk_serialization.py
tests/llm/storage/__init__.py
tests/llm/storage/test_session_storage.py
tests/llm/storage/test_session_finder.py
tests/llm/session/__init__.py
tests/llm/session/test_resolver.py
```

## Files to Modify

### Source Files
```
src/mcp_coder/__init__.py                 # Update imports
src/mcp_coder/cli/commands/prompt.py      # Slim down from 800 to ~100 lines
src/mcp_coder/cli/commands/commit.py      # Update imports (if uses LLM)
src/mcp_coder/prompt_manager.py           # Update imports (if any)
```

### Test Files
```
tests/cli/commands/test_prompt.py         # Slim down, keep only CLI tests
tests/test_module_exports.py              # Update imports
tests/test_module_integration.py          # Update imports
```

## Files to Move

### Source Files
```
src/mcp_coder/llm_types.py          → src/mcp_coder/llm/types.py
src/mcp_coder/llm_interface.py      → src/mcp_coder/llm/interface.py
src/mcp_coder/llm_serialization.py  → src/mcp_coder/llm/serialization.py
src/mcp_coder/llm_providers/        → src/mcp_coder/llm/providers/
```

### Test Files
```
tests/test_llm_types.py              → tests/llm/test_types.py
tests/test_llm_interface.py          → tests/llm/test_interface.py
tests/test_llm_serialization.py      → tests/llm/test_serialization.py
tests/llm_providers/                 → tests/llm/providers/
tests/cli/commands/test_prompt_sdk_utilities.py → tests/llm/formatting/test_sdk_serialization.py
```

## Files to Delete

### Source Files
```
src/mcp_coder/llm_types.py               # Moved to llm/types.py
src/mcp_coder/llm_interface.py           # Moved to llm/interface.py
src/mcp_coder/llm_serialization.py       # Moved to llm/serialization.py
src/mcp_coder/llm_providers/             # Moved to llm/providers/
src/mcp_coder/cli/llm_helpers.py         # Moved to llm/session/resolver.py
```

### Test Files
```
tests/test_llm_types.py                  # Moved to llm/test_types.py
tests/test_llm_interface.py              # Moved to llm/test_interface.py
tests/test_llm_serialization.py          # Moved to llm/test_serialization.py
tests/llm_providers/                     # Moved to llm/providers/
tests/cli/commands/test_prompt_sdk_utilities.py  # Moved to llm/formatting/
```

## Implementation Steps

1. **Step 1: Create Package Structure** - Create `llm/` package with empty modules
2. **Step 2: Move Core Modules** - Move `llm_types.py`, `llm_interface.py`, `llm_serialization.py`
3. **Step 3: Move Providers** - Move `llm_providers/` to `llm/providers/`
4. **Step 4: Extract SDK Utilities** - Extract from `prompt.py` to `llm/formatting/sdk_serialization.py`
5. **Step 5: Extract Formatters** - Extract from `prompt.py` to `llm/formatting/formatters.py`
6. **Step 6: Extract Storage** - Extract from `prompt.py` to `llm/storage/`
7. **Step 7: Extract Session Logic** - Move from `cli/llm_helpers.py` to `llm/session/resolver.py`
8. **Step 8: Move Core Tests** - Reorganize test structure to mirror code
9. **Step 9: Extract Formatting Tests** - Extract from `test_prompt.py`
10. **Step 10: Extract Storage/Session Tests** - Extract from `test_prompt.py`
11. **Step 11: Verify & Cleanup** - Run all tests, update imports, cleanup

## Import Guidelines

**Always use absolute imports starting with `mcp_coder`:**

```python
# ✅ Acceptable styles
from mcp_coder.llm.types import LLMResponseDict
from mcp_coder.llm import LLMResponseDict  # Via public API

# ❌ Avoid relative imports
from .types import LLMResponseDict
```

**Rationale:**
- Absolute imports provide clarity about module location
- Both direct and public API imports are acceptable
- Relative imports can be confusing in larger codebases

## Benefits

1. **Clear Organization** - All LLM functionality in one place (`llm/` module)
2. **Separation of Concerns** - Each sub-package has single responsibility
3. **Better Testability** - Pure functions easy to test without CLI mocking
4. **Reusable Components** - Formatters and utilities available to other modules
5. **Maintainability** - Reduce `prompt.py` from 800 to ~100 lines (87% reduction)
6. **Easier Extension** - Add new formats/storage without touching CLI code
7. **Clean Imports** - `from mcp_coder.llm import ask_llm, prompt_llm`

## Success Criteria

- ✅ All existing tests pass (zero behavior changes)
- ✅ `prompt.py` reduced from 800+ to ~100 lines
- ✅ All LLM functionality under `llm/` module
- ✅ Test structure mirrors code structure
- ✅ Clean public API via `llm/__init__.py`
- ✅ No `cli/llm_helpers.py` (moved to proper location)
- ✅ Static analysis passes (pylint, mypy)

## Risk Mitigation

- **Incremental Approach** - Each step is self-contained and testable
- **TDD** - Tests verify behavior unchanged at each step
- **Import Updates** - Systematic import path updates with test verification
- **Backward Compatibility** - Maintain all existing behavior
