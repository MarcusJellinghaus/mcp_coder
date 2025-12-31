# Files and Modules Overview

## Summary
This document lists all files and modules that will be created or modified during the GitHub API caching implementation.

## New Files Created

### Test Files
- `tests/utils/test_coordinator_cache.py`
  - **Purpose**: Unit tests for core cache logic functions
  - **Functions**: Tests for cache file operations, duplicate protection, refresh logic
  - **Dependencies**: pytest, unittest.mock, datetime, pathlib

- `tests/utils/test_coordinator_cache_integration.py` 
  - **Purpose**: Integration tests for complete caching workflow
  - **Functions**: End-to-end scenarios from CLI to cache files to GitHub API
  - **Dependencies**: pytest, CLI test fixtures, mocked GitHub responses

### Cache Directory (Auto-created)
- `~/.mcp_coder/coordinator_cache/`
  - **Purpose**: Storage location for cache files
  - **Files**: `{owner}_{repo}.issues.json` (e.g., `anthropics_claude-code.issues.json`)
  - **Naming**: Derived from full repo identifier `owner/repo` by replacing `/` with `_`
  - **Structure**: JSON files with last_checked timestamps and issue data

## Modified Files

### Core Implementation
- `src/mcp_coder/cli/commands/coordinator.py`
  - **Changes**: 
    - Add `get_cached_eligible_issues()` function
    - Add cache helper functions (`_load_cache_file`, `_save_cache_file`, etc.)
    - Add `get_cache_refresh_minutes()` config reading function
    - Add `--force-refresh` CLI argument to run subcommand
    - Modify `execute_coordinator_run()` to use cached version
  - **Lines Added**: ~200 (cache function + helpers + integration)

- `src/mcp_coder/utils/github_operations/issue_manager.py`
  - **Changes**:
    - Extend `list_issues()` with optional `since: Optional[datetime] = None` parameter
    - Add datetime import if not present
  - **Lines Added**: ~10 (parameter addition + conditional logic)

### Test Files
- `tests/cli/commands/test_coordinator.py` (existing)
  - **Changes**:
    - Add test functions for cache integration scenarios
    - Add test functions for CLI flag handling
    - Add mock fixtures for cache directory and config
  - **Lines Added**: ~150 (integration test scenarios)

- `tests/utils/github_operations/test_issue_manager.py` (existing)
  - **Changes**:
    - Add test functions for `list_issues()` with `since` parameter
    - Add test fixtures for datetime scenarios
  - **Lines Added**: ~60 (unit tests for extended method)

## Module Dependencies

### New Imports Added
```python
# In coordinator.py
from datetime import datetime, timedelta
from pathlib import Path
import json

# In issue_manager.py  
from datetime import datetime  # (if not already imported)
```

### Configuration Schema
```toml
# Addition to ~/.mcp_coder/config.toml
[coordinator]
cache_refresh_minutes = 1440  # Optional, defaults to 1440 (24 hours)
```

## File Size Impact

### New Code
- **Cache Logic**: ~200 lines (coordinator.py)
- **GitHub API Extension**: ~10 lines (issue_manager.py) 
- **Unit Tests**: ~200 lines (across test files)
- **Integration Tests**: ~100 lines (in test_coordinator.py)
- **Total New**: ~510 lines of code

### Modified Code  
- **CLI Integration**: ~10 lines modified in existing functions
- **Argument Parser**: ~5 lines added to existing setup
- **Total Modified**: ~15 lines of existing code changed

## Architecture Impact

### Component Relationships
```
CLI (coordinator.py)
  └── get_cached_eligible_issues()
      ├── Cache File I/O (JSON, atomic writes)
      ├── Configuration Reading
      ├── Staleness Detection & Logging
      └── IssueManager.list_issues(since=...)
          └── GitHub API (PyGithub)
```

### Error Flow
```
Cache Error → Log Warning → Fallback to get_eligible_issues() → Continue Normally
```

### Data Flow
```
GitHub API → Cache Files → Filtered Results → Coordinator Workflow
```

This implementation maintains the existing architecture while adding a transparent optimization layer that never affects correctness.