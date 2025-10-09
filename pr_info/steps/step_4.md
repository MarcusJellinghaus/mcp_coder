# Step 4: Add Linked Branches Query Functionality

## LLM Prompt
```
Read pr_info/steps/summary.md and this step file. Implement get_linked_branches() method in IssueBranchManager following TDD approach:
1. First write unit tests
2. Then implement the method using GitHub issue timeline events
Query timeline for branch references associated with the issue.
```

## WHERE
- **Test File**: `tests/utils/github_operations/test_issue_branch_manager.py` (extend)
- **Implementation File**: `src/mcp_coder/utils/github_operations/issue_branch_manager.py` (extend)

## WHAT

### Test Functions
```python
class TestGetLinkedBranches:
    def test_get_linked_branches_success(mock_github, tmp_path) -> None
    def test_get_linked_branches_empty_list(mock_github, tmp_path) -> None
    def test_get_linked_branches_multiple_branches(mock_github, tmp_path) -> None
    def test_get_linked_branches_invalid_issue_number(tmp_path) -> None
    def test_get_linked_branches_issue_not_found(mock_github, tmp_path) -> None
    def test_get_linked_branches_auth_error_raises(mock_github, tmp_path) -> None
    def test_get_linked_branches_filters_non_branch_events(mock_github, tmp_path) -> None
```

### Implementation Method
```python
@log_function_call
@_handle_github_errors(default_return=[])
def get_linked_branches(self, issue_number: int) -> List[str]
```

## HOW

### Integration Points
1. **Decorators**: `@log_function_call`, `@_handle_github_errors(default_return=[])`
2. **GitHub API**: 
   - `repo.get_issue(issue_number)` - Get issue object
   - `issue.get_timeline()` - Get timeline events
   - Filter events by type: `"cross-referenced"` or `"head_ref_restored"`
3. **Error Handling**: Return empty list on errors (non-auth)

### Timeline Event Types to Check
- `"cross-referenced"` - Branch mentioned in issue/PR
- `"head_ref_restored"` - Branch restored after deletion
- Extract branch names from event source/commit references

## ALGORITHM

### Test Algorithm (test_get_linked_branches_success)
```
1. Setup: Git repo, mock GitHub API
2. Mock: Timeline events with branch references
3. Execute: branches = manager.get_linked_branches(123)
4. Assert: Correct branch names returned
5. Assert: issue.get_timeline() was called
```

### Implementation Algorithm
```
1. Validate issue_number (return [] if invalid)
2. Get repository (return [] if fails)
3. Get issue object: repo.get_issue(issue_number)
4. Get timeline events: issue.get_timeline()
5. Filter events for branch references
6. Extract branch names from events
7. Return unique list of branch names
```

## DATA

### Input
- `issue_number: int` - Issue number to query

### Output
- `List[str]` - List of branch names linked to the issue

### Examples
```python
# Issue with linked branches
get_linked_branches(123) → ["123-fix-bug", "feature/fix-123"]

# Issue with no linked branches
get_linked_branches(456) → []

# Invalid issue number
get_linked_branches(0) → []
```

## Implementation Pattern

```python
@log_function_call
@_handle_github_errors(default_return=[])
def get_linked_branches(self, issue_number: int) -> List[str]:
    """Get all branches linked to an issue.
    
    Queries GitHub issue timeline events to find branch references.
    
    Args:
        issue_number: Issue number to query
        
    Returns:
        List of branch names linked to the issue
        
    Raises:
        GithubException: For authentication or permission errors
    """
    # 1. Validate issue_number
    if not isinstance(issue_number, int) or issue_number <= 0:
        logger.error(f"Invalid issue number: {issue_number}")
        return []
    
    # 2. Get repository
    repo = self._get_repository()
    if repo is None:
        logger.error("Failed to get repository")
        return []
    
    # 3. Get issue
    issue = repo.get_issue(issue_number)
    
    # 4. Get timeline events
    timeline = issue.get_timeline()
    
    # 5. Extract branch names from events
    branches = []
    for event in timeline:
        # Check event type and extract branch name
        if event.event == "cross-referenced":
            # Extract branch from cross-reference
            if hasattr(event.source, 'issue') and event.source.issue:
                # This is a PR reference
                if hasattr(event.source.issue, 'pull_request'):
                    pr = event.source.issue.pull_request
                    if pr and hasattr(pr, 'head'):
                        branch_name = pr.head.ref
                        branches.append(branch_name)
    
    # 6. Return unique branch names
    return list(set(branches))
```

## Timeline Event Structure

PyGithub timeline events have this structure:
```python
event.event          # Event type string
event.source         # Source object (PR, commit, etc.)
event.commit_id      # Commit SHA if applicable
```

For cross-referenced events:
```python
event.source.issue                    # Issue/PR object
event.source.issue.pull_request       # PR object if it's a PR
event.source.issue.pull_request.head  # PR head ref
event.source.issue.pull_request.head.ref  # Branch name
```

## Test Mock Structure

```python
# Mock timeline event for a branch reference
mock_event = MagicMock()
mock_event.event = "cross-referenced"

# Mock PR structure
mock_pr = MagicMock()
mock_pr.head.ref = "123-fix-bug"

# Mock source
mock_issue = MagicMock()
mock_issue.pull_request = mock_pr

mock_event.source.issue = mock_issue

# Mock get_timeline to return events
mock_github_issue.get_timeline.return_value = [mock_event]
```

## Edge Cases to Handle

1. **Non-PR cross-references**: Filter out issue-only references
2. **Multiple events for same branch**: Return unique names only
3. **Deleted branches**: May still appear in timeline
4. **Empty timeline**: Return empty list
5. **Invalid event structures**: Skip malformed events

## Validation Strategy

```python
# Safe attribute access with hasattr checks
if hasattr(event, 'source') and event.source:
    if hasattr(event.source, 'issue') and event.source.issue:
        if hasattr(event.source.issue, 'pull_request'):
            pr = event.source.issue.pull_request
            if pr and hasattr(pr, 'head') and pr.head:
                if hasattr(pr.head, 'ref'):
                    branch_name = pr.head.ref
                    branches.append(branch_name)
```
