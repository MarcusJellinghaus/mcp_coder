# Step 2: Create workflows/vscodeclaude/ Package Structure

## LLM Prompt
```
Read pr_info/steps/summary.md for context on issue #358.

Implement Step 2: Create the `workflows/vscodeclaude/` package structure.

Create the new package directory and move files from utils/vscodeclaude/.
Move templates from coordinator/vscodeclaude_templates.py.
Replace _get_coordinator() late-binding with direct imports from utils.
```

---

## WHERE

### Files to Create

| Source | Destination |
|--------|-------------|
| `utils/vscodeclaude/__init__.py` | `workflows/vscodeclaude/__init__.py` |
| `utils/vscodeclaude/cleanup.py` | `workflows/vscodeclaude/cleanup.py` |
| `utils/vscodeclaude/config.py` | `workflows/vscodeclaude/config.py` |
| `utils/vscodeclaude/helpers.py` | `workflows/vscodeclaude/helpers.py` |
| `utils/vscodeclaude/issues.py` | `workflows/vscodeclaude/issues.py` |
| `utils/vscodeclaude/orchestrator.py` | `workflows/vscodeclaude/orchestrator.py` |
| `utils/vscodeclaude/sessions.py` | `workflows/vscodeclaude/sessions.py` |
| `utils/vscodeclaude/status.py` | `workflows/vscodeclaude/status.py` |
| `utils/vscodeclaude/types.py` | `workflows/vscodeclaude/types.py` |
| `utils/vscodeclaude/workspace.py` | `workflows/vscodeclaude/workspace.py` |
| `cli/commands/coordinator/vscodeclaude_templates.py` | `workflows/vscodeclaude/templates.py` |

### Files to Modify  
- `src/mcp_coder/workflows/__init__.py` - Add vscodeclaude export

---

## WHAT

### Package Structure
```
src/mcp_coder/workflows/vscodeclaude/
├── __init__.py      # Public API exports
├── cleanup.py       # Session cleanup operations
├── config.py        # Configuration loading
├── helpers.py       # Helper functions
├── issues.py        # Issue filtering logic
├── orchestrator.py  # Main orchestration logic
├── sessions.py      # Session management
├── status.py        # Status display and staleness
├── templates.py     # Template strings (from coordinator)
├── types.py         # Type definitions and constants
└── workspace.py     # Workspace file operations
```

### __init__.py Exports
```python
"""VSCode Claude workspace management workflows."""

from .core import (
    # Public functions - list based on actual module content
)
from .templates import (
    # Template constants
)

__all__ = [
    # All public exports
]
```

---

## HOW

### Import Replacement Pattern

**Before (in utils/vscodeclaude):**
```python
def _get_coordinator() -> ModuleType:
    from mcp_coder.cli.commands import coordinator
    return coordinator

# Usage:
coordinator = _get_coordinator()
coordinator.IssueManager(...)
coordinator.load_labels_config(...)
```

**After (in workflows/vscodeclaude):**
```python
from mcp_coder.utils.github_operations.issue_manager import IssueManager
from mcp_coder.utils.github_operations.issue_branch_manager import IssueBranchManager
from mcp_coder.utils.github_operations.label_config import load_labels_config
from mcp_coder.utils.user_config import get_config_values, get_cache_refresh_minutes
```

---

## ALGORITHM

### File Move Process
```
1. Create workflows/vscodeclaude/ directory
2. Copy all 10 files from utils/vscodeclaude/ (see table above)
3. Copy vscodeclaude_templates.py → templates.py
4. In files that use _get_coordinator() (config.py, issues.py, orchestrator.py, status.py):
   - Remove _get_coordinator() function
   - Replace coordinator.X calls with direct imports
5. Update internal imports (..github_operations → ...utils.github_operations)
6. Update workflows/__init__.py to export vscodeclaude
```

---

## DATA

### Direct Import Mapping

| Late-binding call | Direct import |
|-------------------|---------------|
| `coordinator.IssueManager` | `from ...utils.github_operations.issue_manager import IssueManager` |
| `coordinator.IssueBranchManager` | `from ...utils.github_operations.issue_branch_manager import IssueBranchManager` |
| `coordinator.load_labels_config` | `from ...utils.github_operations.label_config import load_labels_config` |
| `coordinator.get_config_values` | `from ...utils.user_config import get_config_values` |
| `coordinator.get_cache_refresh_minutes` | `from ...utils.user_config import get_cache_refresh_minutes` |

---

## Verification

After this step:
- `from mcp_coder.workflows.vscodeclaude import ...` should work
- No imports from `cli.commands.coordinator` in the new package
- Run: `./tools/lint_imports.sh` to verify layer compliance
