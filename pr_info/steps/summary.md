# Issue #358: Refactor vscodeclaude - Move from utils to workflows layer

## Summary

Move `utils/vscodeclaude/` package to `workflows/vscodeclaude/` to fix architectural layering violation where the lower-level utils layer imports from the higher-level CLI layer.

## Problem

The `utils/vscodeclaude/` package uses a `_get_coordinator()` late-binding pattern to import from `cli/commands/coordinator/`. This violates the layered architecture:
- **utils** (infrastructure) should NOT import from **cli** (presentation)
- `vscodeclaude` is feature/workflow logic, not a general-purpose utility

## Solution

Move `vscodeclaude` to the `workflows/` layer where it belongs, replacing late-binding with direct imports from `utils/`.

---

## Architectural Changes

### Before (Violation)
```
cli/commands/coordinator/
    └── vscodeclaude.py (re-exports)
    └── vscodeclaude_templates.py
    └── core.py (contains get_cache_refresh_minutes)

utils/vscodeclaude/
    └── *.py (imports via _get_coordinator() → cli layer) ❌ VIOLATION
```

### After (Correct)
```
workflows/vscodeclaude/
    └── *.py (imports directly from utils) ✓ CORRECT
    └── templates.py (moved from coordinator)

utils/user_config.py
    └── get_cache_refresh_minutes() (moved from coordinator/core.py)
```

### Layer Dependency Flow
```
cli (presentation)
  ↓ imports from
workflows (application)  ← vscodeclaude lives here now
  ↓ imports from
utils (infrastructure)
```

---

## Files to Create

| Path | Description |
|------|-------------|
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | Package init with exports |
| `src/mcp_coder/workflows/vscodeclaude/core.py` | Main logic (moved from utils) |
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | Templates (moved from coordinator) |
| `src/mcp_coder/workflows/vscodeclaude/*.py` | Other modules (moved from utils) |

## Files to Modify

| Path | Change |
|------|--------|
| `src/mcp_coder/utils/user_config.py` | Add `get_cache_refresh_minutes()` function |
| `src/mcp_coder/cli/commands/coordinator/__init__.py` | Remove vscodeclaude re-exports |
| `src/mcp_coder/cli/commands/coordinator/core.py` | Remove `get_cache_refresh_minutes()` |
| `src/mcp_coder/workflows/__init__.py` | Add vscodeclaude to exports |
| `tests/utils/vscodeclaude/*.py` | Update patch paths |
| `tests/cli/commands/coordinator/*.py` | Update patch paths for cache function |

## Files to Delete

| Path | Reason |
|------|--------|
| `src/mcp_coder/utils/vscodeclaude/` | Entire directory - moved to workflows |
| `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py` | No longer needed |
| `src/mcp_coder/cli/commands/coordinator/vscodeclaude_templates.py` | Moved to workflows |

---

## Key Design Decisions

| Topic | Decision |
|-------|----------|
| Late-binding removal | Replace `_get_coordinator()` with direct imports from `utils` |
| Template location | Move to `workflows/vscodeclaude/templates.py` |
| Cache config function | Move to `utils/user_config.py` (infrastructure layer) |
| CLI re-export wrapper | Delete entirely - consumers import from `workflows.vscodeclaude` |
| Test file reorganization | Update patches only; file moves in follow-up PR |
| Deprecation warnings | None - clean delete |

---

## Verification Checklist

- [ ] `./tools/lint_imports.sh` passes
- [ ] `./tools/tach_check.sh` passes  
- [ ] `mcp__code-checker__run_pylint_check` passes
- [ ] `mcp__code-checker__run_mypy_check` passes
- [ ] `mcp__code-checker__run_pytest_check` passes
- [ ] No imports from CLI layer in workflows layer
