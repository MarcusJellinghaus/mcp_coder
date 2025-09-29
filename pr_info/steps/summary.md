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
- **IssueManager class**: Main API class in `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Data structures**: TypedDict classes for IssueData, CommentData, LabelData
- **Integration tests**: Test suite with `github_integration` marker

### Design Principles
- **Mirror PR Manager**: Same error handling, validation, logging patterns as `pr_manager.py`
- **Structured data**: TypedDict return types for consistent API
- **Configuration reuse**: Leverage existing GitHub token configuration
- **Comprehensive validation**: Input validation with detailed error messages
- **Hybrid error handling**: Raise exceptions for auth/permission errors, return empty dict/list for other errors

## Files Created or Modified

### New Files
```
src/mcp_coder/utils/github_operations/issue_manager.py    # Core IssueManager class
tests/utils/test_issue_manager.py                         # Unit tests with mocking  
tests/utils/test_issue_manager_integration.py             # Integration tests
```

### Modified Files
```
src/mcp_coder/utils/github_operations/__init__.py        # Export IssueManager class
```

## Implementation Steps
1. **Data Structures**: Define TypedDict classes for structured returns
2. **Class Structure**: IssueManager class skeleton with validation
3. **Basic Issue Reading**: Get single issue and list issues with filtering
4. **Issue Creation & Lifecycle**: Create, close, reopen issues with integration test
5. **Repository Labels & Add Labels**: Get available labels and add labels to issues
6. **Remove & Set Labels**: Complete label management with enhanced integration test
7. **Add/Get Comments**: Comment creation and retrieval operations
8. **Edit/Delete Comments**: Complete comment management with final integration test
9. **Integration**: Export IssueManager class
10. **Comprehensive Testing**: Additional integration test scenarios

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
- **Error handling**: Comprehensive validation and graceful failure modes
- **Documentation**: Complete docstrings following existing patterns
