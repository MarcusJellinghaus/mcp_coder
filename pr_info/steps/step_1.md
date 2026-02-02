# Step 1: Add Git Merge-Base Detection to `base_branch.py`

## LLM Prompt
```
Implement Step 1 of Issue #388: Add git merge-base detection to detect_base_branch().

Reference: pr_info/steps/summary.md for full context.

This step adds the core merge-base algorithm as the PRIMARY detection method,
changes the return type to Optional[str], and updates existing tests.
```

## Overview

Add `_detect_from_git_merge_base()` as priority 1 in `detect_base_branch()` and change return type from `str` to `Optional[str]`.

---

## WHERE: Files to Modify

| File | Action |
|------|--------|
| `src/mcp_coder/workflow_utils/base_branch.py` | Add merge-base detection |
| `tests/workflow_utils/test_base_branch.py` | Add tests, update for `None` |

---

## WHAT: Functions and Signatures

### New Constant
```python
# src/mcp_coder/workflow_utils/base_branch.py

# Maximum commits between merge-base and candidate branch HEAD to consider
# the candidate as the parent branch. Higher values are more permissive but
# risk selecting wrong branches; lower values may miss valid parents that
# have moved forward since branching.
MERGE_BASE_DISTANCE_THRESHOLD = 20
```

### New Function
```python
def _detect_from_git_merge_base(
    project_dir: Path, 
    current_branch: str
) -> Optional[str]:
    """Detect parent branch using git merge-base.
    
    For each local and remote branch (candidate), find the merge-base with 
    current branch. The parent is the branch whose HEAD is closest to the 
    merge-base (smallest distance).
    
    Args:
        project_dir: Path to git repository
        current_branch: Current branch name
        
    Returns:
        Branch name if found within threshold, None otherwise
    """
```

