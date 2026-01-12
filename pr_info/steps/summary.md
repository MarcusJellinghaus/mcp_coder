# Issue #276: Remove Direct GitPython Import from github_operations.base_manager

## Summary

This refactoring removes the direct `git` package (GitPython) import from `base_manager.py` in the `github_operations` module. All git operations will go through the `git_operations` abstraction layer, enforcing the Git Library Isolation architectural contract.

## Architectural / Design Changes

### Before
```
github_operations.base_manager
    ├── imports git (GitPython) directly
    ├── uses git.Repo() for repository validation
    ├── uses git.InvalidGitRepositoryError for exception handling
    └── stores self._repo attribute (git.Repo instance)
```

### After
```
github_operations.base_manager
    ├── imports git_operations (abstraction layer)
    ├── uses git_operations.is_git_repository() for validation
    ├── uses git_operations.get_github_repository_url() for remote URL
    └── stateless design (no self._repo attribute)
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Stateless refactoring | Remove `self._repo` entirely; use function calls instead |
| No new git_operations functions | Required functions already exist |
| Namespace import style | `from mcp_coder.utils import git_operations` for clarity |
| Preserve error messages | Maintain API compatibility |

## Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `src/mcp_coder/utils/github_operations/base_manager.py` | Modify | Remove git import, use git_operations |
| `tests/utils/github_operations/test_base_manager.py` | Modify | Update mocks to target git_operations |
| `.importlinter` | Modify | Remove the exception rule for base_manager |

## Files NOT Modified

- `src/mcp_coder/utils/git_operations/*.py` - No changes needed; functions already exist

## Existing Functions Used (No Changes Required)

From `git_operations.repository`:
```python
def is_git_repository(project_dir: Path) -> bool
```

From `git_operations.remotes`:
```python
def get_github_repository_url(project_dir: Path) -> Optional[str]
```

## Implementation Steps

1. **Step 1**: Update `base_manager.py` - Remove git import, use git_operations abstraction
2. **Step 2**: Update tests - Change mocks from git.Repo to git_operations functions
3. **Step 3**: Update `.importlinter` - Remove the exception rule and verify

## Acceptance Criteria

- [ ] `base_manager.py` no longer imports from `git` package
- [ ] All existing tests pass
- [ ] `lint-imports` passes without the exception rule
- [ ] Same error messages preserved for API compatibility
