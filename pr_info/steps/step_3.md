# Step 3: Add `_prepare_restart_branch()` Helper

## LLM Prompt

```
Implement Step 3 of Issue #422 (see pr_info/steps/summary.md for full context).

Add the `_prepare_restart_branch()` helper function to orchestrator.py with TDD approach.
This function encapsulates all git operations needed during session restart.
```

---

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/orchestrator.py` | ADD function |
| `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` | ADD tests |

---

## WHAT

### Function Signature

```python
from typing import NamedTuple

class BranchPrepResult(NamedTuple):
    """Result of branch preparation for session restart."""
    should_proceed: bool
    skip_reason: str | None = None
    branch_name: str | None = None


def _prepare_restart_branch(
    folder_path: Path,
    current_status: str,
    branch_manager: IssueBranchManager,
    issue_number: int,
) -> BranchPrepResult:
    """Prepare branch for session restart.
    
    Handles git fetch, branch verification, dirty check, and checkout.
    
    Args:
        folder_path: Path to the git repository
        current_status: Current issue status label
        branch_manager: IssueBranchManager for GitHub API calls
        issue_number: GitHub issue number
        
    Returns:
        BranchPrepResult with:
        - should_proceed: True if restart can continue
        - skip_reason: None if success, else "No branch"/"Dirty"/"Git error"/"Multi-branch"
        - branch_name: Branch name if switched, None if staying on current
    """
```

---

## HOW

### Integration Points

1. Add as private helper function in `orchestrator.py` (before `restart_closed_sessions`)
2. Import `get_folder_git_status` from `.status`
3. Import `status_requires_linked_branch` from `.issues`
4. Uses existing `get_linked_branch_for_issue` from `.issues`
5. Uses `execute_subprocess` for git commands

---

## ALGORITHM

```python
def _prepare_restart_branch(folder_path, current_status, branch_manager, issue_number):
    # 1. Always run git fetch origin (fatal if fails)
    try:
        execute_subprocess(["git", "fetch", "origin"], cwd=folder_path, check=True)
    except CalledProcessError as e:
        logger.error("git fetch failed for %s: %s", folder_path, e)
        return BranchPrepResult(False, "Git error", None)
    
    # 2. If status doesn't require branch, return success (stay on current branch)
    if not status_requires_linked_branch(current_status):
        return BranchPrepResult(True, None, None)
    
    # 3. Get linked branch from GitHub
    try:
        linked_branch = get_linked_branch_for_issue(branch_manager, issue_number)
    except ValueError:
        # Multiple branches linked to issue
        return BranchPrepResult(False, "Multi-branch", None)
    
    if not linked_branch:
        return BranchPrepResult(False, "No branch", None)
    
    # 4. Check if repo is dirty
    git_status = get_folder_git_status(folder_path)
    if git_status == "Dirty":
        return BranchPrepResult(False, "Dirty", None)
    
    # 5. Checkout and pull
    try:
        execute_subprocess(["git", "checkout", linked_branch], cwd=folder_path, check=True)
        execute_subprocess(["git", "pull"], cwd=folder_path, check=True)
    except CalledProcessError as e:
        logger.error("Git operation failed: %s", e)
        return BranchPrepResult(False, "Git error", None)
    
    return BranchPrepResult(True, None, linked_branch)
