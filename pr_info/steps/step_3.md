# Step 3: Validate Matrix Implementation and Test External API Access

## LLM Prompt
```
Reference: pr_info/steps/summary.md - CI Pipeline Restructure

Implement Step 3: Create comprehensive validation tests for the matrix-based CI implementation from Step 2. Verify that the new approach meets all requirements and provides proper external API access for automated analysis.

Follow the requirements in this step document precisely.
```

## Objective
Validate the matrix CI implementation works correctly and provides the expected external API access for automated tools.

## WHERE
- `tests/ci/test_matrix_validation.py` (new test file)
- `.github/workflows/ci.yml` (validation target)

## WHAT

### Main Functions
```python
def test_matrix_job_independence():
    """Verify matrix jobs run independently and show correct status"""

def test_github_api_job_access():
    """Test external API access to individual job status"""
    
def test_failure_propagation():
    """Confirm individual failures don't affect other matrix jobs"""

def test_artifact_generation():
    """Verify JUnit XML artifacts are generated correctly"""

def test_forbidden_folders_integration():
    """Ensure forbidden-folders job integration preserved"""
```

## HOW

### Integration Points
- **GitHub API**: Use PyGithub for API access testing
- **Workflow validation**: Parse YAML structure to verify matrix config
- **Mock testing**: Simulate job failures to test independence
- **Integration markers**: Use `@pytest.mark.github_integration`

### Imports
```python
import yaml
import pytest
from github import Github
from pathlib import Path
from unittest.mock import Mock, patch
```

## ALGORITHM

### Core Logic (test_github_api_job_access)
```
1. Load GitHub API credentials from environment
2. Query workflow run for matrix job list
3. Verify job names match matrix configuration
4. Test individual job status retrieval
5. Confirm job conclusion values (success/failure)
6. Validate external tool can distinguish job results
```

## DATA

### API Response Structure
```python
# GitHub API job list response
JobListResponse = {
    'jobs': List[{
        'name': str,           # Matrix job name (black, isort, etc.)
        'conclusion': str,     # success, failure, skipped
        'status': str,         # completed, in_progress
        'steps': List[dict],   # Individual step details
        'html_url': str        # Job details URL
    }]
}

# Validation result
ValidationResult = {
    'matrix_jobs_found': List[str],
    'api_accessible': bool,
    'status_accuracy': bool,
    'external_tool_ready': bool
}
```

## Implementation Notes
- **External API testing**: Verify automated tools can access job data
- **Status validation**: Confirm red/green status reflects actual results
- **Integration testing**: Test with real GitHub API endpoints
- **Artifact verification**: Ensure test results properly uploaded
- **Comprehensive coverage**: Test both success and failure scenarios

## Success Criteria
- Matrix jobs accessible via GitHub API individually
- Job status reflects actual check results (red for failures)
- External automation can distinguish which specific checks failed
- Artifact uploads work correctly for test jobs
- All requirements from original issue satisfied
- No regression in existing functionality

## Validation Scenarios
1. **All checks pass**: All matrix jobs show green status
2. **Single check fails**: Failed job shows red, others show green
3. **Multiple checks fail**: Each failure shows individually in API
4. **API accessibility**: External tools can query job status
5. **Artifact access**: JUnit XML files available via artifacts API

## Integration Testing
- **Real workflow runs**: Test on actual GitHub repository
- **API endpoint verification**: Confirm `/actions/runs/{run_id}/jobs` works
- **External tool simulation**: Mock automated analysis tool behavior
- **Performance check**: Ensure matrix doesn't significantly increase runtime