### Modified Function Signature
```python
def detect_base_branch(
    project_dir: Path,
    current_branch: Optional[str] = None,
    issue_data: Optional[IssueData] = None,
) -> Optional[str]:  # Changed from str
    """Detect the base branch for the current feature branch.
    
    Detection priority:
    1. Git merge-base (PRIMARY) - Detect actual parent from git history
    2. GitHub PR base branch (if open PR exists for current branch)
    3. Linked issue's `### Base Branch` section
    4. Default branch (main/master)
    5. None if all detection fails
    
    Returns:
        Branch name string, or None if detection fails.
    """
```

---

## HOW: Integration Points

### New Import Required
```python
from git import Repo
from git.exc import GitCommandError
```

### Detection Order Change
```python
def detect_base_branch(...) -> Optional[str]:
    # Get current branch...
    
    # 1. Try git merge-base first (NEW - highest priority)
    base_branch = _detect_from_git_merge_base(project_dir, current_branch)
    if base_branch:
        return base_branch
    
    # 2. Try PR lookup (was priority 1)
    base_branch = _detect_from_pr(project_dir, current_branch)
    if base_branch:
        return base_branch
    
    # 3. Try issue base_branch (was priority 2)
    # ... existing code ...
    
    # 4. Fall back to default branch (was priority 3)
    # ... existing code ...
    
    # All detection methods failed - return None (was "unknown")
    logger.warning("Could not detect base branch from merge-base, PR, issue, or default")
    return None
```

---

## ALGORITHM: `_detect_from_git_merge_base()` Pseudocode

```python
def _detect_from_git_merge_base(project_dir, current_branch):
    repo = Repo(project_dir)
    current_commit = repo.heads[current_branch].commit
    candidates_passing = []
    
    # Check local branches
    for branch in repo.heads:
        if branch.name == current_branch:
            continue
        merge_base = repo.merge_base(current_commit, branch.commit)
        if not merge_base:
            continue
        distance = count_commits(merge_base[0], branch.commit)
        if distance <= MERGE_BASE_DISTANCE_THRESHOLD:
            candidates_passing.append((branch.name, distance))
    
    # Check remote branches (origin/*)
    if has_origin_remote(repo):
        for ref in repo.remotes.origin.refs:
            branch_name = ref.name.replace("origin/", "")
            if branch_name in [current_branch, "HEAD"]:
                continue
            if already_in_candidates(branch_name, candidates_passing):
                continue
            merge_base = repo.merge_base(current_commit, ref.commit)
            if not merge_base:
                continue
            distance = count_commits(merge_base[0], ref.commit)
            if distance <= MERGE_BASE_DISTANCE_THRESHOLD:
                candidates_passing.append((branch_name, distance))
    
    # Return smallest distance candidate
    if candidates_passing:
        candidates_passing.sort(key=lambda x: x[1])
        return candidates_passing[0][0]
    return None
```

---

## DATA: Return Values

| Function | Return Type | Success | Failure |
|----------|-------------|---------|---------|
| `_detect_from_git_merge_base()` | `Optional[str]` | Branch name | `None` |
| `detect_base_branch()` | `Optional[str]` | Branch name | `None` (was `"unknown"`) |

---

## TEST: New Test Cases

### File: `tests/workflow_utils/test_base_branch.py`

```python
class TestDetectFromGitMergeBase:
    """Tests for git merge-base detection (priority 1)."""

    def test_branch_from_feature_branch(self, mocks):
        """feature-B branched from feature-A, main is further away."""
        # Mock: feature-A distance=0, main distance=15
        # Expected: returns feature-A
        
    def test_parent_moved_forward(self, mocks):
        """Parent branch got more commits after branching."""
        # Mock: feature-A distance=5, main distance=25
        # Expected: returns feature-A (5 <= 20 threshold)
        
    def test_parent_moved_too_far(self, mocks):
        """Parent moved beyond threshold, falls through."""
        # Mock: feature-A distance=25 (> 20 threshold)
        # Expected: returns None, falls through to PR/Issue/Default
        
    def test_multiple_candidates_pick_smallest(self, mocks):
        """Multiple branches pass threshold, pick smallest distance."""
        # Mock: feature-A distance=3, develop distance=8
        # Expected: returns feature-A
        
    def test_simple_branch_from_main(self, mocks):
        """Standard case: feature branch from main."""
        # Mock: main distance=0
        # Expected: returns main
        
    def test_remote_branch_only(self, mocks):
        """Local branch deleted, only origin/feature-A exists."""
        # Mock: origin/feature-A distance=2
        # Expected: returns feature-A (without origin/ prefix)


class TestDetectBaseBranchReturnsNone:
    """Tests for None return value (was 'unknown')."""
    
    def test_returns_none_when_no_current_branch(self, mocks):
        """Detached HEAD returns None."""
        # Update existing test: assert result is None (was "unknown")
        
    def test_returns_none_when_all_detection_fails(self, mocks):
        """All methods fail returns None."""
        # Update existing test: assert result is None (was "unknown")
```

### Mocking Strategy

Mock at the GitPython level:
```python
@pytest.fixture
def mock_repo():
    """Mock GitPython Repo for merge-base tests."""
    with patch("mcp_coder.workflow_utils.base_branch.Repo") as mock:
        repo_instance = MagicMock()
        mock.return_value = repo_instance
        
        # Setup mock branches
        mock_branch_a = MagicMock()
        mock_branch_a.name = "feature-A"
        mock_branch_a.commit.hexsha = "abc123"
        
        mock_main = MagicMock()
        mock_main.name = "main"
        mock_main.commit.hexsha = "def456"
        
        repo_instance.heads = [mock_branch_a, mock_main]
        
        yield repo_instance
```

---

## ACCEPTANCE CRITERIA

- [ ] `MERGE_BASE_DISTANCE_THRESHOLD = 20` constant added with comment
- [ ] `_detect_from_git_merge_base()` implemented
- [ ] `detect_base_branch()` calls merge-base as priority 1
- [ ] `detect_base_branch()` returns `Optional[str]` (not `str`)
- [ ] Returns `None` instead of `"unknown"` on failure
- [ ] DEBUG logging for detection steps
- [ ] All new tests pass
- [ ] Existing tests updated for `None` return
