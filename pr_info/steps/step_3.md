# Step 3: Core Statistics Script (issue_stats.py)

## LLM Prompt
```
Implement Step 3 from pr_info/steps/summary.md: Create the core issue_stats.py script with statistics calculation, ignore labels feature, and display logic.

Follow Test-Driven Development:
1. Write tests for core functions (load config, validate issues, filter ignored labels, group by category)
2. Implement main script following define_labels.py pattern
3. Add command-line argument parsing (--filter, --details, --ignore-labels, --log-level)
4. Implement statistics display with simple text formatting (including validation errors in details mode)
5. Run all code quality checks using MCP tools

Use ONLY MCP filesystem tools for all file operations (mcp__filesystem__*).
Reference workflows/define_labels.py for code patterns and structure.
```

## WHERE: File Paths

### Files to CREATE/MODIFY
```
workflows/issue_stats.py                    # Main script (CREATE)
tests/workflows/test_issue_stats.py         # Complete tests (MODIFY from skeleton)
```

## WHAT: Main Functions

### 1. load_labels_config()
```python
def load_labels_config(config_path: Path) -> dict:
    """Load label configuration from JSON file.
    
    Args:
        config_path: Path to labels.json
        
    Returns:
        Dict with 'workflow_labels' key containing list of label configs
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        ValueError: If required fields are missing
    """
```

### 2. validate_issue_labels()
```python
def validate_issue_labels(
    issue: IssueData,
    valid_status_labels: set[str]
) -> tuple[bool, str]:
    """Validate that issue has exactly one valid status label.
    
    Args:
        issue: IssueData dictionary
        valid_status_labels: Set of valid status label names
        
    Returns:
        Tuple of (is_valid, error_type)
        - is_valid: True if exactly one valid status label
        - error_type: "" if valid, "no_status" or "multiple_status" if invalid
    """
```

### 3. filter_ignored_issues()
```python
def filter_ignored_issues(
    issues: List[IssueData],
    ignore_labels: List[str]
) -> List[IssueData]:
    """Filter out issues that have any of the ignored labels.
    
    Args:
        issues: List of IssueData dictionaries
        ignore_labels: List of label names to ignore
        
    Returns:
        Filtered list of issues without any ignored labels
    """
```

### 4. group_issues_by_category()
```python
def group_issues_by_category(
    issues: List[IssueData],
    labels_config: dict
) -> dict[str, dict[str, List[IssueData]]]:
    """Group issues by category and status label.
    
    Args:
        issues: List of IssueData dictionaries
        labels_config: Label configuration from JSON
        
    Returns:
        Dict structure:
        {
            'human_action': {
                'status-01:created': [issue1, issue2],
                'status-04:plan-review': []
            },
            'bot_pickup': {...},
            'bot_busy': {...},
            'errors': {
                'no_status': [issue_without_label],
                'multiple_status': [issue_with_multiple]
            }
        }
    """
```

### 5. display_statistics()
```python
def display_statistics(
    grouped_issues: dict,
    labels_config: dict,
    filter_category: str = "all",
    show_details: bool = False
) -> None:
    """Display formatted statistics to console.
    
    Args:
        grouped_issues: Output from group_issues_by_category()
        labels_config: Label configuration for display order
        filter_category: 'all', 'human', or 'bot'
        show_details: If True, show individual issues with links
    """
```

### 6. parse_arguments()
```python
def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Namespace with: project_dir, log_level, filter, details, ignore_labels
    """
```

### 7. main()
```python
def main() -> None:
    """Main entry point for issue statistics workflow."""
```

## HOW: Integration Points

### Imports
```python
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List

from mcp_coder.utils import get_github_repository_url
from mcp_coder.utils.github_operations.issue_manager import IssueManager, IssueData
from mcp_coder.utils.log_utils import setup_logging
from mcp_coder.workflows.utils import resolve_project_dir
```

### Simple URL Formatting
```python
def format_issue_url(issue: IssueData, repo_url: str) -> str:
    """Format plain text URL for an issue.
    
    Args:
        issue: IssueData dictionary
        repo_url: Repository URL
        
    Returns:
        Full issue URL as string
    """
    return f"{repo_url}/issues/{issue['number']}"
```

