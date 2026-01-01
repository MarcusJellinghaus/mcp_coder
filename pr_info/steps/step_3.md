# Step 3: Update `coordinator.py` to Use `RepoIdentifier`

## Overview
Update all callers in `coordinator.py` to use the new `RepoIdentifier` class, remove the old `_parse_repo_identifier()` function, and simplify `_get_cache_file_path()`.

## LLM Prompt
```
Update coordinator.py to use RepoIdentifier as specified in pr_info/steps/summary.md.

Requirements:
1. Import RepoIdentifier from github_utils
2. Delete the entire _parse_repo_identifier() function
3. Simplify _get_cache_file_path() to accept RepoIdentifier and remove owner parameter
4. Update get_cached_eligible_issues() to use RepoIdentifier
5. Update execute_coordinator_run() to create RepoIdentifier from repo_url
6. Simplify exception handler to use RepoIdentifier directly
7. Run all tests to verify behavior

The goal is full adoption of RepoIdentifier throughout the module.
```

## WHERE: File Paths
- **Primary**: `src/mcp_coder/cli/commands/coordinator.py`

## WHAT: Changes

### 1. Add Import
```python
from ...utils.github_operations.github_utils import RepoIdentifier
```

### 2. Delete Function
Delete entire `_parse_repo_identifier()` function (~37 lines starting with):
```python
def _parse_repo_identifier(repo_url: str, repo_name: str) -> tuple[str, str | None]:
    """Parse repository URL to extract owner and repo name with fallback.
    ...
```

### 3. Simplify `_get_cache_file_path()`

**BEFORE:**
```python
def _get_cache_file_path(repo_full_name: str, owner: str | None = None) -> Path:
    """Get cache file path with enhanced naming for missing owner."""
    cache_dir = Path.home() / ".mcp_coder" / "coordinator_cache"

    if "/" in repo_full_name:
        safe_name = repo_full_name.replace("/", "_")
        return cache_dir / f"{safe_name}.issues.json"

    if owner:
        safe_name = f"{owner}_{repo_full_name}"
        return cache_dir / f"{safe_name}.issues.json"

    return cache_dir / f"{repo_full_name}.issues.json"
```

**AFTER:**
```python
def _get_cache_file_path(repo_identifier: RepoIdentifier) -> Path:
    """Get cache file path for repository.
    
    Args:
        repo_identifier: RepoIdentifier instance
        
    Returns:
        Path to cache file (e.g., ~/.mcp_coder/coordinator_cache/owner_repo.issues.json)
    """
    cache_dir = Path.home() / ".mcp_coder" / "coordinator_cache"
    return cache_dir / f"{repo_identifier.cache_safe_name}.issues.json"
```

### 4. Update `get_cached_eligible_issues()`

**BEFORE (signature):**
```python
def get_cached_eligible_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    ...
) -> List[IssueData]:
```

**AFTER (signature):**
```python
def get_cached_eligible_issues(
    repo_identifier: RepoIdentifier,
    issue_manager: IssueManager,
    ...
) -> List[IssueData]:
```

**Update function body:**
- Remove `_parse_repo_identifier()` call
- Use `repo_identifier` directly
- Update `_get_cache_file_path()` call to pass `repo_identifier`
- Use `repo_identifier.repo_name` for logging
- Simplify exception handler

### 5. Update `execute_coordinator_run()`

**BEFORE:**
```python
# Extract repo_full_name from repo_url
repo_url = validated_config["repo_url"]
if repo_url.startswith("https://github.com/"):
    repo_full_name = repo_url[len("https://github.com/") :]
    if repo_full_name.endswith(".git"):
        repo_full_name = repo_full_name[:-4]
else:
    repo_full_name = repo_name

try:
    eligible_issues = get_cached_eligible_issues(
        repo_full_name=repo_full_name,
        issue_manager=issue_manager,
        ...
    )
```

**AFTER:**
```python
# Parse repository URL into RepoIdentifier
repo_identifier = RepoIdentifier.from_repo_url(validated_config["repo_url"])

try:
    eligible_issues = get_cached_eligible_issues(
        repo_identifier=repo_identifier,
        issue_manager=issue_manager,
        ...
    )
```

### 6. Simplify Exception Handler

**BEFORE:**
```python
except Exception as e:
    try:
        repo_url = getattr(issue_manager, "repo_url", repo_full_name)
        if not isinstance(repo_url, str):
            repo_url = repo_full_name
        repo_name, _ = _parse_repo_identifier(repo_url, repo_full_name)
    except Exception:
        repo_name = repo_full_name

    _log_cache_metrics("miss", repo_name, reason=f"error_{type(e).__name__}")
    logger.warning(f"Cache error for {repo_name}: {e}, falling back to direct fetch")
    return get_eligible_issues(issue_manager)
```

**AFTER:**
```python
except Exception as e:
    _log_cache_metrics("miss", repo_identifier.repo_name, reason=f"error_{type(e).__name__}")
    logger.warning(f"Cache error for {repo_identifier.full_name}: {e}, falling back to direct fetch")
    return get_eligible_issues(issue_manager)
```

## HOW: Integration Points
- **Import**: Add `RepoIdentifier` to imports from `github_utils`
- **Type Hints**: Update function signatures to use `RepoIdentifier`
- **Logging**: Use `repo_identifier.repo_name` or `repo_identifier.full_name` as appropriate

## ALGORITHM: Migration Steps
```
1. Add import for RepoIdentifier
2. Delete _parse_repo_identifier() function
3. Update _get_cache_file_path() signature and body
4. Update get_cached_eligible_issues() signature and body
5. Update execute_coordinator_run() to use RepoIdentifier.from_repo_url()
6. Update exception handler
7. Search for any remaining references to old patterns
8. Run tests to verify
```

## Implementation Notes
- **Backward Compatibility**: This changes internal function signatures only; no external API changes
- **Error Handling**: `RepoIdentifier.from_repo_url()` raises `ValueError` on invalid URLs, which will bubble up appropriately
- **Logging Consistency**: Use `repo_identifier.full_name` for user-facing logs, `repo_identifier.repo_name` for metrics
