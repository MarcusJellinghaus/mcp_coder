# Step 4: Artifact Retrieval Implementation

## LLM Prompt
```
I'm implementing issue #213 - CI Pipeline Result Analysis Tool. Please refer to pr_info/steps/summary.md for the full architectural overview.

In this step, implement the get_artifacts method:
1. Write tests for get_artifacts method first (TDD approach)
2. Reuse `_download_and_extract_zip()` helper from Step 3 (Decision 16)
3. Implement the method to download and return artifact contents
4. Support optional name filtering
5. Handle binary files by returning bytes (Decision 19)
6. Handle edge cases (no artifacts, download errors)

This provides raw artifact data - parsing (e.g., JUnit XML) is left to the consumer.
No limit on artifact size - document memory implications (Decision 18).
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
@_handle_github_errors(default_return={})
def get_artifacts(
    self, 
    run_id: int, 
    name_filter: Optional[str] = None
) -> Dict[str, Union[str, bytes]]:
    """Download and return artifact contents from a workflow run.
    
    Args:
        run_id: Workflow run ID to get artifacts from
        name_filter: Optional filter - only return artifacts containing this string
                     in their name (case-insensitive). If None, returns all artifacts.
    
    Returns:
        Dictionary mapping artifact file names to their contents.
        Text files returned as str, binary files as bytes (Decision 19).
        Artifacts are ZIP files - contents are extracted and returned.
        Example: {"test-results.xml": "<xml content...>", "image.png": b"..."}
        
        Note: No size limit - consumer should use name_filter for large runs (Decision 18).
    
    Raises:
        GithubException: For authentication or permission errors
    """
```

## HOW: Integration Points

### PyGithub API Calls
```python
# Get workflow run artifacts
repo = self._get_repository()
workflow_run = repo.get_workflow_run(run_id)
artifacts = workflow_run.get_artifacts()

# Optional filtering by name
if name_filter:
    artifacts = [a for a in artifacts if name_filter.lower() in a.name.lower()]

# Download each artifact via archive_download_url
artifact.archive_download_url  # Get download URL
```

### HTTP Requests for Artifact Download (ZIP)
```python
import requests
import zipfile
import io

# Download artifact using Bearer token authentication
headers = {
    "Authorization": f"Bearer {self.github_token}",
    "Accept": "application/vnd.github.v3+json"
}
response = requests.get(artifact.archive_download_url, headers=headers, allow_redirects=True)

# Response is a ZIP file - extract contents
zip_buffer = io.BytesIO(response.content)
with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
    for file_name in zip_file.namelist():
        content = zip_file.read(file_name).decode('utf-8')
```

## ALGORITHM: Core Logic

### get_artifacts Implementation
```python
def get_artifacts(self, run_id: int, name_filter: Optional[str] = None) -> Dict[str, str]:
    # 1. Validate run_id parameter
    # 2. Get workflow run and artifacts list
    # 3. Apply name_filter if provided
    # 4. Download and extract each artifact ZIP
    # 5. Collect all file contents into result dictionary
    # 6. Return {filename: content} dictionary
```

### Artifact Download (Reuses Step 3 Helper)
```python
# Uses _download_and_extract_zip() from Step 3 (Decision 16)
# For each artifact:
#   contents = self._download_and_extract_zip(artifact.archive_download_url)
```

## DATA: Test Cases and Expected Returns

### Test Cases Structure
```python
class TestGetArtifacts:
    def test_single_artifact(self, mock_repo, ci_manager)
    def test_multiple_artifacts(self, mock_repo, ci_manager)
    def test_no_artifacts(self, mock_repo, ci_manager)
    def test_with_name_filter(self, mock_repo, ci_manager)
    def test_name_filter_no_match(self, mock_repo, ci_manager)
    def test_artifact_download_failure(self, mock_repo, ci_manager)
    def test_invalid_run_id(self, ci_manager)
    def test_binary_file_handling(self, mock_repo, ci_manager)
```

### Expected Return Examples
```python
# Single artifact with one file
{
    "test-results.xml": "<?xml version=\"1.0\"?>..."
}

# Multiple artifacts with mixed content (Decision 19)
{
    "junit.xml": "<?xml version=\"1.0\"?>...",      # str - text file
    "coverage.json": "{\"total\": 85.5, ...}",      # str - text file
    "screenshot.png": b"\x89PNG\r\n..."             # bytes - binary file
}

# No artifacts
{}

# With name_filter="junit" (only matching artifacts)
{
    "junit-results.xml": "<?xml version=\"1.0\"?>..."
}
```

### Mock Setup for Tests (use @pytest.fixture)
```python
@pytest.fixture
def mock_artifact():
    artifact = Mock()
    artifact.name = "test-results"
    artifact.archive_download_url = "https://api.github.com/repos/.../artifacts/.../zip"
    return artifact

@pytest.fixture
def mock_zip_content():
    # Create in-memory ZIP with test file
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        zf.writestr("results.xml", "<?xml version=\"1.0\"?>...")
    return buffer.getvalue()
```

### Edge Cases to Handle
```python
# Name filter behavior
# - Case insensitive matching
# - Empty filter = return all

# Download/extraction errors
# - Network failures: skip artifact, log error, continue with others
# - ZIP extraction errors: skip artifact, log error, continue

# Binary file handling (Decision 19)
# - Try UTF-8 decode first
# - If decode fails, return as bytes
# - No files are skipped

# Empty scenarios
# - No artifacts in run: return {}
# - All artifacts filtered out: return {}
# - All downloads fail: return {}
```

## Success Criteria
- [ ] Tests written first (use @pytest.fixture pattern)
- [ ] Method downloads and extracts artifacts correctly
- [ ] Optional name_filter works (case-insensitive)
- [ ] Returns raw file contents as strings
- [ ] Graceful error handling for download/extraction failures
- [ ] All tests pass
