# GitHub Issues API Implementation - Summary

## Overview
Add GitHub Issues management capabilities to mcp_coder, following the same patterns as the existing Pull Request management. This enables complete issue lifecycle automation within the existing workflow system.

## Core Requirements
- **Read issues**: Get single issue, list issues with filtering
- **Create issues**: Create new issues with title, body, labels
- **Manage issue lifecycle**: Close and reopen issues 
- **Label management**: Add, remove, set labels on issues
- **Comment management**: Create, read, edit, delete issue comments

## Architectural Changes

### New Components
- **IssueManager class**: Main API class in `src/mcp_coder/utils/github_operations/issue_manager.py` inheriting from BaseGitHubManager
- **Data structures**: TypedDict classes for IssueData, CommentData, LabelData
- **Integration tests**: Test suite with `github_integration` marker
- **Error handling decorator**: `_handle_github_errors` decorator in BaseGitHubManager for consistent error handling across all GitHub managers

### Design Principles
- **Inherit from BaseGitHubManager**: Reuse GitHub client setup, repository access, and validation patterns
- **Structured data**: TypedDict return types for consistent API
- **Configuration reuse**: Leverage existing GitHub token configuration
- **Comprehensive validation**: Input validation with detailed error messages
- **Consistent error handling**: Decorator-based error handling that raises exceptions for auth errors (401/403), returns empty values for other GitHub errors, and lets programming errors propagate

## Files Created or Modified

### New Files
```
src/mcp_coder/utils/github_operations/issue_manager.py    # Core IssueManager class
tests/utils/github_operations/test_issue_manager.py       # Unit tests with mocking  
tests/utils/github_operations/test_issue_manager_integration.py  # Integration tests
tests/utils/github_operations/test_base_manager.py        # Decorator tests
```

### Modified Files
```
src/mcp_coder/utils/github_operations/__init__.py         # Export IssueManager class
src/mcp_coder/utils/github_operations/base_manager.py     # Add error handling decorator
src/mcp_coder/utils/github_operations/pr_manager.py       # Apply decorator, cleanup
src/mcp_coder/utils/github_operations/labels_manager.py   # Apply decorator
```

## Implementation Steps

### Phase 1: Core Issue Management (Steps 1-10)
1. **Data Structures**: Define TypedDict classes for structured returns
2. **Class Structure**: IssueManager class inheriting from BaseGitHubManager with additional validation
3. **Basic Issue Reading**: Get single issue and list issues with filtering
4. **Issue Creation & Lifecycle**: Create, close, reopen issues with integration test
5. **Repository Labels & Add Labels**: Get available labels and add labels to issues
6. **Remove & Set Labels**: Complete label management with enhanced integration test
7. **Add/Get Comments**: Comment creation and retrieval operations
8. **Edit/Delete Comments**: Complete comment management with final integration test
9. **Integration**: Export IssueManager class
10. **Comprehensive Testing**: Additional integration test scenarios

### Phase 2: Error Handling Refactoring (Steps 11-15)
11. **Error Handling Decorator**: Create `_handle_github_errors` decorator in BaseGitHubManager
12. **Apply to IssueManager**: Apply decorator to all 10 IssueManager methods, remove bare Exception catches
13. **Apply to PullRequestManager**: Apply decorator to all 4 methods, remove debug logging
14. **Apply to LabelsManager**: Apply decorator to all 5 methods
15. **Update Tests**: Update unit tests for new error handling behavior

## API Overview
```python
from mcp_coder.utils.github_operations import IssueManager

# Initialize (same pattern as PullRequestManager)
manager = IssueManager(project_dir=Path("."))

# Issue operations
issues = manager.get_issues(state="open", labels=["bug"])
issue = manager.get_issue(123)
new_issue = manager.create_issue("Bug report", "Description", labels=["bug"])
closed = manager.close_issue(123)

# Label management  
manager.add_labels(123, "urgent", "backend")
manager.set_labels(123, "resolved", "tested")

# Comments
comment = manager.add_comment(123, "Working on this")
manager.edit_comment(comment["id"], "Fixed the issue")
```

## Quality Assurance
- **Unit tests**: Mocked GitHub API calls for fast testing
- **Integration tests**: Real GitHub API testing with authentication
- **Error handling**: Decorator-based consistency across all managers
- **Documentation**: Complete docstrings following existing patterns
