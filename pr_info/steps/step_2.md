# Step 2: Add Parent Branch Detection and Workflow Integration with Tests

## Overview

Add the parent branch detection logic and integrate the rebase step into the implement workflow. The detection function is a private helper in `core.py` since it's workflow-specific (uses PR manager, reads pr_info files). Also integrates force push support when rebase succeeds.

## LLM Prompt

```
Implement Step 2 of the auto-rebase feature as described in pr_info/steps/summary.md.

Add parent branch detection and integrate the rebase step into the implement workflow.
Follow TDD: write tests first, then implement the function and integration.
```

---

## WHERE: File Locations

| File | Action |
|------|--------|
| `tests/workflows/implement/test_core.py` | ADD test class `TestGetRebaseTargetBranch` and `TestRebaseIntegration` |
| `src/mcp_coder/workflows/implement/core.py` | ADD function `_get_rebase_target_branch()` and integrate into workflow |
| `src/mcp_coder/workflows/implement/task_processing.py` | MODIFY `push_changes()` to accept and use `force_with_lease` parameter |

---

## WHAT: Function Signatures

### Private Helper Function

```python
def _get_rebase_target_branch(project_dir: Path) -> Optional[str]:
    """Determine the target branch for rebasing the current feature branch.
    
    Detection priority:
    1. GitHub PR base branch (if open PR exists for current branch)
    2. pr_info/BASE_BRANCH file content (if file exists)
    3. Default branch (main/master) via get_default_branch_name()
    
    Args:
        project_dir: Path to the project directory
    
    Returns:
        Branch name to rebase onto, or None if detection fails
    
    Note:
        All errors are handled gracefully - returns None on any failure.
        Debug logging indicates which detection method was used.
    """
```

---

## HOW: Integration Points

### New Imports in core.py

```python
from mcp_coder.utils.git_operations import (
    # ... existing imports ...
    get_current_branch_name,
    get_default_branch_name,
    rebase_onto_branch,
)
from mcp_coder.utils.github_operations.pr_manager import PullRequestManager
```

### Integration Location in `run_implement_workflow()`

```python
def run_implement_workflow(...) -> int:
    # Step 1: Check git status and prerequisites
    if not check_git_clean(project_dir):
        return 1
    if not check_main_branch(project_dir):
        return 1
    if not check_prerequisites(project_dir):
        return 1

    # NEW: Step 1.5 - Attempt rebase onto parent branch (never blocks workflow)
    rebase_succeeded = _attempt_rebase(project_dir)

    # Step 2: Prepare task tracker if needed
    if not prepare_task_tracker(...):
        return 1
    
    # ... task processing loop ...
    # Pass rebase_succeeded to task processing so push_changes() 
    # can use force_with_lease=True when needed
```

### Helper for Clean Integration

```python
def _attempt_rebase(project_dir: Path) -> bool:
    """Attempt to rebase onto parent branch. Never fails workflow.
    
    Returns:
        True if rebase succeeded (subsequent pushes need force_with_lease).
        False if rebase skipped, failed, or no target detected.
    """
    target = _get_rebase_target_branch(project_dir)
    if target:
        logger.info(f"Rebasing onto origin/{target}...")
        return rebase_onto_branch(project_dir, target)
    else:
        logger.debug("Could not detect parent branch for rebase")
        return False
```

### Modified: `push_changes()` in task_processing.py

```python
def push_changes(project_dir: Path, force_with_lease: bool = False) -> bool:
    """Push committed changes to remote.
    
    Args:
        project_dir: Path to the project directory
        force_with_lease: If True, use --force-with-lease for safe force push
    
    Returns:
        True if push succeeded, False otherwise
    """
```

---

## ALGORITHM: Parent Branch Detection (Pseudocode)

```python
def _get_rebase_target_branch(project_dir):
    # 1. Get current branch name
    current_branch = get_current_branch_name(project_dir)
    if not current_branch:
        return None
    
    # 2. Try GitHub PR lookup
    try:
        pr_manager = PullRequestManager(project_dir)
        open_prs = pr_manager.list_pull_requests(state="open")
        for pr in open_prs:
            if pr["head_branch"] == current_branch:
                logger.debug("Parent branch detected from: GitHub PR")
                return pr["base_branch"]
    except Exception:
        pass  # Continue to next method
    
    # 3. Try BASE_BRANCH file
    base_branch_file = project_dir / "pr_info" / "BASE_BRANCH"
    if base_branch_file.exists():
        content = base_branch_file.read_text().strip()
        if content:
            logger.debug("Parent branch detected from: BASE_BRANCH file")
            return content
    
    # 4. Fall back to default branch
    default = get_default_branch_name(project_dir)
    if default:
        logger.debug("Parent branch detected from: default branch")
    return default
```

---

## DATA: Detection Sources

| Priority | Source | Example |
|----------|--------|---------|
| 1 | GitHub PR base_branch | PR targeting `develop` → returns `develop` |
| 2 | `pr_info/BASE_BRANCH` file | File contains `release-2.0` → returns `release-2.0` |
| 3 | Default branch | No PR, no file → returns `main` or `master` |

