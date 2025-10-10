# Step 2: Prerequisites Validation

## Objective

Implement validation for repository cleanliness and GitHub issue existence.

## Files to Modify

- `workflows/create_plan.py` - Add prerequisites validation function

## Implementation Details

### WHERE
- `workflows/create_plan.py` - Add `check_prerequisites()` function

### WHAT

```python
def check_prerequisites(project_dir: Path, issue_number: int) -> tuple[bool, IssueData]:
    """Validate prerequisites for plan creation workflow.
    
    Returns:
        Tuple of (success: bool, issue_data: IssueData)
    """
```

### HOW

**Imports:**
```python
from mcp_coder.utils import is_working_directory_clean
from mcp_coder.utils.github_operations.issue_manager import IssueManager, IssueData
```

**Function structure:**
- Check git working directory is clean
- Fetch issue from GitHub using IssueManager
- Validate issue exists and is accessible
- Log each check with ✓ or ✗ indicators

### ALGORITHM

```
1. Log "Checking prerequisites for plan creation..."
2. Check if git working directory is clean
   - If not clean: log error, return (False, empty_issue_data)
   - If clean: log "✓ Git working directory is clean"
3. Try to fetch issue using IssueManager(project_dir).get_issue(issue_number)
   - If issue.number == 0 (not found): log error, return (False, empty_issue_data)
   - If exception: log error, return (False, empty_issue_data)
   - If success: log "✓ Issue #X exists: 'Title'"
4. Log "All prerequisites passed"
5. Return (True, issue_data)
```

### DATA

**Returns:**
```python
tuple[bool, IssueData]
# IssueData contains: number, title, body, state, labels, assignees, user, created_at, updated_at, url, locked
```

**Empty IssueData on failure:**
```python
IssueData(
    number=0, title="", body="", state="", labels=[], assignees=[],
    user=None, created_at=None, updated_at=None, url="", locked=False
)
```

## Testing

Create `tests/workflows/create_plan/test_prerequisites.py`:

```python
def test_check_prerequisites_success()
def test_check_prerequisites_dirty_repo()
def test_check_prerequisites_issue_not_found()
def test_check_prerequisites_github_api_error()
def test_check_prerequisites_logs_issue_details()
```

## Acceptance Criteria

- [ ] Function validates git repository is clean
- [ ] Function fetches issue from GitHub
- [ ] Function validates issue exists (number != 0)
- [ ] Function returns success flag and issue data
- [ ] Function logs each check with clear indicators
- [ ] Function handles GitHub API errors gracefully
- [ ] All tests pass with mocked GitHub API

## LLM Prompt for Implementation

```
Please implement Step 2 of the create_plan workflow.

Reference the summary at pr_info/steps/summary.md and step 1 at pr_info/steps/step_1.md.

Add the check_prerequisites() function to workflows/create_plan.py.

Key requirements:
- Use is_working_directory_clean() from utils.git_operations
- Use IssueManager from utils.github_operations.issue_manager
- Follow logging pattern from create_pr.py with ✓ and ✗ indicators
- Return tuple of (bool, IssueData) for success/failure handling
- Handle all error cases (dirty repo, missing issue, API errors)

Implement the tests as specified with proper mocking of GitHub API.
```
