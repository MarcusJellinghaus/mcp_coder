# Step 1: Create Base Branch Detection Module

## LLM Prompt

```
Implement Step 1 of Issue #374 (see pr_info/steps/summary.md for context).

Create the shared base branch detection module with TDD approach:
1. First create the test file with all test cases
2. Then implement the function to make tests pass

Follow the specifications below exactly.
```

## Overview

Create `src/mcp_coder/workflow_utils/base_branch.py` with a single function that detects the base branch for the current feature branch.

---

## WHERE: File Paths

### New Files
- `src/mcp_coder/workflow_utils/base_branch.py` - Implementation
- `tests/workflow_utils/test_base_branch.py` - Tests

---

## WHAT: Function Signature

```python
# src/mcp_coder/workflow_utils/base_branch.py

from pathlib import Path
from typing import Optional
from mcp_coder.utils.github_operations.issue_manager import IssueData

def detect_base_branch(
    project_dir: Path,
    issue_data: Optional[IssueData] = None
) -> str:
    """Detect the base branch for the current feature branch.
    
    Detection priority:
    1. GitHub PR base branch (if open PR exists for current branch)
    2. Linked issue's `### Base Branch` section (from issue_data or fetched)
    3. Default branch (main/master)
    4. "unknown" if all detection fails
    
    Args:
        project_dir: Path to git repository
        issue_data: Optional pre-fetched issue data (avoids duplicate API calls)
    
    Returns:
        Branch name string, or "unknown" if detection fails.
    
    Note:
        Makes up to 2 GitHub API calls if issue_data not provided:
        - PR list lookup
        - Issue fetch (if no PR found and branch has issue number)
    """
```

---

## HOW: Integration Points

### Imports Required
```python
import logging
from pathlib import Path
from typing import Optional

from mcp_coder.utils.git_operations.readers import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from mcp_coder.utils.git_operations import get_default_branch_name
from mcp_coder.utils.github_operations.issue_manager import IssueData, IssueManager
from mcp_coder.utils.github_operations.pr_manager import PullRequestManager

logger = logging.getLogger(__name__)
```

---

## ALGORITHM: Core Logic (Pseudocode)

```
function detect_base_branch(project_dir, issue_data):
    current_branch = get_current_branch_name(project_dir)
    if not current_branch: return "unknown"
    
    # 1. Try PR lookup
    try: find open PR with head_branch == current_branch, return base_branch
    except: pass
    
    # 2. Try issue base_branch
    if issue_data and issue_data.base_branch: return it
    if not issue_data:
        issue_number = extract from branch
        if issue_number: fetch issue, return base_branch if present
    
    # 3. Fall back to default branch
    return get_default_branch_name(project_dir) or "unknown"
```

---

## DATA: Return Values

| Scenario | Return Value |
|----------|--------------|
| Open PR exists | PR's `base_branch` (e.g., "main", "develop") |
| Issue has base branch | Issue's parsed `base_branch` field |
| Default branch found | Default branch name (e.g., "main", "master") |
| All detection fails | `"unknown"` |

---

## TEST CASES

### Test File: `tests/workflow_utils/test_base_branch.py`

```python
"""Tests for base branch detection functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


def test_detect_base_branch_from_pr() -> None:
    """Test detection from open PR."""
    # Mock: current branch has open PR with base_branch="develop"
    # Expected: returns "develop"


def test_detect_base_branch_from_issue_data() -> None:
    """Test detection from pre-fetched issue data."""
    # Mock: no PR, issue_data has base_branch="feature/v2"
    # Expected: returns "feature/v2"


def test_detect_base_branch_fetches_issue() -> None:
    """Test fetching issue when issue_data not provided."""
    # Mock: no PR, branch "123-feature", issue #123 has base_branch="main"
    # Expected: returns "main"


def test_detect_base_branch_default_fallback() -> None:
    """Test fallback to default branch."""
    # Mock: no PR, no issue base_branch, default branch is "main"
    # Expected: returns "main"


def test_detect_base_branch_unknown_fallback() -> None:
    """Test unknown fallback when all detection fails."""
    # Mock: no current branch
    # Expected: returns "unknown"


def test_detect_base_branch_pr_api_error() -> None:
    """Test graceful handling of PR API errors."""
    # Mock: PR lookup raises exception
    # Expected: continues to next detection method


def test_detect_base_branch_issue_api_error() -> None:
    """Test graceful handling of issue API errors."""
    # Mock: Issue lookup raises exception
    # Expected: falls back to default branch


def test_detect_base_branch_no_issue_number_in_branch() -> None:
    """Test branch without issue number skips issue lookup."""
    # Mock: branch "feature/no-issue", no PR
    # Expected: skips issue lookup, returns default branch
```

---

## IMPLEMENTATION CHECKLIST

- [ ] Create test file with all test cases (tests first)
- [ ] Create `base_branch.py` with imports and function stub
- [ ] Implement PR detection logic
- [ ] Implement issue-based detection logic  
- [ ] Implement default branch fallback
- [ ] Ensure all exceptions are caught and logged
- [ ] Run tests to verify all pass
- [ ] Run mypy type checking
