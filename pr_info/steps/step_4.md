# Step 4: Fix Hardcoded "main" in `pr_manager.py`

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 4.

Fix the hardcoded "main" default in pr_manager.py's create_pull_request():
1. First write/update the unit tests
2. Then modify the function to use get_default_branch_name()
3. Run tests to verify

Follow the specifications in this step file exactly.
```

---

## Overview

Fix the `create_pull_request()` method to dynamically resolve the default branch instead of hardcoding `"main"`.

---

## WHERE: File Paths

| File | Action |
|------|--------|
| `src/mcp_coder/utils/github_operations/pr_manager.py` | Modify `create_pull_request()` default parameter |
| `tests/utils/github_operations/test_pr_manager.py` | Add tests for dynamic default branch resolution |

---

## WHAT: Function Signature Change

### Current (before)

```python
def create_pull_request(
    self, title: str, head_branch: str, base_branch: str = "main", body: str = ""
) -> PullRequestData:
```

### New (after)

```python
def create_pull_request(
    self,
    title: str,
    head_branch: str,
    base_branch: Optional[str] = None,
    body: str = "",
) -> PullRequestData:
```

---

## HOW: Integration Points

### Import Changes

The file already imports `get_default_branch_name` at line 19:

```python
from mcp_coder.utils.git_operations import (
    get_default_branch_name,
    get_github_repository_url,
)
```

No new imports needed.

### Method Body Changes

Location: Around line 115 in `pr_manager.py`, inside `create_pull_request()`

```python
def create_pull_request(
    self,
    title: str,
    head_branch: str,
    base_branch: Optional[str] = None,
    body: str = "",
) -> PullRequestData:
    """Create a new pull request.

    Args:
        title: Title of the pull request (must be non-empty)
        head_branch: Source branch for the pull request
        base_branch: Target branch for the pull request (default: repository default branch)
        body: Description/body of the pull request (optional)
    ...
    """
    # Resolve base_branch if not provided
    if base_branch is None:
        assert self.project_dir is not None, "project_dir required for default branch"
        resolved_base = get_default_branch_name(self.project_dir)
        if resolved_base is None:
            logger.error("Could not determine default branch for repository")
            return cast(PullRequestData, {})
        base_branch = resolved_base
        logger.debug(f"Using repository default branch: {base_branch}")

    # ... rest of existing validation and logic ...
```

---

## ALGORITHM: Pseudocode

```python
def create_pull_request(self, title, head_branch, base_branch=None, body=""):
    # 1. If base_branch is None:
    #    a. Call get_default_branch_name(self.project_dir)
    #    b. If returns None, log error and return empty dict
    #    c. Otherwise, use returned value as base_branch
    # 2. Continue with existing validation (title, branch names)
    # 3. Create PR via GitHub API
    # 4. Return PullRequestData
```

---

## DATA: Test Cases

### Test File: `tests/utils/github_operations/test_pr_manager.py`

Add new test class or tests to existing file:

```python
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from mcp_coder.utils.github_operations.pr_manager import PullRequestManager


