# Step 8: Split Test File by Feature

## LLM Prompt
```
I'm implementing issue #213 - CI Pipeline Result Analysis Tool. Please refer to pr_info/steps/summary.md for the full architectural overview.

This is a code review follow-up step. Implement:
1. Split `test_ci_results_manager.py` (964 lines) into multiple focused test files
2. Organize tests by feature/method
3. Ensure shared fixtures from conftest.py are used (from Step 7)

Follow Decision 26 from pr_info/steps/Decisions.md.
```

## WHERE: File Locations
```
tests/utils/github_operations/test_ci_results_manager.py              # DELETE after split
tests/utils/github_operations/test_ci_results_manager_foundation.py   # CREATE
tests/utils/github_operations/test_ci_results_manager_status.py       # CREATE
tests/utils/github_operations/test_ci_results_manager_logs.py         # CREATE
tests/utils/github_operations/test_ci_results_manager_artifacts.py    # CREATE
```

## WHAT: Test Class Distribution

### test_ci_results_manager_foundation.py
```python
"""Tests for CIResultsManager foundation - initialization and validation."""

class TestCIResultsManagerFoundation:
    """Test the foundational components of CIResultsManager."""
    # - test_initialization_with_project_dir
    # - test_initialization_with_repo_url
    # - test_initialization_validation
    # - test_validate_branch_name
    # - test_validate_run_id
    # - test_cistatus_data_structure
    # - test_manager_inheritance
```

### test_ci_results_manager_status.py
```python
"""Tests for CIResultsManager get_latest_ci_status method."""

class TestGetLatestCIStatus:
    """Test the get_latest_ci_status method."""
    # - test_successful_status_retrieval
    # - test_no_workflow_runs_for_branch
    # - test_invalid_branch_name
    # - test_run_with_multiple_jobs
    # - test_github_api_error_handling
    # - test_run_without_jobs
```

### test_ci_results_manager_logs.py
```python
"""Tests for CIResultsManager log retrieval methods."""

class TestDownloadAndExtractZip:
    """Test the _download_and_extract_zip helper method."""
    # - test_successful_download
    # - test_http_error
    # - test_invalid_zip

class TestGetRunLogs:
    """Test the get_run_logs method."""
    # - test_successful_logs_retrieval
    # - test_invalid_run_id
```

### test_ci_results_manager_artifacts.py
```python
"""Tests for CIResultsManager artifact retrieval methods."""

class TestGetArtifacts:
    """Test the get_artifacts method."""
    # - test_single_artifact
    # - test_multiple_artifacts
    # - test_no_artifacts
    # - test_with_name_filter
    # - test_name_filter_no_match
    # - test_artifact_download_failure
    # - test_invalid_run_id
    # - test_binary_file_skipped_with_warning
    # - test_github_api_error_handling
```

## HOW: Integration Points

### Common Imports for Each File
```python
import io
import zipfile
from pathlib import Path
from typing import Dict
from unittest.mock import Mock, patch

import pytest
import requests
from github import GithubException

from mcp_coder.utils.github_operations import (
    CIResultsManager,
    CIStatusData,
)
```

### Fixture Usage
- All test files use fixtures from `conftest.py` (created in Step 7)
- No fixture duplication between files
- Fixtures are automatically available via pytest discovery

## ALGORITHM: Core Logic

```python
# 1. Identify test classes and their methods
# 2. Group by feature:
#    - Foundation: init, validation, data structures
#    - Status: get_latest_ci_status
#    - Logs: _download_and_extract_zip, get_run_logs
#    - Artifacts: get_artifacts
# 3. Create new files with appropriate classes
# 4. Move test methods to new files
# 5. Delete original file
# 6. Run pytest to verify all tests pass
```

## DATA: No data structure changes

This step only reorganizes test files without changing test logic.

## Success Criteria
- [ ] Original `test_ci_results_manager.py` deleted
- [ ] `test_ci_results_manager_foundation.py` created with foundation tests
- [ ] `test_ci_results_manager_status.py` created with status tests
- [ ] `test_ci_results_manager_logs.py` created with log tests
- [ ] `test_ci_results_manager_artifacts.py` created with artifact tests
- [ ] All tests pass (same count as before split)
- [ ] No duplicate test methods across files
