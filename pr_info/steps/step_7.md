# Step 7: Move Shared Test Fixtures to conftest.py

## LLM Prompt
```
I'm implementing issue #213 - CI Pipeline Result Analysis Tool. Please refer to pr_info/steps/summary.md for the full architectural overview.

This is a code review follow-up step. Implement:
1. Create/update `tests/utils/github_operations/conftest.py`
2. Move shared fixtures (`mock_repo`, `ci_manager`, `mock_artifact`, `mock_zip_content`) from test files
3. Remove duplicate fixture definitions from test classes

Follow Decision 27 from pr_info/steps/Decisions.md.
```

## WHERE: File Locations
```
tests/utils/github_operations/conftest.py                   # Create/update with shared fixtures
tests/utils/github_operations/test_ci_results_manager.py    # Remove duplicate fixtures
```

## WHAT: Main Components

### Shared Fixtures to Move
```python
# tests/utils/github_operations/conftest.py

import io
import zipfile
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, patch

import pytest

from mcp_coder.utils.github_operations import CIResultsManager


@pytest.fixture
def mock_repo() -> Mock:
    """Mock GitHub repository for testing."""
    return Mock()


@pytest.fixture
def ci_manager(mock_repo: Mock) -> CIResultsManager:
    """CIResultsManager instance for testing with mocked dependencies."""
    repo_url = "https://github.com/test/repo.git"

    with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
        mock_config.return_value = "test_token"

        with patch("github.Github") as mock_github:
            mock_github.return_value.get_repo.return_value = mock_repo
            manager = CIResultsManager(repo_url=repo_url)
            manager._repository = mock_repo
            return manager


@pytest.fixture
def mock_artifact() -> Mock:
    """Mock artifact for testing."""
    artifact = Mock()
    artifact.name = "test-results"
    artifact.archive_download_url = (
        "https://api.github.com/repos/test/repo/artifacts/123/zip"
    )
    return artifact


@pytest.fixture
def mock_zip_content() -> bytes:
    """Create mock ZIP content with test files."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("results.xml", "<?xml version='1.0'?><testsuites></testsuites>")
        zf.writestr("coverage.json", '{"total": 85.5}')
    return buffer.getvalue()
```

## HOW: Integration Points

### Fixture Discovery
- pytest automatically discovers fixtures in `conftest.py`
- Fixtures in `conftest.py` are available to all test files in the same directory and subdirectories
- No explicit imports needed in test files

### Remove Duplicates
- Remove `@pytest.fixture def mock_repo()` from each test class
- Remove `@pytest.fixture def ci_manager()` from each test class
- Remove `@pytest.fixture def mock_artifact()` from test classes
- Remove `@pytest.fixture def mock_zip_content()` from test classes

## ALGORITHM: Core Logic

```python
# 1. Identify all fixture definitions in test file
# 2. Check which fixtures are used by multiple test classes
# 3. Move shared fixtures to conftest.py
# 4. Remove duplicate definitions from test classes
# 5. Verify tests still pass with fixtures from conftest
```

## DATA: No data structure changes

This step only reorganizes test fixtures without changing their behavior.

## Success Criteria
- [ ] `conftest.py` created/updated with shared fixtures
- [ ] Duplicate fixtures removed from test classes
- [ ] All existing tests still pass
- [ ] No fixture-related warnings from pytest
