# Step 4: Update Package Imports and External References

## Objective
Update all external references to coordinator.py to work with the new package structure, ensuring backward compatibility and updating test imports for the modular structure.

## LLM Prompt
```
Based on summary.md, implement Step 4 of the coordinator module refactoring. Update all external imports and references to work with the new coordinator package structure. Focus on maintaining backward compatibility while updating test files to import from the appropriate modules (core.py vs commands.py). Preserve all existing functionality.
```

## Implementation Details

### WHERE (Files to Update)
- `src/mcp_coder/cli/commands/__init__.py` 
- `tests/cli/commands/test_coordinator.py`
- `src/mcp_coder/cli/commands/coordinator/__init__.py` (complete the exports)

### WHAT (Import Updates)

**File: `src/mcp_coder/cli/commands/__init__.py`**
```python
# Update coordinator import from single file to package
from . import coordinator  # This now refers to the package
from .coordinator import execute_coordinator_test  # Still works via __init__.py

# Keep all other imports unchanged
from .commit import execute_commit_auto, execute_commit_clipboard
from .create_plan import execute_create_plan
# ... etc
```

**File: `tests/cli/commands/test_coordinator.py`**
```python
# Update imports to be more specific about module sources
from mcp_coder.cli.commands.coordinator.commands import (
    DEFAULT_TEST_COMMAND,
    DEFAULT_TEST_COMMAND_WINDOWS,
    execute_coordinator_test,
    execute_coordinator_run,
    format_job_output,
)
from mcp_coder.cli.commands.coordinator.core import (
    CacheData,
    _filter_eligible_issues,
    _get_cache_file_path,
    _load_cache_file,
    _save_cache_file,
    _update_issue_labels_in_cache,
    dispatch_workflow,
    get_cache_refresh_minutes,
    get_cached_eligible_issues,
    get_eligible_issues,
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
)
```

**File: `src/mcp_coder/cli/commands/coordinator/__init__.py`** (Complete version)
```python
"""Coordinator CLI commands for automated workflow orchestration."""

# Import from commands module
from .commands import (
    execute_coordinator_test,
    execute_coordinator_run,
    format_job_output,
)

# Import from core module  
from .core import (
    CacheData,
    dispatch_workflow,
    get_cached_eligible_issues,
    get_eligible_issues,
    load_repo_config,
    validate_repo_config,
    get_jenkins_credentials,
    get_cache_refresh_minutes,
    # All private functions for test access
    _filter_eligible_issues,
    _get_cache_file_path,
    _load_cache_file,
    _save_cache_file,
    _update_issue_labels_in_cache,
    _log_cache_metrics,
    _log_stale_cache_entries,
)

__all__ = [
    # Public CLI interface
    "execute_coordinator_test",
    "execute_coordinator_run",
    "format_job_output",
    # Public business logic
    "CacheData", 
    "dispatch_workflow",
    "get_cached_eligible_issues",
    "get_eligible_issues", 
    "load_repo_config",
    "validate_repo_config",
    "get_jenkins_credentials",
    "get_cache_refresh_minutes",
    # Private functions (for testing)
    "_filter_eligible_issues",
    "_get_cache_file_path", 
    "_load_cache_file",
    "_save_cache_file",
    "_update_issue_labels_in_cache",
    "_log_cache_metrics",
    "_log_stale_cache_entries",
]
```

### HOW (Backward Compatibility Strategy)
1. **Package-level imports**: Existing `from coordinator import function` still works
2. **Module-level imports**: `from coordinator.commands import function` for specific modules  
3. **Private function access**: Tests can access private functions through package imports
4. **CLI registration**: No changes needed to CLI command registration

### ALGORITHM (Import Update Process)
1. Complete the coordinator/__init__.py with all public exports
2. Update CLI commands/__init__.py to import from coordinator package
3. Update test file imports to use specific module paths
4. Verify all import paths resolve correctly
5. Run tests to ensure no import errors

### DATA (Import Mappings)
**Backward Compatible Imports:**
- `from coordinator import execute_coordinator_test` → Works via __init__.py
- `from coordinator import dispatch_workflow` → Works via __init__.py  

**New Specific Imports:**
- `from coordinator.commands import execute_coordinator_test`
- `from coordinator.core import dispatch_workflow`

**Test-specific Imports:**
- Private functions accessible via coordinator package or direct module imports

## Test Strategy
**Validation Steps:**
1. **Import Tests**: Verify all import statements work without errors
2. **Function Tests**: Run existing test suite to ensure all functions work identically
3. **CLI Tests**: Verify CLI entry points still work through command registration
4. **Backward Compatibility**: Test that old import styles still work

**Test Execution:**
```bash
# Run coordinator-specific tests
python -m pytest tests/cli/commands/test_coordinator.py -v

# Verify CLI still works  
mcp-coder coordinator --help
```

## Success Criteria
- [x] All external imports updated to work with package structure
- [x] Test file imports updated to use specific modules appropriately  
- [x] Backward compatibility maintained for all existing import patterns
- [x] All existing tests pass without any logic changes
- [x] CLI commands still register and execute properly
- [x] Private functions accessible for testing through package imports

## Dependencies
- **Requires**: Steps 2-3 completion (all code moved to appropriate modules)
- **Provides**: Complete working package with proper import structure
- **Next**: Step 5 will perform final verification and cleanup