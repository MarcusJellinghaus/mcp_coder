# Step 3: Pass `base_branch` Through `create_plan.py` Workflow

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 3.

Update create_plan.py to pass base_branch from issue data to branch creation:
1. First write/update the unit tests
2. Then modify manage_branch() and run_create_plan_workflow()
3. Run tests to verify

Follow the specifications in this step file exactly.
```

---

## Overview

Update the `create_plan.py` workflow to extract `base_branch` from issue data and pass it to the branch creation function.

---

## WHERE: File Paths

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/create_plan.py` | Modify `manage_branch()` signature, update `run_create_plan_workflow()` |
| `tests/workflows/create_plan/test_branch_management.py` | Add tests for `base_branch` parameter |

---

## WHAT: Function Signature Changes

### Current `manage_branch()` (before)

```python
def manage_branch(
    project_dir: Path, issue_number: int, issue_title: str
) -> Optional[str]:
```

### New `manage_branch()` (after)

```python
def manage_branch(
    project_dir: Path,
    issue_number: int,
    issue_title: str,
    base_branch: Optional[str] = None,
) -> Optional[str]:
```

---

## HOW: Integration Points

### Changes to `manage_branch()`

Location: Around line 85 in `create_plan.py`

```python
def manage_branch(
    project_dir: Path,
    issue_number: int,
    issue_title: str,
    base_branch: Optional[str] = None,
) -> Optional[str]:
    """Get existing linked branch or create new one.

    Args:
        project_dir: Path to the project directory containing git repository
        issue_number: GitHub issue number to link branch to
        issue_title: GitHub issue title for branch name generation
        base_branch: Optional base branch to create from (uses repo default if None)

    Returns:
        Branch name if successful, None on error
    """
```

### Changes Inside `manage_branch()`

```python
# Change this line (around line 110):
result = manager.create_remote_branch_for_issue(issue_number)

# To this:
result = manager.create_remote_branch_for_issue(
    issue_number,
    base_branch=base_branch,
)
```

### Changes to `run_create_plan_workflow()`

Location: Around line 295 in `create_plan.py`

```python
# After check_prerequisites returns issue_data, extract base_branch:
# (around line 310)

# Step 2: Manage branch
logger.info("Step 2/7: Managing branch...")
base_branch = issue_data.get("base_branch")  # NEW: Extract from issue data
if base_branch:
    logger.info(f"Using base branch from issue: {base_branch}")

branch_name = manage_branch(
    project_dir,
    issue_number,
    issue_data["title"],
    base_branch=base_branch,  # NEW: Pass base_branch
)
```

---

## ALGORITHM: Pseudocode for `manage_branch()` Changes

```python
def manage_branch(project_dir, issue_number, issue_title, base_branch=None):
    # 1. Create IssueBranchManager instance
    # 2. Check for existing linked branches
    # 3. If linked branches exist, use the first one
    # 4. Otherwise, create new branch:
    #    - Pass base_branch to create_remote_branch_for_issue()
    #    - If base_branch is invalid, create_remote_branch_for_issue()
    #      will fail with clear error (repo.get_branch() raises)
    # 5. Checkout the branch locally
    # 6. Return branch name or None on error
```

---

## DATA: Test Cases

### Test File: `tests/workflows/create_plan/test_branch_management.py`

