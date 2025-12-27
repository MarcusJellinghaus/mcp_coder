# Step 4: JUnit Artifact Parsing Implementation

## LLM Prompt
```
I'm implementing issue #213 - CI Pipeline Result Analysis Tool. Please refer to pr_info/steps/summary.md for the full architectural overview.

In this step, implement the get_junit_failures method:
1. Write tests for get_junit_failures method first (TDD approach)
2. Implement the method to download and parse JUnit XML artifacts
3. Extract test failure information (test name, failure message, file, etc.)
4. Handle multiple artifacts and XML parsing errors

This covers requirement 4 from the issue: "Download and parse artifacts (JUnit XML) for detailed failure information".
Follow existing patterns from other GitHub operations managers.
```

## WHERE: File Locations
```
tests/utils/github_operations/test_ci_results_manager.py    # Add test cases + test fixtures
src/mcp_coder/utils/github_operations/ci_results_manager.py # Add implementation
```

## WHAT: Main Function

### Method Signature
```python
@log_function_call
@_handle_github_errors(default_return=[])
def get_junit_failures(self, run_id: int) -> List[Dict[str, Any]]:
    """Get parsed test failures from JUnit XML artifacts.
    
    Args:
        run_id: Workflow run ID to get artifacts from
    
    Returns:
        List of failure details: [
            {
                "test_name": "test_function_name",
                "class_name": "TestClass", 
                "failure_message": "AssertionError: ...",
                "failure_type": "AssertionError",
                "file": "test_file.py",
                "line": "42"
            }
        ]
    
    Raises:
        GithubException: For authentication or permission errors
    """
```

### Helper Method
```python
def _parse_junit_xml(self, xml_content: str) -> List[Dict[str, Any]]:
    """Parse JUnit XML and extract failure information."""
```

## HOW: Integration Points

### PyGithub API Calls
```python
# Get workflow run artifacts
repo = self._get_repository()
workflow_run = repo.get_workflow_run(run_id)
artifacts = workflow_run.get_artifacts()

# Filter for JUnit/test result artifacts
junit_artifacts = [a for a in artifacts if 'junit' in a.name.lower() or 'test' in a.name.lower()]

# Download each artifact
artifact.download_url  # Get download URL
```

### XML Parsing
```python
import xml.etree.ElementTree as ET
import io
import zipfile

# Parse XML content
root = ET.fromstring(xml_content)

# Navigate JUnit XML structure
# <testsuite> -> <testcase> -> <failure>
```

## ALGORITHM: Core Logic

### get_junit_failures Implementation
```python
def get_junit_failures(self, run_id: int) -> List[Dict[str, Any]]:
    # 1. Validate run_id parameter
    # 2. Get workflow run and artifacts
    # 3. Filter artifacts for JUnit/test-related ones
    # 4. Download and extract each artifact (handle ZIP files)
    # 5. Parse XML content for test failures
    # 6. Return consolidated list of failure details
```

### JUnit XML Parsing Logic
```python
def _parse_junit_xml(self, xml_content: str) -> List[Dict[str, Any]]:
    # 1. Parse XML string with ElementTree
    # 2. Find all <testcase> elements with <failure> or <error> children
    # 3. Extract test metadata (name, classname, file)
    # 4. Extract failure details (message, type, stack trace)
    # 5. Return list of structured failure data
```

### Artifact Download and Extraction
```python
def _download_and_extract_artifact(self, artifact) -> List[str]:
    # 1. Download artifact ZIP file via HTTP
    # 2. Extract all XML files from ZIP
    # 3. Return list of XML file contents
    # 4. Handle download/extraction errors gracefully
```

## DATA: Test Cases and Expected Returns

### Test Cases Structure
```python
class TestGetJunitFailures:
    def test_single_junit_artifact_with_failures(self, mock_repo, ci_manager)
    def test_multiple_junit_artifacts(self, mock_repo, ci_manager)
    def test_no_junit_artifacts(self, mock_repo, ci_manager)
    def test_junit_artifact_no_failures(self, mock_repo, ci_manager)
    def test_invalid_xml_content(self, mock_repo, ci_manager)
    def test_artifact_download_failure(self, mock_repo, ci_manager)
    def test_invalid_run_id(self, ci_manager)
```

### Test Fixtures - Sample JUnit XML
```python
SAMPLE_JUNIT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="pytest" tests="3" failures="2" errors="0" time="1.234">
    <testcase classname="test_example" name="test_success" time="0.1"/>
    <testcase classname="test_example" name="test_assertion_failure" time="0.2">
        <failure message="AssertionError: expected 5, got 3" type="AssertionError">
            File "test_example.py", line 42, in test_assertion_failure
            assert result == 5
            AssertionError: expected 5, got 3
        </failure>
    </testcase>
    <testcase classname="test_other" name="test_value_error" time="0.3">
        <error message="ValueError: invalid input" type="ValueError">
            File "test_other.py", line 15, in test_value_error
            raise ValueError("invalid input")
            ValueError: invalid input
        </error>
    </testcase>
</testsuite>"""
```

### Expected Return Structure
```python
# Parsed failures from above XML
[
    {
        "test_name": "test_assertion_failure",
        "class_name": "test_example",
        "failure_message": "AssertionError: expected 5, got 3",
        "failure_type": "AssertionError", 
        "file": "test_example.py",
        "line": "42",
        "details": "File \"test_example.py\", line 42, in test_assertion_failure\nassert result == 5\nAssertionError: expected 5, got 3"
    },
    {
        "test_name": "test_value_error",
        "class_name": "test_other", 
        "failure_message": "ValueError: invalid input",
        "failure_type": "ValueError",
        "file": "test_other.py", 
        "line": "15",
        "details": "File \"test_other.py\", line 15, in test_value_error\nraise ValueError(\"invalid input\")\nValueError: invalid input"
    }
]

# No failures case
[]

# No artifacts case  
[]
```

### Mock Setup for Tests
```python
# Mock artifact
mock_artifact = Mock()
mock_artifact.name = "junit-test-results"
mock_artifact.download_url = "https://github.com/.../artifacts/.../zip" 

# Mock ZIP file content
mock_zip_content = b"PK..." # ZIP file bytes containing XML

# Mock workflow run
mock_run = Mock()
mock_run.get_artifacts.return_value = [mock_artifact]
mock_repo.get_workflow_run.return_value = mock_run

# Mock HTTP response for artifact download
mock_response = Mock()
mock_response.content = mock_zip_content
```

### Edge Cases to Handle
```python
# Artifact filtering criteria
junit_indicators = ['junit', 'test', 'results', 'report']

# XML parsing errors
# - Malformed XML: return empty list, log warning
# - Missing expected elements: skip those test cases
# - Empty artifacts: return empty list

# Download errors  
# - Network failures: return empty list, log error
# - ZIP extraction errors: skip that artifact, continue with others
```

## Success Criteria
- [ ] Tests written first with sample JUnit XML fixtures
- [ ] Method downloads and extracts JUnit artifacts correctly
- [ ] XML parsing extracts all failure/error information
- [ ] Handles multiple artifacts and consolidates results
- [ ] Graceful error handling for download/parsing failures
- [ ] Returns structured failure data with all required fields
- [ ] All tests pass