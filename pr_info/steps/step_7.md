# Step 7: Restructure Test Files

## Objective
Split the monolithic test file (1,848 lines) into a test package with symmetrical structure matching the source modules.

## LLM Prompt
```
Based on summary.md and Decisions.md, implement Step 7 of the coordinator module refactoring. Create a test package at tests/cli/commands/coordinator/ with separate test files for core.py tests, commands.py tests, and integration tests. Move test classes to appropriate files and delete the original test_coordinator.py. Preserve all existing test functionality.
```

## Implementation Details

### WHERE (Files to Create/Delete)

**New Directory:**
- `tests/cli/commands/coordinator/`

**New Files:**
- `tests/cli/commands/coordinator/__init__.py`
- `tests/cli/commands/coordinator/test_core.py`
- `tests/cli/commands/coordinator/test_commands.py`
- `tests/cli/commands/coordinator/test_integration.py`

**File to Delete:**
- `tests/cli/commands/test_coordinator.py`

### WHAT (Test Class Distribution)

**test_core.py** (Tests for `core.py` functions):
```python
# Configuration tests
class TestLoadRepoConfig:
class TestValidateRepoConfig:
class TestGetJenkinsCredentials:
class TestGetCacheRefreshMinutes:

# Issue filtering tests
class TestGetEligibleIssues:

# Workflow dispatch tests
class TestDispatchWorkflow:

# Cache file operation tests
class TestCacheFilePath:
class TestCacheFileOperations:
class TestStalenessLogging:
class TestGetCachedEligibleIssues:
```

**test_commands.py** (Tests for `commands.py` functions):
```python
class TestFormatJobOutput:
class TestExecuteCoordinatorTest:
class TestExecuteCoordinatorRun:
```

**test_integration.py** (End-to-end integration tests):
```python
class TestCoordinatorRunCacheIntegration:
class TestCacheUpdateIntegration:
```

### HOW (Import Updates)

**test_core.py imports:**
```python
from mcp_coder.cli.commands.coordinator.core import (
    load_repo_config,
    validate_repo_config,
    get_jenkins_credentials,
    get_cache_refresh_minutes,
    get_eligible_issues,
    dispatch_workflow,
    _get_cache_file_path,
    _load_cache_file,
    _save_cache_file,
    _log_stale_cache_entries,
    get_cached_eligible_issues,
    CacheData,
)
from mcp_coder.cli.commands.coordinator.workflow_constants import WORKFLOW_MAPPING
```

**test_commands.py imports:**
```python
from mcp_coder.cli.commands.coordinator.commands import (
    format_job_output,
    execute_coordinator_test,
    execute_coordinator_run,
)
from mcp_coder.cli.commands.coordinator.command_templates import (
    DEFAULT_TEST_COMMAND,
    DEFAULT_TEST_COMMAND_WINDOWS,
)
```

**test_integration.py imports:**
```python
from mcp_coder.cli.commands.coordinator import (
    execute_coordinator_run,
    get_cached_eligible_issues,
    dispatch_workflow,
    _update_issue_labels_in_cache,
)
```

### ALGORITHM (Migration Steps)

```
1. Create tests/cli/commands/coordinator/ directory
2. Create __init__.py (empty)
3. Create test_core.py with core.py test classes + imports
4. Create test_commands.py with commands.py test classes + imports
5. Create test_integration.py with integration test classes + imports
6. Run pytest to verify all tests pass in new locations
7. Delete original tests/cli/commands/test_coordinator.py
8. Run final quality checks
```

### DATA (Test Class Mapping)

| Original Class | New File | Line Count |
|---------------|----------|------------|
| TestLoadRepoConfig | test_core.py | ~124 lines |
| TestValidateRepoConfig | test_core.py | ~96 lines |
| TestGetJenkinsCredentials | test_core.py | ~49 lines |
| TestGetCacheRefreshMinutes | test_core.py | ~44 lines |
| TestGetEligibleIssues | test_core.py | ~85 lines |
| TestDispatchWorkflow | test_core.py | ~207 lines |
| TestCacheFilePath | test_core.py | ~31 lines |
| TestCacheFileOperations | test_core.py | ~81 lines |
| TestStalenessLogging | test_core.py | ~88 lines |
| TestGetCachedEligibleIssues | test_core.py | ~180 lines |
| TestFormatJobOutput | test_commands.py | ~26 lines |
| TestExecuteCoordinatorTest | test_commands.py | ~76 lines |
| TestExecuteCoordinatorRun | test_commands.py | ~128 lines |
| TestCoordinatorRunCacheIntegration | test_integration.py | ~261 lines |
| TestCacheUpdateIntegration | test_integration.py | ~324 lines |

**Estimated file sizes:**
- `test_core.py`: ~985 lines
- `test_commands.py`: ~230 lines
- `test_integration.py`: ~585 lines

## Test Strategy

**Verification approach:**
1. Create new test files with moved test classes
2. Run pytest on new test package to verify all tests pass
3. Compare test counts before and after to ensure no tests lost
4. Delete original file only after verification

**Commands:**
```bash
# Before deletion - count tests
pytest tests/cli/commands/test_coordinator.py --collect-only | grep "test session"

# After creation - count tests in new package
pytest tests/cli/commands/coordinator/ --collect-only | grep "test session"

# Verify all pass
pytest tests/cli/commands/coordinator/ -v
```

## Success Criteria
- [ ] `tests/cli/commands/coordinator/` package created
- [ ] `test_core.py` contains all core.py test classes
- [ ] `test_commands.py` contains all commands.py test classes
- [ ] `test_integration.py` contains all integration test classes
- [ ] All tests pass in new locations
- [ ] Test count matches original (no tests lost)
- [ ] Original `test_coordinator.py` deleted
- [ ] pylint, pytest, mypy quality checks pass

## Dependencies
- **Requires**: Step 6 completion (constants modules exist for correct imports)
- **Provides**: Symmetrical test structure matching source modules
- **Result**: Complete refactoring with clean module and test organization
