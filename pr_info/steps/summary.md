# GitHub Labels Manager Implementation - Summary

## Overview
Add a minimal labels manager to the existing GitHub operations module for basic CRUD operations on repository labels.

## Architectural Changes

### New Components
- **LabelsManager class**: Simple wrapper around PyGithub for label operations
- **LabelData TypedDict**: Structured label data representation

### Design Decisions
1. **Reuse existing patterns**: Mirror PullRequestManager structure for consistency
2. **Minimal scope**: Only essential CRUD operations (get, create, delete)
3. **Same validation**: Reuse project_dir/token validation from PullRequestManager
4. **Graceful failures**: Return empty dict/list on errors (no exceptions to caller)
5. **Permissive validation**: Label names follow GitHub's permissive rules (allow spaces, hyphens, underscores, emojis, etc.). Only check non-empty and no leading/trailing whitespace
6. **Flexible color format**: Accept hex colors with or without `#` prefix (e.g., both `"FF0000"` and `"#FF0000"`), normalize internally by stripping `#` before GitHub API calls
7. **Idempotent create**: `create_label()` succeeds if label already exists - returns existing label with debug message, no error raised

### No Changes To
- Configuration system (reuse existing `~/.mcp_coder/config.toml`)
- Repository URL parsing (reuse `github_utils.py`)
- Test infrastructure (reuse `@pytest.mark.github_integration`)
- Dependencies (PyGithub already installed)

## Files to Create or Modify

### New Files
```
src/mcp_coder/utils/github_operations/labels_manager.py
pr_info/steps/step_1.md
pr_info/steps/step_2.md
pr_info/steps/step_3.md
pr_info/steps/step_4.md
```

### Modified Files
```
src/mcp_coder/utils/github_operations/__init__.py  (add exports)
tests/utils/test_github_operations.py               (add test classes)
docs/architecture/ARCHITECTURE.md                   (update building blocks)
```

## Implementation Steps

1. **Step 1**: Create unit tests for LabelsManager validation
2. **Step 2**: Implement LabelsManager class with initialization
3. **Step 3**: Add integration tests for label operations
4. **Step 4**: Implement label CRUD methods and update exports

## API Surface

```python
class LabelsManager:
    def __init__(self, project_dir: Optional[Path] = None) -> None
    def get_labels(self) -> List[LabelData]
    def create_label(self, name: str, color: str, description: str = "") -> LabelData
    def delete_label(self, name: str) -> bool

class LabelData(TypedDict):
    name: str
    color: str       # 6-char hex (accepts input with or without '#', stored without '#')
    description: str
    url: str
```

## Testing Strategy

- **Unit tests**: Validation, error handling with mocks
- **Integration tests**: Real GitHub API with test repository
- **Test marker**: `@pytest.mark.github_integration`
- **Cleanup**: Labels deleted in test finally blocks

## Configuration Required

Existing configuration in `~/.mcp_coder/config.toml`:
```toml
[github]
token = "ghp_your_token_here"
test_repo_url = "https://github.com/user/test-repo"  # for integration tests
```
