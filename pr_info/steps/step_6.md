# Step 6: Extract Constants to Dedicated Modules

## Objective
Extract duplicate command templates and workflow mapping into dedicated constants modules to eliminate code duplication and improve maintainability.

## LLM Prompt
```
Based on summary.md and Decisions.md, implement Step 6 of the coordinator module refactoring. Create two new constants modules (command_templates.py and workflow_constants.py), move all template strings and WORKFLOW_MAPPING to these modules, update imports in commands.py and core.py, and revert the pyproject.toml mypy change. Preserve all existing functionality.
```

## Implementation Details

### WHERE (Files to Create/Modify)

**New Files:**
- `src/mcp_coder/cli/commands/coordinator/command_templates.py`
- `src/mcp_coder/cli/commands/coordinator/workflow_constants.py`

**Files to Modify:**
- `src/mcp_coder/cli/commands/coordinator/commands.py`
- `src/mcp_coder/cli/commands/coordinator/core.py`
- `src/mcp_coder/cli/commands/coordinator/__init__.py`
- `pyproject.toml`

### WHAT (Module Contents)

**command_templates.py:**
```python
"""Command template strings for coordinator CLI operations."""

# Test command templates
DEFAULT_TEST_COMMAND: str
DEFAULT_TEST_COMMAND_WINDOWS: str
TEST_COMMAND_TEMPLATES: dict[str, str]

# Workflow command templates - Linux
CREATE_PLAN_COMMAND_TEMPLATE: str
IMPLEMENT_COMMAND_TEMPLATE: str
CREATE_PR_COMMAND_TEMPLATE: str

# Workflow command templates - Windows
CREATE_PLAN_COMMAND_WINDOWS: str
IMPLEMENT_COMMAND_WINDOWS: str
CREATE_PR_COMMAND_WINDOWS: str

# Priority order
PRIORITY_ORDER: list[str]
```

**workflow_constants.py:**
```python
"""Workflow configuration constants for coordinator operations."""

from typing import TypedDict

class WorkflowConfig(TypedDict):
    workflow: str
    branch_strategy: str
    next_label: str

WORKFLOW_MAPPING: dict[str, WorkflowConfig]
```

### HOW (Integration Points)

**commands.py imports:**
```python
from .command_templates import (
    DEFAULT_TEST_COMMAND,
    DEFAULT_TEST_COMMAND_WINDOWS,
    TEST_COMMAND_TEMPLATES,
)
```

**core.py imports:**
```python
from .command_templates import (
    CREATE_PLAN_COMMAND_TEMPLATE,
    CREATE_PLAN_COMMAND_WINDOWS,
    CREATE_PR_COMMAND_TEMPLATE,
    CREATE_PR_COMMAND_WINDOWS,
    IMPLEMENT_COMMAND_TEMPLATE,
    IMPLEMENT_COMMAND_WINDOWS,
    PRIORITY_ORDER,
)
from .workflow_constants import WORKFLOW_MAPPING
```

**__init__.py exports:**
```python
from .command_templates import (
    CREATE_PLAN_COMMAND_TEMPLATE,
    CREATE_PLAN_COMMAND_WINDOWS,
    # ... all templates
)
from .workflow_constants import WORKFLOW_MAPPING
```

### ALGORITHM (Migration Steps)

```
1. Create command_templates.py with all template strings from commands.py
2. Create workflow_constants.py with WORKFLOW_MAPPING from core.py
3. Update commands.py: remove templates, add imports from command_templates
4. Update core.py: remove templates and WORKFLOW_MAPPING, add imports
5. Update __init__.py: change imports to use new modules
6. Revert pyproject.toml: remove disable_error_code line
7. Run quality checks to verify no regressions
```

### DATA (Constants to Move)

**From commands.py to command_templates.py:**
- `DEFAULT_TEST_COMMAND`
- `DEFAULT_TEST_COMMAND_WINDOWS`
- `TEST_COMMAND_TEMPLATES`
- `CREATE_PLAN_COMMAND_WINDOWS`
- `IMPLEMENT_COMMAND_WINDOWS`
- `CREATE_PR_COMMAND_WINDOWS`
- `CREATE_PLAN_COMMAND_TEMPLATE`
- `IMPLEMENT_COMMAND_TEMPLATE`
- `CREATE_PR_COMMAND_TEMPLATE`
- `PRIORITY_ORDER`

**From core.py to workflow_constants.py:**
- `WORKFLOW_MAPPING`

**From core.py to command_templates.py (duplicates to remove):**
- `CREATE_PLAN_COMMAND_WINDOWS` (duplicate)
- `IMPLEMENT_COMMAND_WINDOWS` (duplicate)
- `CREATE_PR_COMMAND_WINDOWS` (duplicate)
- `CREATE_PLAN_COMMAND_TEMPLATE` (duplicate)
- `IMPLEMENT_COMMAND_TEMPLATE` (duplicate)
- `CREATE_PR_COMMAND_TEMPLATE` (duplicate)

## Test Strategy

**No new tests required** - this is pure code movement.

**Verification Steps:**
1. All existing tests pass without modification
2. Import patterns work correctly
3. pylint, pytest, mypy all pass
4. No duplicate code remains

## Success Criteria
- [ ] `command_templates.py` created with all template strings
- [ ] `workflow_constants.py` created with WORKFLOW_MAPPING
- [ ] `commands.py` imports from `command_templates.py`, no local templates
- [ ] `core.py` imports from both new modules, no local templates/mapping
- [ ] `__init__.py` exports from new modules
- [ ] `pyproject.toml` mypy change reverted
- [ ] All existing tests pass
- [ ] pylint, pytest, mypy quality checks pass

## Dependencies
- **Requires**: Steps 1-5 completion (coordinator package exists)
- **Provides**: Clean separation of constants from logic
- **Next**: Step 7 will restructure test files
