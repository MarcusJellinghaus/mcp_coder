# Step 0: Foundational Enhancements

## Overview

This step adds foundational components needed for the CI check feature:
1. Enhance `CIResultsManager.get_latest_ci_status()` to include step-level information for each job
2. Add `get_latest_commit_sha()` helper function for debug logging (Decision 19)

## LLM Prompt for This Step

```
Implement Step 0 from pr_info/steps/step_0.md.

Reference the summary at pr_info/steps/summary.md for context.

This step adds foundational components:
1. Enhance CIResultsManager to include step-level data for each job
2. Add get_latest_commit_sha() helper function

Follow TDD: write tests first, then implement.
```

---

## Part 1: Write Tests First

### WHERE
`tests/utils/github_operations/test_ci_results_manager_status.py` (append to existing tests)

### WHAT
Add tests for step-level data in job info:

```python
class TestGetLatestCIStatusSteps:
    """Tests for step-level data in get_latest_ci_status."""

    def test_jobs_include_steps_data(self):
        """Job info should include steps array with number, name, conclusion."""
        # Setup mock with job steps
        # Verify steps data is included in response

    def test_steps_contain_required_fields(self):
        """Each step should have number, name, and conclusion fields."""
        # Verify step structure

    def test_empty_steps_when_job_has_no_steps(self):
        """Jobs with no steps should have empty steps array."""
        # Handle edge case
```

### HOW
Append to existing test file, using existing mock patterns.

---

## Part 2: Add TypedDicts for Step and Job Data (Decision 15)

### WHERE
`src/mcp_coder/utils/github_operations/ci_results_manager.py`

### WHAT
Add explicit TypedDicts for full type safety:

```python
class StepData(TypedDict):
    """TypedDict for workflow job step data."""

    number: int
    name: str
    conclusion: Optional[str]  # "success", "failure", "skipped", None


class JobData(TypedDict):
    """TypedDict for workflow job data."""

    id: int
    name: str
    status: str
    conclusion: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    steps: List[StepData]


class CIStatusData(TypedDict):
    """TypedDict for CI status data structure."""

    run: Dict[str, Any]
    jobs: List[JobData]
```

Add `Optional` to imports if not already present.

---

## Part 3: Update get_latest_ci_status Implementation

### WHERE
`src/mcp_coder/utils/github_operations/ci_results_manager.py`

### WHAT
Modify the job data transformation to include steps:

```python
# In get_latest_ci_status(), update job_data dict:
job_data = {
    "id": job.id,
    "name": job.name,
    "status": job.status,
    "conclusion": job.conclusion,
    "started_at": job.started_at.isoformat() if job.started_at else None,
    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    "steps": [
        {
            "number": step.number,
            "name": step.name,
            "conclusion": step.conclusion,
        }
        for step in job.steps
    ],
}
```

### ALGORITHM
```
1. In the jobs loop, after creating job_data dict
2. Access job.steps (PyGithub provides this)
3. Transform each step to dict with number, name, conclusion
4. Add steps list to job_data
```

### DATA

**Step structure:**
```python
{
    "number": int,      # Step number (1, 2, 3, ...)
    "name": str,        # Step name ("Set up job", "Run tests", etc.)
    "conclusion": str,  # "success", "failure", "skipped", None
}
```

---

---

## Part 4: Add get_latest_commit_sha Helper (Decision 19)

### WHERE
`src/mcp_coder/utils/git_operations/commits.py`

### WHAT
Add helper function to get the current HEAD commit SHA:

```python
def get_latest_commit_sha(project_dir: Path) -> Optional[str]:
    """Get the SHA of the current HEAD commit.
    
    Args:
        project_dir: Path to the git repository
    
    Returns:
        The full SHA of HEAD, or None if not in a git repository
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
```

### HOW
Add after existing functions in commits.py. Uses subprocess to run `git rev-parse HEAD`.

---

## Part 5: Write Tests for get_latest_commit_sha

### WHERE
`tests/utils/git_operations/test_commits.py`

### WHAT
Add tests for the new helper function:

```python
class TestGetLatestCommitSha:
    """Tests for get_latest_commit_sha function."""

    def test_returns_sha_in_git_repo(self, temp_git_repo):
        """Should return SHA string in a valid git repo."""
        sha = get_latest_commit_sha(temp_git_repo)
        
        assert sha is not None
        assert len(sha) == 40  # Full SHA length
        assert all(c in '0123456789abcdef' for c in sha)

    def test_returns_none_outside_git_repo(self, tmp_path):
        """Should return None when not in a git repository."""
        sha = get_latest_commit_sha(tmp_path)
        
        assert sha is None
```

---

## Verification

1. Run CIResultsManager tests: `pytest tests/utils/github_operations/test_ci_results_manager_status.py -v`
2. Run commits tests: `pytest tests/utils/git_operations/test_commits.py -v`
3. All tests should pass
4. Verify step data is correctly extracted from GitHub API
