# Step 2: Move Core Business Logic to core.py

## Objective
Move all business logic functions, utilities, and data structures from coordinator.py to core.py while preserving exact functionality and maintaining test compatibility.

## LLM Prompt
```
Based on summary.md, implement Step 2 of the coordinator module refactoring. Move all business logic functions from the original coordinator.py to core.py. This includes configuration management, caching system, issue filtering, workflow dispatch, and utility functions. Preserve exact function signatures, docstrings, and logic. Update imports as needed.
```

## Implementation Details

### WHERE (Files)
- **Source**: `src/mcp_coder/cli/commands/coordinator.py` 
- **Target**: `src/mcp_coder/cli/commands/coordinator/core.py`

### WHAT (Functions to Move)
**Configuration Management:**
```python
def load_repo_config(repo_name: str) -> dict[str, Optional[str]]
def validate_repo_config(repo_name: str, config: dict[str, Optional[str]]) -> None
def get_jenkins_credentials() -> tuple[str, str, str]  
def get_cache_refresh_minutes() -> int
```

**Caching System:**
```python
class CacheData(TypedDict): ...
def get_cached_eligible_issues(...) -> List[IssueData]
def _load_cache_file(cache_file_path: Path) -> CacheData
def _save_cache_file(cache_file_path: Path, cache_data: CacheData) -> bool
def _get_cache_file_path(repo_identifier: RepoIdentifier) -> Path
def _log_cache_metrics(action: str, repo_name: str, **kwargs: Any) -> None
def _log_stale_cache_entries(...) -> None
def _update_issue_labels_in_cache(...) -> None
```

**Issue Filtering:**
```python
def get_eligible_issues(issue_manager: IssueManager, log_level: str = "INFO") -> list[IssueData]
def _filter_eligible_issues(issues: List[IssueData]) -> List[IssueData]
```

**Workflow Dispatch:**
```python
def dispatch_workflow(...) -> None
```

### HOW (Integration Points)
**Imports for core.py:**
```python
import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict
from urllib.parse import quote

from ....utils.github_operations.github_utils import RepoIdentifier
from ....utils.github_operations.issue_branch_manager import IssueBranchManager  
from ....utils.github_operations.issue_manager import IssueData, IssueManager
from ....utils.github_operations.label_config import load_labels_config
from ....utils.jenkins_operations.client import JenkinsClient
from ....utils.jenkins_operations.models import JobStatus
from ....utils.timezone_utils import (
    format_for_cache,
    is_within_duration,
    now_utc,
    parse_iso_timestamp,
)
from ....utils.user_config import (
    create_default_config,
    get_config_file_path, 
    get_config_value,
    load_config,
)
```

### ALGORITHM (Code Movement)
1. Copy all imports needed by business logic functions to core.py
2. Move CacheData TypedDict definition  
3. Move all configuration management functions
4. Move all caching system functions (maintaining private _prefixes)
5. Move all issue filtering functions
6. Move workflow dispatch function
7. Verify all internal function calls still work within core.py

### DATA (Function Signatures)
- **Input**: All function signatures preserved exactly as in original
- **Output**: All return types and data structures identical
- **Internal**: All private helper functions maintain _ prefix convention

## Test Strategy
**Test Approach:**
1. Update test imports to import from `coordinator.core` 
2. Run existing tests to verify all business logic functions work unchanged
3. Test both direct imports and imports through coordinator package __init__.py

**Test File Updates:**
```python
# In tests/cli/commands/test_coordinator.py
from mcp_coder.cli.commands.coordinator.core import (
    load_repo_config,
    validate_repo_config, 
    get_jenkins_credentials,
    get_cached_eligible_issues,
    # etc...
)
```

## Success Criteria
- [x] All business logic functions moved to core.py with exact signatures
- [x] All imports updated correctly in core.py
- [x] All private helper functions maintain proper encapsulation
- [x] Tests pass when importing from core.py directly
- [x] Tests pass when importing through coordinator package
- [x] No circular import dependencies created

## Dependencies  
- **Requires**: Step 1 completion (package structure exists)
- **Provides**: Core business logic separated and ready for CLI module creation
- **Next**: Step 3 will move CLI entry points to commands.py