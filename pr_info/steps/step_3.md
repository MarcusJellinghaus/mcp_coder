# Step 3: Run Logs Retrieval Implementation

## LLM Prompt
```
I'm implementing issue #213 - CI Pipeline Result Analysis Tool. Please refer to pr_info/steps/summary.md for the full architectural overview.

In this step, implement the get_run_logs method:
1. Write tests for get_run_logs method first (TDD approach)
2. Implement shared helper _download_and_extract_zip() for ZIP download/extraction
3. Implement the method to retrieve all console logs from a run
4. Include job status info so consumer knows which jobs failed
5. Handle edge cases (no logs, download errors)

This covers requirement 3 from the issue: "Retrieve console logs for failed jobs".
Note: Returns ALL logs with job status info - consumer filters if needed (Decision 15).
Follow existing patterns from other GitHub operations managers.
```

## WHERE: File Locations
```
tests/utils/github_operations/test_ci_results_manager.py    # Add test cases
src/mcp_coder/utils/github_operations/ci_results_manager.py # Add implementation
pyproject.toml                                              # Add requests dependency
```

## WHAT: Main Components

### Shared Helper (Decision 16)
```python
def _download_and_extract_zip(self, url: str) -> Dict[str, str]:
    """Download ZIP from URL and extract contents.
    
    Args:
        url: URL to download ZIP from
    
    Returns:
        Dictionary mapping filenames to their contents as strings
    """
```

### Method Signature
```python
@log_function_call
@_handle_github_errors(default_return={"logs": {}, "jobs": []})
def get_run_logs(self, run_id: int) -> Dict[str, Any]:
    """Get all console logs from a workflow run with job status info.
    
    Args:
        run_id: Workflow run ID to get logs from
    
    Returns:
        Dictionary with:
        - "logs": Dict[str, str] mapping log filenames to contents
        - "jobs": List[Dict] with job status info (id, name, status, conclusion)
        Consumer can use job info to identify which logs belong to failed jobs.
    
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

### _download_and_extract_zip Implementation
```python
def _download_and_extract_zip(self, url: str) -> Dict[str, str]:
    # 1. Make authenticated HTTP request with Bearer token
    # 2. Handle ZIP response - extract all files
    # 3. Return {filename: content} dictionary
    # 4. Handle HTTP/ZIP errors gracefully (return empty dict)
```

### get_run_logs Implementation
```python
def get_run_logs(self, run_id: int) -> Dict[str, Any]:
    # 1. Validate run_id parameter
    # 2. Get workflow run from GitHub API
    # 3. Get all jobs for the run (for status info)
    # 4. Download logs using _download_and_extract_zip()
    # 5. Return {"logs": {...}, "jobs": [...]} structure
```

## DATA: Test Cases and Expected Returns

### Test Cases Structure
```python
class TestDownloadAndExtractZip:
    def test_successful_download(self, ci_manager, mock_requests)
    def test_http_error(self, ci_manager, mock_requests)
    def test_invalid_zip(self, ci_manager, mock_requests)

class TestGetRunLogs:
    def test_successful_logs_with_job_info(self, mock_repo, ci_manager)
    def test_invalid_run_id(self, ci_manager) 
    def test_log_download_failure(self, mock_repo, ci_manager, mock_requests)
```

### Expected Return Examples
```python
# Successful case - all logs with job status info (Decision 15)
{
    "logs": {
        "test/1_Setup.txt": "Setting up...",
        "test/2_Run tests.txt": "Test failed: assertion error",
        "build/1_Setup.txt": "Setting up...",
        "build/2_Compile.txt": "Build successful"
    },
    "jobs": [
        {"id": 123, "name": "test", "status": "completed", "conclusion": "failure"},
        {"id": 124, "name": "build", "status": "completed", "conclusion": "success"}
    ]
}
# Consumer can filter logs by checking which jobs have conclusion='failure'

# No logs available
{"logs": {}, "jobs": []}
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
# HTTP errors during log download
# - Return empty logs dict
# - Log the error but don't fail the entire method

# ZIP extraction errors
# - Return empty dict for that file
# - Continue with other files
```

## Success Criteria
- [ ] Tests written first and define expected behavior
- [ ] Shared helper `_download_and_extract_zip()` implemented and tested
- [ ] Method returns all logs with job status info
- [ ] Handles HTTP errors gracefully during log download  
- [ ] Returns proper structure with logs and jobs
- [ ] Edge cases handled (no logs, invalid run ID)
- [ ] All tests pass (use @pytest.fixture pattern)