# Step 2: CI Status Retrieval Implementation

## LLM Prompt
```
I'm implementing issue #213 - CI Pipeline Result Analysis Tool. Please refer to pr_info/steps/summary.md for the full architectural overview.

In this step, implement the get_latest_ci_status method:
1. Write tests for get_latest_ci_status method first (TDD approach)
2. Implement the method to fetch latest workflow run for a branch
3. Include job status information in the response
4. Handle edge cases (no runs, no jobs, API errors)

This covers requirements 1 & 2 from the issue: "Fetch latest CI run for a branch" and "Determine which jobs passed/failed".
Follow existing patterns from other GitHub operations managers.
```

## WHERE: File Locations
```
tests/utils/github_operations/test_ci_results_manager.py    # Add test cases
src/mcp_coder/utils/github_operations/ci_results_manager.py # Add implementation
```

## WHAT: Main Function

### Method Signature
```python
@log_function_call
@_handle_github_errors(default_return=CIStatusData(run={}, jobs=[]))
def get_latest_ci_status(self, branch: str) -> CIStatusData:
    """Get latest CI run status and job results for a branch.
    
    Args:
        branch: Branch name (required, e.g., 'feature/xyz', 'main')
    
    Returns:
        CIStatusData with run info and all job statuses
    
    Raises:
        GithubException: For authentication or permission errors
    """
```

## HOW: Integration Points

### PyGithub API Calls
```python
# Get workflow runs for specific branch
repo = self._get_repository()
runs = repo.get_workflow_runs(branch=branch)

# Get jobs for the latest run  
latest_run = runs[0]  # First run is the latest
jobs = latest_run.jobs()
```

### Error Handling
- Use `@_handle_github_errors` decorator
- Return empty CIStatusData on errors
- Validate branch parameter before API calls

## ALGORITHM: Core Logic

### get_latest_ci_status Implementation
```python
def get_latest_ci_status(self, branch: str) -> CIStatusData:
    # 1. Validate branch parameter
    # 2. Get repository and workflow runs for branch
    # 3. Get latest run (first in list) or return empty if none
    # 4. Get all jobs for the run
    # 5. Format and return CIStatusData structure
```

### Data Transformation
```python
# Transform run data (field names illustrative - verify against PyGithub objects)
run_data = {
    "id": run.id,
    "status": run.status,
    "conclusion": run.conclusion,
    "workflow_name": run.name,         # Workflow name (e.g., "CI")
    "event": run.event,                 # Trigger (e.g., "push", "pull_request")
    "workflow_path": run.path,          # e.g., ".github/workflows/ci.yml"
    "branch": branch,
    "commit_sha": run.head_sha,
    "created_at": run.created_at.isoformat() if run.created_at else None,
    "url": run.html_url
}

# Transform job data (field names illustrative - verify against PyGithub objects)
jobs_data = [{
    "id": job.id,
    "name": job.name,
    "status": job.status,
    "conclusion": job.conclusion,
    "started_at": job.started_at.isoformat() if job.started_at else None,
    "completed_at": job.completed_at.isoformat() if job.completed_at else None
} for job in jobs]
```

## DATA: Test Cases and Expected Returns

### Test Cases Structure
```python
class TestGetLatestCIStatus:
    def test_successful_status_retrieval(self, mock_repo, ci_manager)
    def test_no_workflow_runs_for_branch(self, mock_repo, ci_manager)  
    def test_invalid_branch_name(self, ci_manager)
    def test_run_with_multiple_jobs(self, mock_repo, ci_manager)
    def test_github_api_error_handling(self, mock_repo, ci_manager)
```

### Expected Return Structure
```python
# Successful case (field names illustrative)
{
    "run": {
        "id": 123456789,
        "status": "completed", 
        "conclusion": "failure",
        "workflow_name": "CI",
        "event": "push",
        "workflow_path": ".github/workflows/ci.yml",
        "branch": "feature/xyz",
        "commit_sha": "abc123...",
        "created_at": "2024-01-15T10:30:00Z",
        "url": "https://github.com/owner/repo/actions/runs/123456789"
    },
    "jobs": [
        {
            "id": 987654321,
            "name": "test",
            "status": "completed",
            "conclusion": "failure", 
            "started_at": "2024-01-15T10:31:00Z",
            "completed_at": "2024-01-15T10:35:00Z"
        },
        {
            "id": 987654322,
            "name": "build",
            "status": "completed",
            "conclusion": "success",
            "started_at": "2024-01-15T10:31:00Z", 
            "completed_at": "2024-01-15T10:33:00Z"
        }
    ]
}

# No runs case
{"run": {}, "jobs": []}
```

### Mock Setup for Tests
```python
# Mock workflow run with jobs
mock_run = Mock()
mock_run.id = 123456789
mock_run.status = "completed"
mock_run.conclusion = "failure"
# ... other fields

mock_job = Mock()
mock_job.id = 987654321
mock_job.name = "test"
# ... other fields

mock_run.jobs.return_value = [mock_job]
mock_repo.get_workflow_runs.return_value = [mock_run]
```

## Success Criteria
- [ ] Tests written first and define expected behavior
- [ ] Method retrieves latest workflow run for given branch 
- [ ] Method includes all job status information
- [ ] Handles edge cases (no runs, no jobs)
- [ ] Proper error handling with decorators
- [ ] Returns structured CIStatusData format
- [ ] All tests pass (use @pytest.fixture pattern)