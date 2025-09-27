# GitHub Pull Request Operations - Implementation Summary (Updated)

## Overview
Add GitHub pull request functionality to MCP Coder using object-oriented **PullRequestManager** class approach. This provides better API design, resource management, and extensibility while following TDD and KISS principles.

## Architectural Changes

### New Module
- **Package structure**: `src/mcp_coder/utils/github_operations/`
  - `__init__.py` - Exports PullRequestManager class and factory function
  - `pr_manager.py` - Core PullRequestManager implementation
- **Object-oriented API**: Single manager instance per repository
- **Enhanced functionality**: Merge capabilities, properties, and better state management

### Configuration Integration
- **Reuses existing pattern**: `get_config_value()` from `user_config.py`
- **Two new config keys**:
  - `github.token` - Personal Access Token with repo scope
  - `github.test_repo_url` - Test repository URL

### Testing Strategy
- **New test marker**: `github_integration` for conditional execution
- **Graceful skipping**: Tests skip when GitHub credentials unavailable
- **Manager-based testing**: Integration tests using PullRequestManager instances

## Files Created/Modified

### New Files
- `src/mcp_coder/utils/github_operations/__init__.py` - PullRequestManager exports
- `src/mcp_coder/utils/github_operations/pr_manager.py` - Core implementation
- `tests/utils/test_github_operations.py` - Integration tests

### Modified Files
- `pyproject.toml` - Add github_integration marker (PyGithub already present)
- `src/mcp_coder/utils/__init__.py` - Export PullRequestManager and factory function

## Design Principles Applied

### KISS (Keep It Simple, Stupid)
- Single class with clear responsibilities
- Simple method signatures with sensible defaults
- Consistent return types (always dict for operations)
- Minimal error handling with graceful degradation

### Test-Driven Development
- Tests written before implementation
- Manager-based testing approach drives API design
- Each step includes failing test → minimal implementation → refactor

### Object-Oriented Benefits
- No repeated repo_url parameters
- Single GitHub client instance (better performance)
- Better resource management and state consistency
- Extensible design for future GitHub features

## API Design

```python
class PullRequestManager:
    def __init__(self, repo_url: str, token: Optional[str] = None):
        """Initialize manager for specific repository."""
    
    def create_pull_request(self, title: str, body: str, head: str, base: str = "main") -> Dict[str, Any]:
        """Returns: {'number': int, 'url': str, 'title': str}"""

    def get_pull_request(self, pr_number: int) -> Dict[str, Any]:
        """Returns: {'number': int, 'title': str, 'state': str, 'url': str, 'body': str, 'head': str, 'base': str}"""

    def list_pull_requests(self, state: str = "open") -> List[Dict[str, Any]]:
        """Returns: [{'number': int, 'title': str, 'state': str, 'url': str, 'head': str, 'base': str}]"""

    def close_pull_request(self, pr_number: int) -> Dict[str, Any]:
        """Returns: {'number': int, 'state': str}"""

    def merge_pull_request(self, pr_number: int, merge_method: str = "merge") -> Dict[str, Any]:
        """Returns: {'merged': bool, 'sha': str, 'message': str}"""
    
    @property
    def repository_name(self) -> str:
        """Get repository full name (owner/repo)."""
    
    @property
    def default_branch(self) -> str:
        """Get repository default branch name."""

def create_pr_manager(repo_url: str, token: Optional[str] = None) -> PullRequestManager:
    """Factory function to create PullRequestManager instance."""
```

## Usage Examples

```python
# Basic usage
from mcp_coder.utils.github_operations import PullRequestManager

manager = PullRequestManager("https://github.com/user/repo")
pr = manager.create_pull_request("Fix bug", "Description", "feature-branch")
details = manager.get_pull_request(pr['number'])
manager.close_pull_request(pr['number'])

# Using factory function
from mcp_coder.utils.github_operations import create_pr_manager

manager = create_pr_manager("https://github.com/user/repo")
prs = manager.list_pull_requests(state="all")
```

## Configuration Example

```toml
[github]
token = "ghp_your_personal_access_token"
test_repo_url = "https://github.com/username/test-repo"  # Repository for integration tests
```

## Implementation Benefits

### Performance Benefits
- **Single GitHub client**: Reused across multiple operations
- **Repository caching**: No repeated repo object creation
- **Connection pooling**: Better resource utilization

### API Benefits
- **Cleaner interface**: No repeated repo_url parameters
- **Better discoverability**: All PR operations in one place
- **Consistent error handling**: Centralized approach
- **Extensible design**: Easy to add new features

### Testing Benefits
- **Simpler mocking**: Mock single manager instance
- **Better state management**: Repository context maintained
- **Cleaner test setup**: Single initialization per test class

### Maintenance Benefits
- **Centralized logic**: All PR operations in one class
- **Future-proof**: Easy to extend with new GitHub features
- **Better separation of concerns**: Clear boundaries and responsibilities

## Implementation Steps

1. **Step 1**: Add github_integration test marker to pyproject.toml
2. **Step 2**: Create PullRequestManager class structure with empty implementations
3. **Step 3**: Write failing integration tests using manager instances
4. **Step 4**: Implement PyGithub functionality to make tests pass
5. **Step 5**: Add enhanced features and validation (merge, properties)
6. **Step 6**: Update utils module exports for easy imports

This approach provides a more robust, maintainable, and user-friendly API compared to standalone functions while maintaining the same TDD methodology and simplicity principles.
