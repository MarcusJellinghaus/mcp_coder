# GitHub API Caching Implementation - Summary

## Overview
Add GitHub API caching to the coordinator to reduce unnecessary API calls when running frequently (e.g., every minute monitoring loops). This prevents duplicate issue dispatches and reduces GitHub API rate limit consumption.

## Problem Statement
- Coordinator fetches ALL open issues on every run via `IssueManager.list_issues()`
- No incremental fetching or caching mechanism
- Risk of duplicate issue dispatches before GitHub label updates propagate
- Unnecessary API calls when nothing has changed

## Solution Architecture

### Design Principles (KISS)
- **Single cache function** handles all caching logic
- **No API pollution** - minimal changes to existing interfaces
- **Pure optimization layer** - cache failures never affect correctness
- **Backwards compatible** - existing behavior preserved on any cache error

### Key Components

#### 1. Cache Storage
- **Location**: `~/.mcp_coder/coordinator_cache/{repo_name}.issues.json`
- **Format**: Simple JSON with `last_checked` timestamp and issue objects
- **Fields per issue**: `number`, `state`, `labels`, `updated_at` (minimal set)

#### 2. Incremental Fetching
- **GitHub API**: Use `since` parameter with `state="all"` to detect changes
- **Strategy**: Fetch issues modified since last check, merge with cache
- **Fallback**: Full refresh when cache age > `cache_refresh_minutes` (default 24h)

#### 3. Duplicate Protection  
- **Rule**: Skip repository if last checked < 1 minute ago
- **Behavior**: Log INFO message, continue to next repo (exit code 0)
- **Scope**: Per-repository protection

#### 4. Configuration
- **Setting**: `[coordinator] cache_refresh_minutes = 1440` (24 hours default)
- **CLI**: `--force-refresh` flag bypasses all cache logic

### Architectural Changes

#### New Components
- **Cache function**: `get_cached_eligible_issues()` in `coordinator.py`
- **Helper function**: `list_issues_since()` method in `IssueManager`
- **Cache directory**: Auto-created `~/.mcp_coder/coordinator_cache/`

#### Modified Components
- **coordinator.py**: Replace direct `get_eligible_issues()` call with cached version
- **issue_manager.py**: Add incremental fetch method (minimal addition)
- **Config system**: Read `cache_refresh_minutes` setting

#### Integration Points
- **CLI argument**: `--force-refresh` flag in coordinator subcommand
- **Error handling**: All cache errors fall back to existing behavior
- **Logging**: Minimal logging (DEBUG/INFO/WARNING levels only)

## Files Created/Modified

### New Files
- `tests/utils/test_coordinator_cache.py` - Cache function unit tests

### Modified Files  
- `src/mcp_coder/cli/commands/coordinator.py` - Add cache function and integration
- `src/mcp_coder/utils/github_operations/issue_manager.py` - Add `list_issues_since()` method
- `tests/cli/commands/test_coordinator.py` - Add cache integration tests

## Benefits
- **Reduced API calls**: Only fetch changed issues after initial run
- **Duplicate protection**: Prevent workflows from running too frequently  
- **Rate limit friendly**: Minimize GitHub API consumption
- **Zero risk**: Cache failures never break existing workflows
- **Simple maintenance**: Single cache function contains all complexity

## Implementation Approach
1. **Test-driven development** - Write tests first for each component
2. **Incremental integration** - Add cache as opt-in layer initially
3. **Graceful degradation** - Any error reverts to current behavior
4. **Minimal surface area** - Keep changes localized and focused