class TestCreatePullRequestDefaultBranch:
    """Tests for dynamic default branch resolution in create_pull_request()."""

    @pytest.fixture
    def mock_pr_manager(self, tmp_path):
        """Create PullRequestManager with mocked dependencies."""
        with patch(
            "mcp_coder.utils.github_operations.pr_manager.get_github_repository_url"
        ) as mock_url:
            with patch(
                "mcp_coder.utils.github_operations.base_manager.Github"
            ) as mock_github:
                with patch(
                    "mcp_coder.utils.github_operations.base_manager.get_github_token"
                ) as mock_token:
                    mock_url.return_value = "https://github.com/test/repo.git"
                    mock_token.return_value = "fake-token"

                    # Create a mock repo
                    mock_repo = Mock()
                    mock_github.return_value.get_repo.return_value = mock_repo

                    # Create git directory for validation
                    (tmp_path / ".git").mkdir()

                    manager = PullRequestManager(project_dir=tmp_path)
                    manager._mock_repo = mock_repo
                    yield manager

    @patch("mcp_coder.utils.github_operations.pr_manager.get_default_branch_name")
    def test_create_pr_resolves_default_branch_when_none(
        self, mock_get_default, mock_pr_manager
    ):
        """When base_branch=None, resolves via get_default_branch_name()."""
        mock_get_default.return_value = "main"

        # Setup mock PR creation
        mock_pr = Mock()
        mock_pr.number = 1
        mock_pr.title = "Test PR"
        mock_pr.body = "Body"
        mock_pr.state = "open"
        mock_pr.head.ref = "feature-branch"
        mock_pr.base.ref = "main"
        mock_pr.html_url = "https://github.com/test/repo/pull/1"
        mock_pr.created_at = None
        mock_pr.updated_at = None
        mock_pr.user = None
        mock_pr.mergeable = True
        mock_pr.merged = False
        mock_pr.draft = False

        mock_pr_manager._mock_repo.create_pull.return_value = mock_pr

        result = mock_pr_manager.create_pull_request(
            title="Test PR",
            head_branch="feature-branch",
            base_branch=None,  # Should resolve to "main"
            body="Body",
        )

        # Verify get_default_branch_name was called
        mock_get_default.assert_called_once()

        # Verify PR was created with resolved branch
        mock_pr_manager._mock_repo.create_pull.assert_called_once()
        call_kwargs = mock_pr_manager._mock_repo.create_pull.call_args[1]
        assert call_kwargs["base"] == "main"

    @patch("mcp_coder.utils.github_operations.pr_manager.get_default_branch_name")
    def test_create_pr_uses_explicit_base_branch(
        self, mock_get_default, mock_pr_manager
    ):
        """When base_branch is provided, uses it directly."""
        # Setup mock PR
        mock_pr = Mock()
        mock_pr.number = 1
        mock_pr.title = "Test PR"
        mock_pr.body = "Body"
        mock_pr.state = "open"
        mock_pr.head.ref = "feature-branch"
        mock_pr.base.ref = "develop"
        mock_pr.html_url = "https://github.com/test/repo/pull/1"
        mock_pr.created_at = None
        mock_pr.updated_at = None
        mock_pr.user = None
        mock_pr.mergeable = True
        mock_pr.merged = False
        mock_pr.draft = False

        mock_pr_manager._mock_repo.create_pull.return_value = mock_pr

        result = mock_pr_manager.create_pull_request(
            title="Test PR",
            head_branch="feature-branch",
            base_branch="develop",  # Explicit branch
            body="Body",
        )

        # Verify get_default_branch_name was NOT called
        mock_get_default.assert_not_called()

        # Verify PR was created with explicit branch
        call_kwargs = mock_pr_manager._mock_repo.create_pull.call_args[1]
        assert call_kwargs["base"] == "develop"

    @patch("mcp_coder.utils.github_operations.pr_manager.get_default_branch_name")
    def test_create_pr_returns_empty_when_default_branch_unknown(
        self, mock_get_default, mock_pr_manager
    ):
        """When default branch cannot be determined, returns empty dict."""
        mock_get_default.return_value = None  # Cannot determine

        result = mock_pr_manager.create_pull_request(
            title="Test PR",
            head_branch="feature-branch",
            base_branch=None,
            body="Body",
        )

        # Should return empty dict
        assert result == {} or result.get("number") is None

        # PR creation should not be attempted
        mock_pr_manager._mock_repo.create_pull.assert_not_called()
```

---

## Verification

After implementation, run:

```bash
pytest tests/utils/github_operations/test_pr_manager.py -v -k "default_branch"
```

Expected: All tests pass.

Also run full PR manager tests:

```bash
pytest tests/utils/github_operations/test_pr_manager.py -v
```