### Title Truncation
```python
def truncate_title(title: str, max_length: int = 80) -> str:
    """Truncate title to max length with ellipsis.
    
    Args:
        title: Original title
        max_length: Maximum length (default: 80)
        
    Returns:
        Truncated title with "..." if needed
    """
    if len(title) <= max_length:
        return title
    return title[:max_length-3] + "..."
```

## ALGORITHM: Main Workflow

```
FUNCTION main():
    args = parse_arguments()
    setup_logging(args.log_level)
    project_dir = resolve_project_dir(args.project_dir)
    
    # Load configuration
    config_path = project_dir.parent / "workflows" / "config" / "labels.json"
    labels_config = load_labels_config(config_path)
    
    # Fetch issues (open only)
    issue_manager = IssueManager(project_dir)
    issues = issue_manager.list_issues(state="open", include_pull_requests=False)
    
    # Build ignore list (JSON defaults + CLI additions)
    ignore_labels = labels_config.get('ignore_labels', []) + (args.ignore_labels or [])
    
    # Filter out ignored issues
    filtered_issues = filter_ignored_issues(issues, ignore_labels)
    
    # Group by category and validate
    grouped = group_issues_by_category(filtered_issues, labels_config)
    
    # Display statistics
    display_statistics(grouped, labels_config, args.filter, args.details)
```

## ALGORITHM: Filter Ignored Issues

```
FUNCTION filter_ignored_issues(issues, ignore_labels):
    IF ignore_labels IS EMPTY:
        RETURN issues  # No filtering needed
    
    filtered = []
    FOR EACH issue IN issues:
        has_ignored_label = FALSE
        FOR EACH label IN issue.labels:
            IF label IN ignore_labels:
                has_ignored_label = TRUE
                BREAK
        
        IF NOT has_ignored_label:
            APPEND issue TO filtered
    
    RETURN filtered
```

## ALGORITHM: Issue Grouping

```
FUNCTION group_issues_by_category(issues, labels_config):
    # Build lookup maps
    label_to_category = MAP label.name -> label.category FROM labels_config
    valid_status_labels = SET of all label.name FROM labels_config
    
    # Initialize result structure
    result = {
        'human_action': {},
        'bot_pickup': {},
        'bot_busy': {},
        'errors': {'no_status': [], 'multiple_status': []}
    }
    
    # Initialize empty lists for each label
    FOR EACH label IN labels_config:
        result[label.category][label.name] = []
    
    # Process each issue
    FOR EACH issue IN issues:
        status_labels = FILTER issue.labels BY valid_status_labels
        
        IF len(status_labels) == 0:
            APPEND issue TO result['errors']['no_status']
        ELSE IF len(status_labels) > 1:
            APPEND issue TO result['errors']['multiple_status']
        ELSE:
            label_name = status_labels[0]
            category = label_to_category[label_name]
            APPEND issue TO result[category][label_name]
    
    RETURN result
```

## DATA: Display Format

### Summary Display (--details not set)
```
Ignored 5 issues with labels: wontfix, duplicate

=== Human Action Required ===
  status-01:created           3 issues
  status-04:plan-review       1 issue
  status-07:code-review       0 issues
  status-10:pr-created        0 issues

=== Bot Should Pickup ===
  status-02:awaiting-planning 2 issues
  status-05:plan-ready        1 issue
  status-08:ready-pr          0 issues

=== Bot Busy ===
  status-03:planning          0 issues
  status-06:implementing      1 issue
  status-09:pr-creating       0 issues

=== Validation Errors ===
  No status label: 2 issues
  Multiple status labels: 1 issue

Total: 20 issues (17 valid, 3 errors, 5 ignored)
```