```

---

## DATA

### Input
- `folder_path: Path` - Git repository path
- `current_status: str` - Issue status label
- `branch_manager: IssueBranchManager` - GitHub API manager
- `issue_number: int` - Issue number for branch lookup

### Output
- `BranchPrepResult` (NamedTuple):
  - `should_proceed: bool` - Whether restart can continue
  - `skip_reason: str | None` - Reason if cannot proceed ("No branch", "Dirty", "Git error", "Multi-branch")
  - `branch_name: str | None` - Branch switched to, or None

### Test Scenarios

| Scenario | Status | Linked Branch | Dirty | Git Result | Expected |
|----------|--------|---------------|-------|------------|----------|
| status-01 | `status-01:created` | any | any | OK | `BranchPrepResult(True, None, None)` |
| status-04 + has branch + clean | `status-04:plan-review` | `"feat-123"` | No | OK | `BranchPrepResult(True, None, "feat-123")` |
| status-04 + no branch | `status-04:plan-review` | `None` | - | - | `BranchPrepResult(False, "No branch", None)` |
| status-07 + dirty | `status-07:code-review` | `"feat-456"` | Yes | - | `BranchPrepResult(False, "Dirty", None)` |
| status-04 + git error | `status-04:plan-review` | `"feat-789"` | No | Fail | `BranchPrepResult(False, "Git error", None)` |
| status-04 + multi-branch | `status-04:plan-review` | Multiple | - | - | `BranchPrepResult(False, "Multi-branch", None)` |
| git fetch fails | any | - | - | Fetch Fail | `BranchPrepResult(False, "Git error", None)` |

---

## TEST IMPLEMENTATION

### File: `tests/workflows/vscodeclaude/test_orchestrator_sessions.py`

Add new test class:

```python
class TestPrepareRestartBranch:
    """Tests for _prepare_restart_branch() helper."""

    def test_status_01_skips_branch_check(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """status-01 doesn't require branch - returns success immediately."""
        # Mock git fetch to succeed
        mock_execute = mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess"
        )
        mock_branch_manager = mocker.MagicMock()
        
        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-01:created",
            branch_manager=mock_branch_manager,
            issue_number=123,
        )
        
        assert result == BranchPrepResult(True, None, None)
        # Branch manager should not be called for status-01
        mock_branch_manager.get_linked_branches.assert_not_called()

    def test_status_04_no_branch_returns_skip(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """status-04 without linked branch returns No branch skip."""
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess"
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            return_value=None,
        )
        mock_branch_manager = mocker.MagicMock()
        
        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=mock_branch_manager,
            issue_number=123,
        )
        
        assert result == BranchPrepResult(False, "No branch", None)

    def test_status_07_dirty_returns_skip(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """status-07 with dirty repo returns Dirty skip."""
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess"
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            return_value="feat-branch",
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_folder_git_status",
            return_value="Dirty",
        )
        mock_branch_manager = mocker.MagicMock()
        
        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-07:code-review",
            branch_manager=mock_branch_manager,
            issue_number=456,
        )
        
        assert result == BranchPrepResult(False, "Dirty", None)

    def test_status_04_clean_switches_branch(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """status-04 with clean repo switches to linked branch."""
        mock_execute = mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess"
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            return_value="feat-123",
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_folder_git_status",
            return_value="Clean",
        )
        mock_branch_manager = mocker.MagicMock()
        
        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=mock_branch_manager,
            issue_number=123,
        )
        
        assert result == BranchPrepResult(True, None, "feat-123")
        # Verify git checkout and pull were called
        calls = mock_execute.call_args_list
        assert any("checkout" in str(c) for c in calls)
        assert any("pull" in str(c) for c in calls)

    def test_git_checkout_failure_returns_error(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """Git checkout failure returns Git error skip."""
        def execute_side_effect(cmd, options):
            if "checkout" in cmd:
                raise CalledProcessError(1, cmd, "", "error")
            return mocker.MagicMock(return_code=0)
        
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess",
            side_effect=execute_side_effect,
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_linked_branch_for_issue",
            return_value="feat-branch",
        )
        mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_folder_git_status",
            return_value="Clean",
        )
        mock_branch_manager = mocker.MagicMock()
        
        result = _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-04:plan-review",
            branch_manager=mock_branch_manager,
            issue_number=123,
        )
        
        assert result == BranchPrepResult(False, "Git error", None)

    def test_git_fetch_always_runs(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """git fetch origin runs for all statuses."""
        mock_execute = mocker.patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.execute_subprocess"
        )
        mock_branch_manager = mocker.MagicMock()
        
        _prepare_restart_branch(
            folder_path=tmp_path,
            current_status="status-01:created",
            branch_manager=mock_branch_manager,
            issue_number=123,
        )
        
        # First call should be git fetch
        first_call = mock_execute.call_args_list[0]
        assert "fetch" in str(first_call)
```

---

## VERIFICATION

After implementation, run:

```bash
pytest tests/workflows/vscodeclaude/test_orchestrator_sessions.py::TestPrepareRestartBranch -v
```

All 6 tests should pass.