```python
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from mcp_coder.workflows.create_plan import manage_branch


class TestManageBranchBaseBranch:
    """Tests for base_branch parameter in manage_branch()."""

    @patch("mcp_coder.workflows.create_plan.IssueBranchManager")
    @patch("mcp_coder.workflows.create_plan.checkout_branch")
    def test_manage_branch_passes_base_branch_to_create(
        self, mock_checkout, mock_manager_class
    ):
        """base_branch is passed to create_remote_branch_for_issue()."""
        mock_manager = Mock()
        mock_manager.get_linked_branches.return_value = []  # No existing branches
        mock_manager.create_remote_branch_for_issue.return_value = {
            "success": True,
            "branch_name": "123-test-issue",
            "error": None,
            "existing_branches": [],
        }
        mock_manager_class.return_value = mock_manager
        mock_checkout.return_value = True

        result = manage_branch(
            project_dir=Path("/tmp/test"),
            issue_number=123,
            issue_title="Test Issue",
            base_branch="feature/v2",
        )

        # Verify base_branch was passed
        mock_manager.create_remote_branch_for_issue.assert_called_once_with(
            123,
            base_branch="feature/v2",
        )
        assert result == "123-test-issue"

    @patch("mcp_coder.workflows.create_plan.IssueBranchManager")
    @patch("mcp_coder.workflows.create_plan.checkout_branch")
    def test_manage_branch_without_base_branch_uses_default(
        self, mock_checkout, mock_manager_class
    ):
        """Without base_branch, None is passed (uses repo default)."""
        mock_manager = Mock()
        mock_manager.get_linked_branches.return_value = []
        mock_manager.create_remote_branch_for_issue.return_value = {
            "success": True,
            "branch_name": "123-test-issue",
            "error": None,
            "existing_branches": [],
        }
        mock_manager_class.return_value = mock_manager
        mock_checkout.return_value = True

        result = manage_branch(
            project_dir=Path("/tmp/test"),
            issue_number=123,
            issue_title="Test Issue",
            # No base_branch provided
        )

        # Verify base_branch=None was passed
        mock_manager.create_remote_branch_for_issue.assert_called_once_with(
            123,
            base_branch=None,
        )
        assert result == "123-test-issue"

    @patch("mcp_coder.workflows.create_plan.IssueBranchManager")
    @patch("mcp_coder.workflows.create_plan.checkout_branch")
    def test_manage_branch_existing_branch_ignores_base_branch(
        self, mock_checkout, mock_manager_class
    ):
        """If branch already exists, base_branch is ignored."""
        mock_manager = Mock()
        mock_manager.get_linked_branches.return_value = ["123-existing-branch"]
        mock_manager_class.return_value = mock_manager
        mock_checkout.return_value = True

        result = manage_branch(
            project_dir=Path("/tmp/test"),
            issue_number=123,
            issue_title="Test Issue",
            base_branch="feature/v2",  # Should be ignored
        )

        # Verify create was NOT called (existing branch used)
        mock_manager.create_remote_branch_for_issue.assert_not_called()
        assert result == "123-existing-branch"


class TestRunCreatePlanWorkflowBaseBranch:
    """Tests for base_branch extraction in run_create_plan_workflow()."""

    @patch("mcp_coder.workflows.create_plan.check_prerequisites")
    @patch("mcp_coder.workflows.create_plan.manage_branch")
    @patch("mcp_coder.workflows.create_plan.verify_steps_directory")
    @patch("mcp_coder.workflows.create_plan.run_planning_prompts")
    @patch("mcp_coder.workflows.create_plan.validate_output_files")
    @patch("mcp_coder.workflows.create_plan.commit_all_changes")
    @patch("mcp_coder.workflows.create_plan.git_push")
    def test_workflow_extracts_and_passes_base_branch(
        self,
        mock_push,
        mock_commit,
        mock_validate,
        mock_prompts,
        mock_verify,
        mock_manage,
        mock_prereq,
    ):
        """Workflow extracts base_branch from issue_data and passes to manage_branch."""
        from mcp_coder.workflows.create_plan import run_create_plan_workflow

        # Setup mocks
        mock_prereq.return_value = (
            True,
            {
                "number": 123,
                "title": "Test Issue",
                "body": "### Base Branch\n\nfeature/v2\n\n### Desc",
                "base_branch": "feature/v2",  # Parsed by issue_manager
                # ... other fields
            },
        )
        mock_manage.return_value = "123-test-issue"
        mock_verify.return_value = True
        mock_prompts.return_value = True
        mock_validate.return_value = True
        mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
        mock_push.return_value = {"success": True}

        result = run_create_plan_workflow(
            issue_number=123,
            project_dir=Path("/tmp/test"),
            provider="claude",
            method="cli",
        )

        # Verify manage_branch was called with base_branch
        mock_manage.assert_called_once()
        call_kwargs = mock_manage.call_args[1] if mock_manage.call_args[1] else {}
        call_args = mock_manage.call_args[0] if mock_manage.call_args[0] else ()

        # Check base_branch was passed (either as kwarg or positional)
        assert "feature/v2" in str(mock_manage.call_args)
```

---

## Verification

After implementation, run:

```bash
pytest tests/workflows/create_plan/test_branch_management.py -v -k "base_branch"
```

Expected: All tests pass.

Also run full workflow tests:

```bash
pytest tests/workflows/create_plan/ -v
```
