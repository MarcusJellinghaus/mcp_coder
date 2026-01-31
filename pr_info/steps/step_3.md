# Step 3: Clean Up CLI Layer and Delete Old Files

## LLM Prompt
```
Read pr_info/steps/summary.md for context on issue #358.

Implement Step 3: Clean up the CLI layer by removing vscodeclaude 
re-exports and deleting the old utils/vscodeclaude/ directory.

This completes the refactoring by removing all traces of the old 
location and updating the coordinator package exports.
```

---

## WHERE

### Files to Delete
- `src/mcp_coder/utils/vscodeclaude/` (entire directory)
- `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py`
- `src/mcp_coder/cli/commands/coordinator/vscodeclaude_templates.py`

### Files to Modify
- `src/mcp_coder/cli/commands/coordinator/__init__.py` - Remove vscodeclaude exports
- `src/mcp_coder/utils/__init__.py` - Remove vscodeclaude import (if present)

---

## WHAT

### Coordinator __init__.py Cleanup

**Remove these imports:**
```python
# DELETE - vscodeclaude re-exports
from .vscodeclaude import (...)
from .vscodeclaude_templates import (...)
```

**Remove from __all__:**
```python
# DELETE from __all__ list:
# - All vscodeclaude-related exports
# - get_cache_refresh_minutes (now in utils.user_config)
```

**Keep these re-exports:**
```python
# KEEP - still needed for coordinator functionality
from .core import (
    _filter_eligible_issues,
    dispatch_workflow,
    get_cached_eligible_issues,
    get_eligible_issues,
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
)
# Note: get_cache_refresh_minutes removed - import from utils.user_config
```

---

## HOW

### Deletion Checklist

1. **Delete `utils/vscodeclaude/`:**
   ```bash
   rm -rf src/mcp_coder/utils/vscodeclaude/
   ```

2. **Delete coordinator vscodeclaude files:**
   ```bash
   rm src/mcp_coder/cli/commands/coordinator/vscodeclaude.py
   rm src/mcp_coder/cli/commands/coordinator/vscodeclaude_templates.py
   ```

3. **Edit coordinator/__init__.py:**
   - Remove vscodeclaude imports
   - Remove from `__all__`
   - Update `get_cache_refresh_minutes` to import from new location (or remove if not needed in coordinator)

---

## ALGORITHM

```
1. Delete utils/vscodeclaude/ directory
2. Delete coordinator/vscodeclaude.py
3. Delete coordinator/vscodeclaude_templates.py  
4. Edit coordinator/__init__.py:
   - Remove vscodeclaude import lines
   - Remove vscodeclaude items from __all__
5. Edit utils/__init__.py (if needed):
   - Remove any vscodeclaude references
```

---

## DATA

### Exports to Remove from coordinator/__init__.py

Based on the issue, these should be removed from `__all__`:
- All vscodeclaude-related function/class exports
- `get_cache_refresh_minutes` (moved to utils.user_config)
- `_filter_eligible_vscodeclaude_issues` if it existed

### Exports to Keep

The coordinator package should still export its core functionality for non-vscodeclaude use cases (if any remain).

---

## Verification

After this step:
- `import mcp_coder.utils.vscodeclaude` should fail (deleted)
- `import mcp_coder.cli.commands.coordinator.vscodeclaude` should fail (deleted)
- `from mcp_coder.workflows.vscodeclaude import ...` should work
- `from mcp_coder.utils.user_config import get_cache_refresh_minutes` should work
- No circular dependencies
