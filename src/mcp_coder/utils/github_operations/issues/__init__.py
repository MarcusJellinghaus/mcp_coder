"""Issues package for GitHub issue operations.

This package provides:
- IssueManager: Main class for issue CRUD operations
- IssueBranchManager: Branch-issue linking via GraphQL
- Type definitions: IssueData, CommentData, EventData, IssueEventType
- Cache functions: get_all_cached_issues, update_issue_labels_in_cache
- Utilities: generate_branch_name_from_issue, BranchCreationResult, CacheData
"""

# Branch manager and utilities
from .branch_manager import (
    BranchCreationResult,
    IssueBranchManager,
    generate_branch_name_from_issue,
)

# Cache functions and types
from .cache import (
    CacheData,
    _get_cache_file_path,
    _load_cache_file,
    _log_stale_cache_entries,
    _save_cache_file,
    get_all_cached_issues,
    update_issue_labels_in_cache,
)

# Main managers
from .manager import IssueManager

# Types (Note: LabelData not included per Decision #7 - use labels_manager)
from .types import (
    CommentData,
    EventData,
    IssueData,
    IssueEventType,
)

__all__ = [
    # Types (LabelData excluded per Decision #7)
    "IssueEventType",
    "IssueData",
    "CommentData",
    "EventData",
    # Main manager
    "IssueManager",
    # Branch manager
    "IssueBranchManager",
    "BranchCreationResult",
    "generate_branch_name_from_issue",
    # Cache
    "CacheData",
    "get_all_cached_issues",
    "update_issue_labels_in_cache",
    # Private cache functions (exported for testing)
    "_get_cache_file_path",
    "_load_cache_file",
    "_log_stale_cache_entries",
    "_save_cache_file",
]
