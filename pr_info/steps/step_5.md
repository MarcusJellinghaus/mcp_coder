# Step 5: Fix Exception Handling and Error Messages

## Overview
Address code review findings: fix potential NameError in exception handler, revert to broad exception handling, and make error messages consistent.

## LLM Prompt
```
Fix exception handling and error messages as specified in pr_info/steps/step_5.md.

Requirements:
1. Initialize repo_identifier to None before try block in get_cached_eligible_issues()
2. Update exception handler to check for None and use fallback
3. Revert exception handling to `except Exception` in 4 locations in coordinator.py
4. Update error messages in RepoIdentifier.from_full_name() to include invalid input
5. Run all tests to verify no regressions

These are bug fixes identified during code review.
```

## WHERE: File Paths
- **Primary**: `src/mcp_coder/cli/commands/coordinator.py`
- **Secondary**: `src/mcp_coder/utils/github_operations/github_utils.py`

## WHAT: Changes

### 1. Fix NameError in `get_cached_eligible_issues()` (coordinator.py)

**BEFORE:**
```python
def get_cached_eligible_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
) -> List[IssueData]:
    ...
    try:
        # Step 1: Create RepoIdentifier from repo_full_name
        repo_identifier = RepoIdentifier.from_full_name(repo_full_name)
        ...
    except (ValueError, KeyError, TypeError) as e:
        _log_cache_metrics(
            "miss", repo_identifier.repo_name, reason=f"error_{type(e).__name__}"
        )
        ...
```

**AFTER:**
```python
def get_cached_eligible_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
) -> List[IssueData]:
    ...
    repo_identifier: RepoIdentifier | None = None  # Initialize before try block
    try:
        # Step 1: Create RepoIdentifier from repo_full_name
        repo_identifier = RepoIdentifier.from_full_name(repo_full_name)
        ...
    except (ValueError, KeyError, TypeError) as e:
        # Use repo_identifier if available, otherwise fall back to repo_full_name
        repo_name = repo_identifier.repo_name if repo_identifier else repo_full_name
        full_name = repo_identifier.full_name if repo_identifier else repo_full_name
        _log_cache_metrics("miss", repo_name, reason=f"error_{type(e).__name__}")
        logger.warning(f"Cache error for {full_name}: {e}, falling back to direct fetch")
        return get_eligible_issues(issue_manager)
```

### 2. Revert Exception Handling (coordinator.py)

**Location 1 - Line ~1087 (execute_coordinator_test):**
```python
# BEFORE
except (ConnectionError, TimeoutError, ValueError) as e:
# AFTER
except Exception as e:
```

**Location 2 - Line ~1105 (execute_coordinator_test):**
```python
# BEFORE
except (ConnectionError, TimeoutError, RuntimeError) as e:
# AFTER
except Exception as e:
```

**Location 3 - Line ~1246 (execute_coordinator_run):**
```python
# BEFORE
except (ValueError, ConnectionError, TimeoutError, RuntimeError) as e:
# AFTER
except Exception as e:
```

**Location 4 - Line ~1269 (execute_coordinator_run):**
```python
# BEFORE
except (ConnectionError, TimeoutError, RuntimeError) as e:
# AFTER
except Exception as e:
```

### 3. Update Error Messages in `from_full_name()` (github_utils.py)

**BEFORE:**
```python
if slash_count != 1:
    raise ValueError(f"Invalid format")

if not owner:
    raise ValueError(f"Owner cannot be empty")
if not repo_name:
    raise ValueError(f"Repository name cannot be empty")
```

**AFTER:**
```python
if slash_count != 1:
    raise ValueError(
        f"Invalid repo identifier '{full_name}': expected 'owner/repo' format "
        f"(exactly one slash), got {slash_count} slashes"
    )

if not owner:
    raise ValueError(
        f"Invalid repo identifier '{full_name}': owner cannot be empty"
    )
if not repo_name:
    raise ValueError(
        f"Invalid repo identifier '{full_name}': repo_name cannot be empty"
    )
```

## HOW: Integration Points
- No new imports required
- Type hint `RepoIdentifier | None` for the initialized variable
- Existing tests should be updated to match new error message format

## ALGORITHM: Exception Handler Fix
```
1. Initialize repo_identifier = None before try block
2. In try block, assign repo_identifier from RepoIdentifier.from_full_name()
3. In except block, check if repo_identifier is None
4. If None, use repo_full_name as fallback for logging
5. If not None, use repo_identifier.repo_name and repo_identifier.full_name
```

## DATA: Test Updates Required

### Update test assertions for new error messages
The tests in `test_repo_identifier.py` check for specific error message substrings:

```python
# BEFORE
with pytest.raises(ValueError, match="Invalid format"):
with pytest.raises(ValueError, match="Owner cannot be empty"):
with pytest.raises(ValueError, match="Repository name cannot be empty"):

# AFTER (same patterns still work - they're substrings)
# No changes needed - the new messages contain these substrings
```

## Implementation Notes
- **Test Impact**: Error message tests use substring matching, so they should still pass
- **Backward Compatibility**: No API changes, only internal fixes
- **Risk**: Low - these are defensive fixes for edge cases
