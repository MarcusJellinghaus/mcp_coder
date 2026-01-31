# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** for Issue #358: Refactor vscodeclaude - Move from utils to workflows layer.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Move `get_cache_refresh_minutes()` to utils/user_config.py
See [step_1.md](./steps/step_1.md) for details.

- [x] Copy `get_cache_refresh_minutes()` function to `utils/user_config.py`
- [x] Remove late-binding - use direct `get_config_values` call
- [x] Remove function from `coordinator/core.py`
- [x] Remove `get_cache_refresh_minutes` from `coordinator/__init__.py` exports
- [x] Add tests for moved function in `tests/utils/test_user_config.py`
- [x] Update test patches in `tests/cli/commands/coordinator/test_core.py`
- [x] Run pylint and fix any issues
- [x] Run pytest and fix any issues
- [x] Run mypy and fix any issues
- [x] Prepare git commit message for Step 1

### Step 2: Create workflows/vscodeclaude/ Package Structure
See [step_2.md](./steps/step_2.md) for details.

- [x] Create `workflows/vscodeclaude/` directory
- [x] Move `utils/vscodeclaude/__init__.py` → `workflows/vscodeclaude/__init__.py`
- [x] Move `utils/vscodeclaude/cleanup.py` → `workflows/vscodeclaude/cleanup.py`
- [x] Move `utils/vscodeclaude/config.py` → `workflows/vscodeclaude/config.py`
- [x] Move `utils/vscodeclaude/helpers.py` → `workflows/vscodeclaude/helpers.py`
- [x] Move `utils/vscodeclaude/issues.py` → `workflows/vscodeclaude/issues.py`
- [x] Move `utils/vscodeclaude/orchestrator.py` → `workflows/vscodeclaude/orchestrator.py`
- [x] Move `utils/vscodeclaude/sessions.py` → `workflows/vscodeclaude/sessions.py`
- [x] Move `utils/vscodeclaude/status.py` → `workflows/vscodeclaude/status.py`
- [x] Move `utils/vscodeclaude/types.py` → `workflows/vscodeclaude/types.py`
- [x] Move `utils/vscodeclaude/workspace.py` → `workflows/vscodeclaude/workspace.py`
- [x] Move `coordinator/vscodeclaude_templates.py` → `workflows/vscodeclaude/templates.py`
- [x] Remove `_get_coordinator()` pattern from all moved files
- [x] Replace late-binding with direct imports from utils
- [x] Update internal imports to use correct relative paths
- [x] Update `workflows/__init__.py` to export vscodeclaude
- [x] Run pylint and fix any issues
- [x] Run pytest and fix any issues
- [x] Run mypy and fix any issues
- [x] Prepare git commit message for Step 2

### Step 3: Clean Up CLI Layer and Delete Old Files
See [step_3.md](./steps/step_3.md) for details.

- [x] Verify and delete empty `utils/vscodeclaude/` directory
- [x] Delete `coordinator/vscodeclaude.py`
- [x] Delete `coordinator/vscodeclaude_templates.py` (if not moved yet)
- [x] Remove vscodeclaude imports from `coordinator/__init__.py`
- [x] Remove vscodeclaude items from `coordinator/__init__.py` `__all__`
- [x] Remove vscodeclaude references from `utils/__init__.py` (if present)
- [x] Run pylint and fix any issues
- [x] Run pytest and fix any issues
- [x] Run mypy and fix any issues
- [x] Prepare git commit message for Step 3

### Step 4: Update Test Patches
See [step_4.md](./steps/step_4.md) for details.

- [x] Search for all patches containing "vscodeclaude" in tests/
- [x] Search for patches of `get_cache_refresh_minutes` in tests/
- [x] Update patches: `utils.vscodeclaude` → `workflows.vscodeclaude`
- [x] Update patches: `coordinator.get_cache_refresh_minutes` → `utils.user_config.get_cache_refresh_minutes`
- [x] Update patches: `coordinator.vscodeclaude` → `workflows.vscodeclaude`
- [x] Run pylint and fix any issues
- [x] Run pytest and fix any issues
- [x] Run mypy and fix any issues
- [x] Prepare git commit message for Step 4

### Step 5: Final Verification
See [step_5.md](./steps/step_5.md) for details.

- [x] Run `./tools/lint_imports.sh` and verify all contracts pass
- [x] Run `./tools/tach_check.sh` and verify no layer violations
- [x] Run `mcp__code-checker__run_pylint_check` and fix any errors/fatal issues
- [x] Run `mcp__code-checker__run_mypy_check` and fix any type errors
- [ ] Run `mcp__code-checker__run_pytest_check` and ensure all tests pass
- [ ] Verify no imports from CLI layer in workflows layer
- [ ] Verify `import mcp_coder.utils.vscodeclaude` fails (deleted)
- [ ] Verify `from mcp_coder.workflows.vscodeclaude import ...` works
- [ ] Verify `from mcp_coder.utils.user_config import get_cache_refresh_minutes` works
- [ ] Prepare git commit message for Step 5

---

## Pull Request

- [ ] Review all implementation steps for completeness
- [ ] Run full test suite and ensure all tests pass
- [ ] Prepare comprehensive PR summary
- [ ] Create pull request
