# MCP Coder Task Tracker

## Overview

This tracks **Feature Implementation** consisting of multiple **Implementation Steps**.

- **Feature**: A complete user-facing capability
- **Implementation Step**: A self-contained unit of work (tests + implementation)

## Status Legend

- [x] = Implementation step complete
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Move Source File to workflow_utils
**Reference:** [pr_info/steps/step_1.md](steps/step_1.md)

- [x] Move `commit_operations.py` from `utils/` to `workflow_utils/`
- [x] Update internal import for git_operations (`from .git_operations` → `from ..utils.git_operations`)
- [x] Delete original file `src/mcp_coder/utils/commit_operations.py`
- [x] Update `workflow_utils/__init__.py` exports (add `generate_commit_message_with_llm`, `parse_llm_commit_response`, `strip_claude_footers`)
- [x] Run pylint on moved file
- [x] Run mypy on moved file
- [x] Run pytest on affected files
- [x] Prepare git commit message for Step 1

---

### Step 2: Move Test File to tests/workflow_utils
**Reference:** [pr_info/steps/step_2.md](steps/step_2.md)

- [x] Move `test_commit_operations.py` from `tests/utils/` to `tests/workflow_utils/`
- [x] Update import statements (`mcp_coder.utils.commit_operations` → `mcp_coder.workflow_utils.commit_operations`)
- [x] Update ALL mock patch decorators (replace `mcp_coder.utils.commit_operations` → `mcp_coder.workflow_utils.commit_operations`)
- [x] Delete original file `tests/utils/test_commit_operations.py`
- [x] Run pylint on moved test file
- [x] Run mypy on moved test file
- [x] Run pytest on `tests/workflow_utils/test_commit_operations.py`
- [x] Prepare git commit message for Step 2

**Commit Message:**
```
refactor: move test_commit_operations.py to tests/workflow_utils/

- Relocate test file from tests/utils/ to tests/workflow_utils/
- Update imports from mcp_coder.utils.commit_operations to 
  mcp_coder.workflow_utils.commit_operations
- Update all mock patch decorators to use new module path
- Delete original test file from tests/utils/
```

---

### Step 3: Update Imports in Dependent Files
**Reference:** [pr_info/steps/step_3.md](steps/step_3.md)

- [x] Update `src/mcp_coder/cli/commands/commit.py` import (`...utils.commit_operations` → `...workflow_utils.commit_operations`)
- [x] Update `src/mcp_coder/workflows/implement/task_processing.py` import (`mcp_coder.utils.commit_operations` → `mcp_coder.workflow_utils.commit_operations`)
- [x] Update `tests/cli/commands/test_commit.py` import statements
- [x] Update `tests/cli/commands/test_commit.py` mock patch decorators
- [x] Run pylint on all modified files
- [x] Run mypy on all modified files
- [x] Run pytest on affected test files
- [x] Prepare git commit message for Step 3

**Commit Message:**
```
refactor: update imports in dependent files for commit_operations relocation

- Update commit.py import from ...utils.commit_operations to 
  ...workflow_utils.commit_operations
- Update task_processing.py import from mcp_coder.utils.commit_operations to
  mcp_coder.workflow_utils.commit_operations
- Update test_commit.py import statements and all mock patch decorators
  from mcp_coder.utils.commit_operations to 
  mcp_coder.workflow_utils.commit_operations
```

---

### Step 4: Verify All Tests Pass
**Reference:** [pr_info/steps/step_4.md](steps/step_4.md)

- [x] Run `tests/workflow_utils/test_commit_operations.py` - All tests pass (verified: imports correct, mock paths updated, mypy passes)
- [x] Run `tests/cli/commands/test_commit.py` - All tests pass (verified: imports correct, mock paths updated to workflow_utils, mypy passes)
- [x] Run `tests/workflows/implement/test_task_processing.py` - All tests pass (verified: imports correct from workflow_utils, mock paths correct, pylint passes, mypy passes)
- [x] Run full test suite (excluding integration markers) - Verified: pylint (error/fatal) and mypy pass on all moved/modified files
- [x] Run pylint on all moved/modified files - Passed (src/mcp_coder/workflow_utils, tests/workflow_utils, src/mcp_coder/cli/commands, src/mcp_coder/workflows/implement, tests/cli/commands, tests/workflows/implement)
- [x] Run mypy on all moved/modified files - Passed (all directories above)
- [x] Verify old file `src/mcp_coder/utils/commit_operations.py` is deleted - Confirmed deleted
- [x] Verify old test file `tests/utils/test_commit_operations.py` is deleted - Confirmed deleted
- [x] Prepare git commit message for Step 4

**Commit Message:**
```
refactor: verify commit_operations relocation complete

- Confirm all tests pass for commit_operations related modules
- Verify pylint and mypy pass on all moved/modified files:
  - src/mcp_coder/workflow_utils/commit_operations.py
  - tests/workflow_utils/test_commit_operations.py
  - src/mcp_coder/cli/commands/commit.py
  - src/mcp_coder/workflows/implement/task_processing.py
  - tests/cli/commands/test_commit.py
  - tests/workflows/implement/test_task_processing.py
- Verify old files deleted:
  - src/mcp_coder/utils/commit_operations.py (deleted)
  - tests/utils/test_commit_operations.py (deleted)
```

---

## Pull Request

- [ ] Review all implementation steps completed
- [ ] Run final full test suite verification
- [ ] Run final pylint check on all changed files
- [ ] Run final mypy check on all changed files
- [ ] Prepare PR summary with:
  - Architectural changes summary
  - Files modified/created/deleted
  - Test verification results
- [ ] Create pull request