### Details Display (--details flag)
```
Ignored 5 issues with labels: wontfix, duplicate

=== Human Action Required ===
  status-01:created           3 issues
    - #123: Fix login bug
      https://github.com/owner/repo/issues/123
    - #145: Add new feature with a very long title that gets truncated with...
      https://github.com/owner/repo/issues/145
    - #167: Update documentation
      https://github.com/owner/repo/issues/167
  
  status-04:plan-review       1 issue
    - #200: Refactor authentication module
      https://github.com/owner/repo/issues/200

...

=== Validation Errors ===
  No status label: 2 issues
    - #201: Some issue without labels
      https://github.com/owner/repo/issues/201
    - #202: Another unlabeled issue
      https://github.com/owner/repo/issues/202
  
  Multiple status labels: 1 issue
    - #203: Issue with too many status labels
      https://github.com/owner/repo/issues/203
```

### Filter Modes
- `--filter all` (default): Show all categories
- `--filter human`: Show only human_action category
- `--filter bot`: Show only bot_pickup and bot_busy categories

### Ignore Labels
- JSON config: `"ignore_labels": ["wontfix", "duplicate"]` - default ignored labels
- CLI: `--ignore-labels "wontfix" --ignore-labels "on hold"` - add more ignored labels
- Combined: JSON defaults + CLI additions = full ignore list
- Multiple flags supported for labels with spaces

## Implementation Checklist
- [ ] Implement load_labels_config() with error handling
- [ ] Implement validate_issue_labels() for single status check
- [ ] Implement filter_ignored_issues() to remove ignored labels
- [ ] Implement group_issues_by_category() with proper structure
- [ ] Implement display_statistics() with simple formatting and validation errors in details mode
- [ ] Implement format_issue_url() for plain URLs
- [ ] Implement truncate_title() for long titles
- [ ] Implement parse_arguments() with all flags (--filter, --details, --ignore-labels)
- [ ] Implement main() orchestrator function with ignore labels support
- [ ] Write comprehensive unit tests (12+ test functions)
- [ ] Test with test_labels.json fixture
- [ ] Run all code quality checks

## Test Functions (test_issue_stats.py)

### Configuration Tests
```python
def test_load_labels_config_valid()
def test_load_labels_config_missing_file()
def test_load_labels_config_invalid_json()
def test_load_labels_config_with_ignore_labels()
```

### Validation Tests
```python
def test_validate_issue_labels_single_valid()
def test_validate_issue_labels_no_status()
def test_validate_issue_labels_multiple_status()
```

### Filtering Tests
```python
def test_filter_ignored_issues_no_ignore_list()
def test_filter_ignored_issues_with_ignored_labels()
def test_filter_ignored_issues_labels_with_spaces()
```

### Grouping Tests
```python
def test_group_issues_by_category_empty_list()
def test_group_issues_by_category_all_valid()
def test_group_issues_by_category_with_errors()
def test_group_issues_by_category_zero_counts_included()
```

### Formatting Tests
```python
def test_format_issue_url()
def test_truncate_title_short()
def test_truncate_title_long()
```

### Display Tests
```python
def test_display_statistics_summary_mode()
def test_display_statistics_details_mode_with_errors()
```

### Integration Tests
```python
def test_main_workflow_with_mocked_data()
def test_parse_arguments_default_values()
def test_parse_arguments_all_flags()
def test_parse_arguments_multiple_ignore_labels()
```

## Quality Checks
```python
# Fast unit tests:
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)

# Type checking:
mcp__code-checker__run_mypy_check()

# Code quality:
mcp__code-checker__run_pylint_check()
```

## Expected Test Output
```
tests/workflows/test_issue_stats.py::test_load_labels_config_valid PASSED
tests/workflows/test_issue_stats.py::test_validate_issue_labels_single_valid PASSED
tests/workflows/test_issue_stats.py::test_group_issues_by_category_all_valid PASSED
tests/workflows/test_issue_stats.py::test_format_issue_url PASSED
tests/workflows/test_issue_stats.py::test_truncate_title_long PASSED
... (10+ tests total)
```

## Notes
- Follow exact same code structure as define_labels.py
- Use INFO level logging for workflow progress
- Fail fast with sys.exit(1) on errors
- Keep display logic simple (plain text formatting)
- Plain URLs on separate lines for easy copying
- Title truncation at 80 chars for readable console output
