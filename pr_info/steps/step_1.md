# Step 1: Tests + Handler for `execute_checkout_issue_branch`

> **Context**: See `pr_info/steps/summary.md` for full overview of issue #647.

## Goal

Implement `execute_checkout_issue_branch()` in `gh_tool.py` with tests. This is the core logic — parser wiring comes in Step 2.

## WHERE

- **Modify**: `src/mcp_coder/cli/commands/gh_tool.py`
- **Modify**: `tests/cli/commands/test_gh_tool.py`

## WHAT

### New function in `gh_tool.py`:

```python
def execute_checkout_issue_branch(args: argparse.Namespace) -> int:
    """Execute checkout-issue-branch command.

    Fetches issue data, finds or creates a linked branch, and checks it out locally.

    Args:
        args: Parsed arguments with issue_number and project_dir option

    Returns:
        0: Success, branch checked out
        1: Could not find or create branch
        2: Error (not a git repo, API failure, git checkout failure)
    """
```

### Parameters expected on `args`:
- `args.issue_number: int` — positional argument
- `args.project_dir: Optional[str]` — optional `--project-dir`

## HOW

### Imports to add in `gh_tool.py`:
```python
import subprocess
from ...utils.github_operations.issues.manager import IssueManager
from ...utils.github_operations.issues.branch_manager import IssueBranchManager
```

### Integration points:
- `IssueManager(project_dir).get_issue(issue_number)` — returns `IssueData` TypedDict with `base_branch` field
- `IssueBranchManager(project_dir).get_linked_branches(issue_number)` — returns `List[str]`
- `IssueBranchManager(project_dir).create_remote_branch_for_issue(issue_number, base_branch=...)` — returns `BranchCreationResult` TypedDict with `success`, `branch_name`, `error`, `existing_branches`
- `subprocess.run(["git", "fetch"], ...)` and `subprocess.run(["git", "checkout", branch_name], ...)`

## ALGORITHM

```
1. resolve_project_dir(args.project_dir)
2. subprocess.run(["git", "fetch"], cwd=project_dir)
3. issue_data = IssueManager(project_dir).get_issue(issue_number)
4. branches = IssueBranchManager(project_dir).get_linked_branches(issue_number)
5. if branches: branch_name = branches[0]
   else: result = create_remote_branch_for_issue(issue_number, base_branch=issue_data["base_branch"])
         if not result["success"]: return 1
         branch_name = result["branch_name"]
6. subprocess.run(["git", "checkout", branch_name], cwd=project_dir, check=True)
7. print(branch_name); return 0
```

## DATA

### Input: `args.issue_number` (int)

### Output: Exit code (int) + branch name printed to stdout

### Dependencies used (existing, no changes):
- `IssueData` TypedDict — `number`, `title`, `base_branch` (from `types.py`)
- `BranchCreationResult` TypedDict — `success`, `branch_name`, `error`, `existing_branches` (from `branch_manager.py`)

## TESTS

Add to `tests/cli/commands/test_gh_tool.py`:

### Fixtures:
```python
@pytest.fixture
def mock_issue_manager():
    """Mock IssueManager for checkout-issue-branch tests."""
    with patch("mcp_coder.cli.commands.gh_tool.IssueManager") as mock:
        yield mock

@pytest.fixture
def mock_branch_manager():
    """Mock IssueBranchManager for checkout-issue-branch tests."""
    with patch("mcp_coder.cli.commands.gh_tool.IssueBranchManager") as mock:
        yield mock

@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for git commands."""
    with patch("mcp_coder.cli.commands.gh_tool.subprocess.run") as mock:
        yield mock
```

### Test class `TestCheckoutIssueBranchExitCodes`:
- `test_checkout_existing_branch_success` — linked branch exists, checkout succeeds → exit 0, branch name on stdout
- `test_checkout_creates_new_branch_success` — no linked branches, creation succeeds, checkout succeeds → exit 0
- `test_checkout_branch_creation_fails` — no linked branches, creation fails → exit 1
- `test_checkout_git_checkout_fails` — branch found but `git checkout` fails → exit 2
- `test_checkout_issue_not_found` — `get_issue` returns empty issue (number=0) → exit 1
- `test_checkout_invalid_project_dir` — `resolve_project_dir` raises `ValueError` → exit 2
- `test_checkout_unexpected_error` — unexpected exception → exit 2

### Test class `TestCheckoutIssueBranchBehavior`:
- `test_checkout_uses_first_linked_branch` — when multiple branches linked, uses first
- `test_checkout_passes_base_branch_to_create` — verifies `base_branch` from issue data is passed to `create_remote_branch_for_issue`
- `test_checkout_git_fetch_called_before_operations` — verifies `git fetch` is called

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement Step 1: Add `execute_checkout_issue_branch()` to `src/mcp_coder/cli/commands/gh_tool.py`
and its tests to `tests/cli/commands/test_gh_tool.py`.

Follow TDD: write the tests first, then implement the function.
Follow the existing pattern of `execute_get_base_branch()` in the same file.
Run pylint, pytest, and mypy after implementation.
```
