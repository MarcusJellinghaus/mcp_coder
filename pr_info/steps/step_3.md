# Step 3: Failed Job Logs Retrieval Implementation

## LLM Prompt
```
I'm implementing issue #213 - CI Pipeline Result Analysis Tool. Please refer to pr_info/steps/summary.md for the full architectural overview.

In this step, implement the get_failed_job_logs method:
1. Write tests for get_failed_job_logs method first (TDD approach)
2. Implement the method to retrieve console logs for failed jobs
3. Handle multiple failed jobs in a single run
4. Handle edge cases (no failed jobs, log download errors)

This covers requirement 3 from the issue: "Retrieve console logs for failed jobs".
Follow existing patterns from other GitHub operations managers.
```

## WHERE: File Locations
```
tests/utils/github_operations/test_ci_results_manager.py    # Add test cases
src/mcp_coder/utils/github_operations/ci_results_manager.py # Add implementation
pyproject.toml                                              # Add requests dependency
```

## WHAT: Main Function

### Method Signature
```python
@log_function_call
@_handle_github_errors(default_return={})
def get_failed_job_logs(self, run_id: int) -> Dict[str, str]:
    """Get console logs for all failed jobs in a workflow run.
    
    Args:
        run_id: Workflow run ID to get failed job logs from
    
    Returns:
        Dictionary mapping job names to their log contents
        Only includes jobs with conclusion='failure' or 'error'
    
    Raises:
        GithubException: For authentication or permission errors
    """
```

## HOW: Integration Points

### Dependencies
Add to `pyproject.toml`:
```toml
dependencies = [
    # ... existing deps
    "requests>=2.28.0",
]
```

### PyGithub API Calls
```python
# Get specific workflow run
repo = self._get_repository()
workflow_run = repo.get_workflow_run(run_id)

# Get jobs and filter for failed ones
jobs = workflow_run.jobs()
failed_jobs = [job for job in jobs if job.conclusion in ['failure', 'error']]

# Get logs URL (returns ZIP file)
logs_url = workflow_run.logs_url
```

### HTTP Requests for Log Download (ZIP)
```python
import requests
import zipfile
import io

# Download logs using Bearer token authentication
headers = {
    "Authorization": f"Bearer {self.github_token}",
    "Accept": "application/vnd.github.v3+json"
}
response = requests.get(logs_url, headers=headers, allow_redirects=True)

# Response is a ZIP file - extract contents
zip_buffer = io.BytesIO(response.content)
with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
    # Extract log files from ZIP
    for file_name in zip_file.namelist():
        log_content = zip_file.read(file_name).decode('utf-8')
```

## ALGORITHM: Core Logic

### get_failed_job_logs Implementation
```python
def get_failed_job_logs(self, run_id: int) -> Dict[str, str]:
    # 1. Validate run_id parameter
    # 2. Get workflow run from GitHub API
    # 3. Get all jobs for the run
    # 4. Filter jobs where conclusion in ['failure', 'error']  
    # 5. Download logs for each failed job
    # 6. Return {job_name: log_content} dictionary
```

### Log Download Logic
```python
def _download_logs(self, logs_url: str) -> Dict[str, str]:
    # 1. Make authenticated HTTP request with Bearer token
    # 2. Handle ZIP response - extract all log files
    # 3. Return {filename: content} dictionary
    # 4. Handle HTTP/ZIP errors gracefully (return empty dict)
```

## DATA: Test Cases and Expected Returns

### Test Cases Structure
```python
class TestGetFailedJobLogs:
    def test_single_failed_job_logs(self, mock_repo, ci_manager)
    def test_multiple_failed_job_logs(self, mock_repo, ci_manager)
    def test_no_failed_jobs(self, mock_repo, ci_manager)
    def test_invalid_run_id(self, ci_manager) 
    def test_log_download_failure(self, mock_repo, ci_manager, mock_requests)
    def test_mixed_job_conclusions(self, mock_repo, ci_manager)
```

### Expected Return Examples
```python
# Single failed job
{
    "test": "==== Test Job Log ====\nStarting tests...\nTest failed: assertion error\n✗ 1 test failed"
}

# Multiple failed jobs
{
    "test": "==== Test Job Log ====\n...\nTest failed: assertion error",
    "lint": "==== Lint Job Log ====\n...\nPylint found 5 errors"  
}

# No failed jobs
{}

# Mixed conclusions (only failures included)
{
    "test": "Test log content..."
    # 'build' job with conclusion='success' not included
    # 'deploy' job with conclusion='cancelled' not included  
}
```

### Mock Setup for Tests
```python
# Mock workflow run
mock_run = Mock()
mock_run.id = 123456789

# Mock failed job
mock_failed_job = Mock()
mock_failed_job.name = "test"
mock_failed_job.conclusion = "failure"
mock_failed_job.logs_url.return_value = "https://api.github.com/repos/.../logs"

# Mock successful job (should be filtered out)
mock_success_job = Mock() 
mock_success_job.name = "build"
mock_success_job.conclusion = "success"

mock_run.jobs.return_value = [mock_failed_job, mock_success_job]
mock_repo.get_workflow_run.return_value = mock_run

# Mock HTTP response for log download
mock_response = Mock()
mock_response.text = "==== Test Job Log ====\nTest failed..."
mock_requests.get.return_value = mock_response
```

### Edge Cases to Handle
```python
# Job conclusions that indicate failure
failed_conclusions = ['failure', 'error']

# Job conclusions to ignore  
ignored_conclusions = ['success', 'cancelled', 'skipped', 'neutral']

# HTTP errors during log download
# - Return empty string for that job
# - Log the error but don't fail the entire method
# - Continue processing other jobs
```

## Success Criteria
- [ ] Tests written first and define expected behavior
- [ ] Method filters jobs by failure conclusions correctly
- [ ] Downloads logs for all failed jobs in a run
- [ ] Handles HTTP errors gracefully during log download  
- [ ] Returns proper dictionary mapping job names to log contents
- [ ] Edge cases handled (no failed jobs, invalid run ID)
- [ ] All tests pass (use @pytest.fixture pattern)