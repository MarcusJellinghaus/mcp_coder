# Step 2: Refactor core.py - Remove _get_coordinator() and use direct imports

## LLM Prompt
```
You are implementing Issue #365: Refactor coordinator - Remove _get_coordinator() late-binding pattern.
See pr_info/steps/summary.md for full context.

This is Step 2: Remove `_get_coordinator()` function from core.py and replace all 
`coordinator.<func>()` calls with direct imports and calls.
```

## WHERE

### File to Modify
- `src/mcp_coder/cli/commands/coordinator/core.py`

## WHAT

### Remove
```python
# DELETE this function entirely
def _get_coordinator() -> ModuleType:
    """Get coordinator package for late binding of patchable functions."""
    from mcp_coder.cli.commands import coordinator
    return coordinator
```

### Remove Import
```python
# DELETE this import (no longer needed)
from types import ModuleType
```

### Add Direct Imports
```python
# ADD these imports (near top of file with other imports)
from ....utils.user_config import get_config_values
from ....utils.github_operations.label_config import load_labels_config
```

### Remove Unused Import (see Decision 3)
```python
# CHANGE this import - REMOVE _update_issue_labels_in_cache (unused in core.py)
from ....utils.github_operations.issue_cache import (
    CacheData,
    _update_issue_labels_in_cache,  # REMOVE - not used in core.py
    get_all_cached_issues,
)

# TO
from ....utils.github_operations.issue_cache import (
    CacheData,
    get_all_cached_issues,
)
```

Note: `_update_issue_labels_in_cache` is never used in `core.py` - it was only imported for re-export.
`commands.py` will import `update_issue_labels_in_cache` directly from `issue_cache.py` (Step 3).

## HOW

### Replace Pattern in Functions

**In `load_repo_config()`:**
```python
# Before
coordinator = _get_coordinator()
config = coordinator.get_config_values([...])

# After
config = get_config_values([...])
```

**In `get_jenkins_credentials()`:**
```python
# Before
coordinator = _get_coordinator()
config = coordinator.get_config_values([...])

# After
config = get_config_values([...])
```

**In `_filter_eligible_issues()`:**
```python
# Before
coordinator = _get_coordinator()
labels_config = coordinator.load_labels_config(config_path)

# After
labels_config = load_labels_config(config_path)
```

**In `get_eligible_issues()`:**
```python
# Before
coordinator = _get_coordinator()
labels_config = coordinator.load_labels_config(config_path)

# After
labels_config = load_labels_config(config_path)
```

## ALGORITHM
```
1. Delete _get_coordinator() function definition
2. Delete "from types import ModuleType" import
3. Add imports for get_config_values and load_labels_config
4. Remove _update_issue_labels_in_cache from issue_cache import (unused in core.py)
5. In each function using coordinator pattern:
   a. Delete line "coordinator = _get_coordinator()"
   b. Replace "coordinator.get_config_values" with "get_config_values"
   c. Replace "coordinator.load_labels_config" with "load_labels_config"
6. Delete any comments about "late binding" or "test patching"
```

## DATA

No data structure changes - only import and call patterns change.

## VERIFICATION

After this step:
```bash
# Should find 0 occurrences
grep "_get_coordinator" src/mcp_coder/cli/commands/coordinator/core.py
grep "coordinator\." src/mcp_coder/cli/commands/coordinator/core.py

# Should find direct imports
grep "from ....utils.user_config import get_config_values" src/mcp_coder/cli/commands/coordinator/core.py
grep "from ....utils.github_operations.label_config import load_labels_config" src/mcp_coder/cli/commands/coordinator/core.py
```