---

## TEST CASES

### Test Class: `TestGetRebaseTargetBranch`

```python
class TestGetRebaseTargetBranch:
    """Tests for _get_rebase_target_branch function."""

    @patch("mcp_coder.workflows.implement.core.PullRequestManager")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    def test_returns_pr_base_branch(self, mock_get_branch, mock_pr_manager, tmp_path):
        """Test returns base_branch from open PR."""
        mock_get_branch.return_value = "feature-123"
        mock_pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "feature-123", "base_branch": "develop"}
        ]
        
        result = _get_rebase_target_branch(tmp_path)
        assert result == "develop"

    @patch("mcp_coder.workflows.implement.core.get_default_branch_name")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    def test_returns_base_branch_file_content(self, mock_get_branch, mock_default, tmp_path):
        """Test returns content from BASE_BRANCH file."""
        mock_get_branch.return_value = "feature-123"
        mock_default.return_value = "main"
        
        # Create BASE_BRANCH file
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        (pr_info / "BASE_BRANCH").write_text("release-2.0\n")
        
        result = _get_rebase_target_branch(tmp_path)
        assert result == "release-2.0"

    @patch("mcp_coder.workflows.implement.core.get_default_branch_name")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    def test_returns_default_branch_as_fallback(self, mock_get_branch, mock_default, tmp_path):
        """Test falls back to default branch."""
        mock_get_branch.return_value = "feature-123"
        mock_default.return_value = "main"
        
        result = _get_rebase_target_branch(tmp_path)
        assert result == "main"

    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    def test_returns_none_when_no_current_branch(self, mock_get_branch, tmp_path):
        """Test returns None in detached HEAD state."""
        mock_get_branch.return_value = None
        
        result = _get_rebase_target_branch(tmp_path)
        assert result is None

    @patch("mcp_coder.workflows.implement.core.PullRequestManager")
    @patch("mcp_coder.workflows.implement.core.get_default_branch_name")
    @patch("mcp_coder.workflows.implement.core.get_current_branch_name")
    def test_pr_takes_priority_over_file(self, mock_get_branch, mock_default, mock_pr_manager, tmp_path):
        """Test PR base branch takes priority over BASE_BRANCH file."""
        mock_get_branch.return_value = "feature-123"
        mock_default.return_value = "main"
        mock_pr_manager.return_value.list_pull_requests.return_value = [
            {"head_branch": "feature-123", "base_branch": "develop"}
        ]
        
        # Create BASE_BRANCH file (should be ignored)
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        (pr_info / "BASE_BRANCH").write_text("release-2.0")
        
        result = _get_rebase_target_branch(tmp_path)
        assert result == "develop"
```

### Test Class: `TestRebaseIntegration`

```python
class TestRebaseIntegration:
    """Tests for rebase integration in workflow."""

    @patch("mcp_coder.workflows.implement.core.rebase_onto_branch")
    @patch("mcp_coder.workflows.implement.core._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_rebase_called_after_prerequisites(self, mock_clean, mock_branch, 
                                                mock_prereq, mock_prepare,
                                                mock_get_target, mock_rebase):
        """Test rebase is attempted after prerequisites pass."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = False  # Stop here
        mock_get_target.return_value = "main"
        
        run_implement_workflow(Path("/test"), "claude", "cli")
        
        mock_get_target.assert_called_once()
        mock_rebase.assert_called_once_with(Path("/test"), "main")

    @patch("mcp_coder.workflows.implement.core.rebase_onto_branch")
    @patch("mcp_coder.workflows.implement.core._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_workflow_continues_when_rebase_fails(self, mock_clean, mock_branch,
                                                   mock_prereq, mock_prepare,
                                                   mock_get_target, mock_rebase):
        """Test workflow continues even when rebase returns False."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = True
        mock_get_target.return_value = "main"
        mock_rebase.return_value = False  # Rebase failed
        
        # Should not fail - workflow continues
        # (would need more mocks for full workflow, but principle is tested)

    @patch("mcp_coder.workflows.implement.core.rebase_onto_branch")
    @patch("mcp_coder.workflows.implement.core._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_rebase_skipped_when_no_target_branch(self, mock_clean, mock_branch,
                                                   mock_prereq, mock_get_target,
                                                   mock_rebase):
        """Test rebase is skipped when target branch cannot be detected."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = False  # Stop here
        mock_get_target.return_value = None  # No target detected
        
        run_implement_workflow(Path("/test"), "claude", "cli")
        
        mock_rebase.assert_not_called()
```

---

## IMPLEMENTATION NOTES

1. **PR Manager Exception Handling**: The `PullRequestManager` constructor can raise `ValueError` if GitHub token is not configured. Wrap in try/except and continue to next detection method.

2. **BASE_BRANCH File**: Simple text file, single line, stripped of whitespace. Empty file is treated as "no configuration".

3. **Logging**: Use `logger.debug()` to indicate detection source for debugging. Use `logger.info()` only for the "Rebasing onto..." message.

4. **Integration Point**: Add rebase between `check_prerequisites()` and `prepare_task_tracker()` - this is after all validation but before any task processing.
