# Step 1: Core Data Structures and Manager Foundation

## LLM Prompt
```
I'm implementing issue #213 - CI Pipeline Result Analysis Tool. Please refer to pr_info/steps/summary.md for the full architectural overview.

In this step, create the foundational components:
1. TypedDict data structures for CI status and failure data
2. Basic CIResultsManager class extending BaseGitHubManager  
3. Core validation methods
4. Unit tests for the foundation

Follow TDD approach - write tests first, then implement minimal code to pass.
Follow existing patterns from IssueManager and other GitHub operations managers.
```

## WHERE: File Locations
```
tests/utils/github_operations/test_ci_results_manager.py    # Create (tests first)
src/mcp_coder/utils/github_operations/ci_results_manager.py # Create (implementation)
```

## WHAT: Main Components

### Data Structures
```python
class CIStatusData(TypedDict):
    run: Dict[str, Any]        # {id, status, conclusion, branch, commit_sha, created_at, url}
    jobs: List[Dict[str, Any]] # [{id, name, status, conclusion, started_at, completed_at}]

class CIFailureData(TypedDict):
    job_logs: Dict[str, str]           # {job_name: log_content}  
    test_failures: List[Dict[str, Any]] # [{test_name, failure_message, file, line}]
```

### Manager Class Foundation
```python
class CIResultsManager(BaseGitHubManager):
    def __init__(self, project_dir: Optional[Path] = None, repo_url: Optional[str] = None)
    def _validate_branch_name(self, branch: str) -> bool
    def _validate_run_id(self, run_id: int) -> bool
```

## HOW: Integration Points

### Imports
```python
from .base_manager import BaseGitHubManager, _handle_github_errors
from mcp_coder.utils.log_utils import log_function_call
from typing import Dict, List, Optional, TypedDict, Any
```

### Decorators to Use
- `@log_function_call` on public methods
- `@_handle_github_errors(default_return=...)` on methods that can fail

## ALGORITHM: Core Logic

### Validation Methods
```python
def _validate_branch_name(self, branch: str) -> bool:
    # 1. Check if branch is non-empty string
    # 2. Check if branch contains valid characters
    # 3. Log error if invalid
    # 4. Return boolean result
```

### Manager Initialization
```python
def __init__(self, project_dir=None, repo_url=None):
    # 1. Call super().__init__ with same parameters
    # 2. No additional setup needed for now
    # 3. Rely on BaseGitHubManager for GitHub client setup
```

## DATA: Test Cases and Expected Returns

### Test Structure
```python
class TestCIResultsManagerFoundation:
    def test_initialization_with_project_dir()
    def test_initialization_with_repo_url() 
    def test_initialization_validation()
    def test_validate_branch_name()
    def test_validate_run_id()
```

### Validation Test Cases
```python
# Branch validation
assert manager._validate_branch_name("feature/xyz") == True
assert manager._validate_branch_name("main") == True  
assert manager._validate_branch_name("") == False
assert manager._validate_branch_name(None) == False

# Run ID validation
assert manager._validate_run_id(12345) == True
assert manager._validate_run_id(0) == False
assert manager._validate_run_id(-1) == False
```

## Success Criteria
- [ ] TypedDict classes defined and importable
- [ ] CIResultsManager extends BaseGitHubManager correctly
- [ ] Validation methods work as expected
- [ ] All tests pass
- [ ] Code follows existing manager patterns
- [ ] Proper error handling and logging setup