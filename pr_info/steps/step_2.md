# Step 2: Issue Filtering Logic (TDD)

## Reference
**Implementation Plan:** See `pr_info/steps/summary.md` for complete architectural overview.

## Objective
Implement issue filtering and prioritization logic to identify eligible issues for automation.

## WHERE

**Test File:**
- `tests/cli/commands/test_coordinator.py`
- Add new test class: `TestGetEligibleIssues`

**Implementation File:**
- `src/mcp_coder/cli/commands/coordinator.py`
- Add function after `load_label_config()`

## WHAT

### Test Class (TDD First)

```python
class TestGetEligibleIssues:
    """Tests for get_eligible_issues function."""
    
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.load_label_config")
    def test_get_eligible_issues_filters_by_bot_pickup_labels() -> None:
        """Test filtering issues by bot_pickup labels."""
        # Mock issue list with mixed labels
        # Verify only bot_pickup issues returned
        
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.load_label_config")
    def test_get_eligible_issues_excludes_ignore_labels() -> None:
        """Test exclusion of issues with ignore_labels."""
        # Mock issue with "Overview" label
        # Verify issue excluded from results
        
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.load_label_config")
    def test_get_eligible_issues_priority_order() -> None:
        """Test issues sorted by priority (08 → 05 → 02)."""
        # Mock issues with different bot_pickup labels
        # Verify sorted: status-08, then status-05, then status-02
        
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.load_label_config")
    def test_get_eligible_issues_empty_result() -> None:
        """Test handling when no eligible issues found."""
        # Mock empty issue list
        # Verify returns empty list without error
```

### Main Function Signature

```python
def get_eligible_issues(
    issue_manager: IssueManager,
    log_level: str = "INFO"
) -> list[IssueData]:
    """Get issues ready for automation, sorted by priority.
    
    Args:
        issue_manager: IssueManager instance for GitHub API calls
        log_level: Logging level for debug output
        
    Returns:
        List of IssueData sorted by priority:
        1. status-08:ready-pr (highest priority)
        2. status-05:plan-ready
        3. status-02:awaiting-planning (lowest priority)
        
    Raises:
        GithubException: If GitHub API errors occur
    """
```

### Constants to Add

```python
# Priority order for processing issues (highest to lowest)
PRIORITY_ORDER = [
    "status-08:ready-pr",
    "status-05:plan-ready",
    "status-02:awaiting-planning"
]
```

## HOW

### Integration Points

**Imports:**
```python
from ..utils.github_operations.issue_manager import IssueManager, IssueData
```

**Usage in coordinator run:**
```python
def execute_coordinator_run(args: Namespace) -> int:
    # ... load config, create managers
    
    # Get eligible issues
    eligible_issues = get_eligible_issues(issue_manager, args.log_level)
    
    if not eligible_issues:
        logger.info(f"No eligible issues found in {repo_name}")
        return 0
        
    # Process each issue
    for issue in eligible_issues:
        # ... dispatch workflow
```

## ALGORITHM

```
1. Load label configuration (bot_pickup, ignore_labels)
2. Query all open issues via issue_manager.list_issues(state="open")
3. Filter issues:
   - Must have exactly ONE bot_pickup label
   - Must NOT have any ignore_labels
4. Sort filtered issues by priority:
   - Create priority map: {label: index in PRIORITY_ORDER}
   - Sort by priority (lower index = higher priority)
5. Log filtering results (count before/after)
6. Return sorted list
```

## DATA

### Input: IssueData from GitHub
```python
IssueData = {
    "number": 123,
    "title": "Implement feature X",
    "labels": ["status-05:plan-ready", "enhancement"],
    "state": "open",
    # ... other fields
}
```

### Output: Filtered and Sorted List
```python
[
    IssueData(number=124, labels=["status-08:ready-pr"]),  # Highest priority
    IssueData(number=125, labels=["status-08:ready-pr"]),
    IssueData(number=123, labels=["status-05:plan-ready"]),
    IssueData(number=122, labels=["status-02:awaiting-planning"])  # Lowest priority
]
```

### Filtering Logic Examples

**Include:**
- `["status-02:awaiting-planning"]` → ✅
- `["status-05:plan-ready", "enhancement"]` → ✅
- `["status-08:ready-pr", "bug"]` → ✅

**Exclude:**
- `["status-01:created"]` → ❌ (not bot_pickup)
- `["status-05:plan-ready", "Overview"]` → ❌ (has ignore_label)
- `["status-05:plan-ready", "status-08:ready-pr"]` → ❌ (multiple bot_pickup labels)
- `[]` → ❌ (no bot_pickup label)

## Implementation Notes

1. **Single Bot Pickup Label:** Issues should have exactly ONE bot_pickup label
   - Multiple bot_pickup labels indicate misconfiguration → skip issue
   
2. **Priority Mapping:** Use dict for O(1) lookup during sorting
   ```python
   priority_map = {label: i for i, label in enumerate(PRIORITY_ORDER)}
   ```

3. **Logging:** Use logger.debug for detailed filtering info
   ```python
   logger.debug(f"Found {len(all_issues)} open issues")
   logger.debug(f"Filtered to {len(eligible)} eligible issues")
   ```

4. **Error Handling:** Let GitHub API exceptions bubble up (handled by caller)

## LLM Prompt for Implementation

```
Implement Step 2 of the coordinator run feature as described in pr_info/steps/summary.md.

Task: Add issue filtering logic to src/mcp_coder/cli/commands/coordinator.py

Requirements:
1. First add PRIORITY_ORDER constant after DEFAULT_TEST_COMMAND

2. Write tests in tests/cli/commands/test_coordinator.py:
   - TestGetEligibleIssues class with 4 test methods
   - Mock IssueManager.list_issues() to return test issues
   - Mock load_label_config() to return label config
   - Test filtering, exclusions, priority sorting, empty results

3. Then implement get_eligible_issues() function:
   - Load label config
   - Query open issues
   - Filter by bot_pickup labels (exactly one required)
   - Exclude issues with ignore_labels
   - Sort by PRIORITY_ORDER (status-08 → 05 → 02)
   - Return sorted list

4. Run code quality checks:
   - mcp__code-checker__run_pytest_check (fast unit tests only)
   - mcp__code-checker__run_pylint_check
   - mcp__code-checker__run_mypy_check

Follow the exact algorithm and data structures in step_2.md.
Use existing IssueManager and IssueData types.
```

## Test Execution

**Run fast unit tests only:**
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"],
    show_details=False
)
```

## Success Criteria

- ✅ All 4 tests pass
- ✅ Filters issues by bot_pickup labels correctly
- ✅ Excludes issues with ignore_labels
- ✅ Sorts by priority (08 → 05 → 02)
- ✅ Handles edge cases (empty list, no eligible issues)
- ✅ Pylint/mypy checks pass
- ✅ Logging provides useful debug info
