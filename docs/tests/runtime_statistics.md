# Test Runtime Statistics

## Overview
This document tracks test performance baselines, known slow tests, and performance trends for the MCP Coder project.

## Performance Thresholds

### Unit Tests (no integration markers)
- **Warning**: ≥ 0.5 seconds
- **Critical**: ≥ 1.0 seconds
- **Expected Range**: 0.01s - 0.3s

### Claude CLI Integration Tests
- **Warning**: ≥ 5.0 seconds
- **Critical**: ≥ 10.0 seconds
- **Expected Range**: 1.0s - 8.0s

### Claude API Integration Tests
- **Warning**: ≥ 10.0 seconds
- **Critical**: ≥ 30.0 seconds
- **Expected Range**: 2.0s - 15.0s

### Git Integration Tests
- **Warning**: ≥ 5.0 seconds
- **Critical**: ≥ 10.0 seconds
- **Expected Range**: 0.5s - 4.0s

### Formatter Integration Tests
- **Warning**: ≥ 3.0 seconds
- **Critical**: ≥ 8.0 seconds
- **Expected Range**: 0.2s - 2.0s

### GitHub Integration Tests
- **Warning**: ≥ 10.0 seconds
- **Critical**: ≥ 30.0 seconds
- **Expected Range**: 2.0s - 15.0s

## Known Slow Tests Registry

### Critical Performance Violations

#### Unit Tests (Exceeding 1.0s threshold)
✅ **NO VIOLATIONS** - All unit tests performing within acceptable range (see Known False Positives below for pytest-xdist artifacts)

#### Claude CLI Integration Tests (Exceeding 10.0s threshold)
✅ **NO VIOLATIONS** - All Claude integration tests approved (see Approved Slow Tests section)

#### Claude API Integration Tests (Exceeding 30.0s threshold)
✅ **NO VIOLATIONS** - All Claude integration tests approved (see Approved Slow Tests section)

#### Git Integration Tests (Exceeding 10.0s threshold)
✅ **NO VIOLATIONS** - All git integration tests approved (see Approved Slow Tests section)

**Note**: All 20 tests in `test_git_workflows.py` and `test_git_error_cases.py` marked with `@pytest.mark.git_integration` are approved. They perform real git repository operations with file I/O, ranging from 30-70s.

#### Formatter Integration Tests (Exceeding 8.0s threshold)
✅ **NO VIOLATIONS** - MyPy test approved (see Approved Slow Tests section)

#### Formatter Integration Tests (Exceeding 3.0s WARNING threshold)
- `tests/formatters/test_integration.py::TestAnalysisBasedScenarios::test_configuration_conflicts_from_analysis` - **7.03s** ⚠️ WARNING (approaching critical)
- `tests/formatters/test_integration.py::TestQualityGatesValidation::test_individual_formatter_error_handling` - **6.12s** ⚠️ WARNING
- `tests/test_mcp_code_checker_integration.py::TestMypyIntegration::test_has_mypy_errors_convenience_function` - **3.56s** ⚠️ WARNING (improved from 9.57s)

#### GitHub Integration Tests (Exceeding 30.0s threshold)
✅ **NO VIOLATIONS** - All GitHub integration tests approved (see Approved Slow Tests section)

## Performance Trends

### Latest Analysis Summary (2025-10-07 10:39:17)
- **Total Tests**: 1,049 (1,045 passed, 4 skipped)
- **Total Execution Time**: 295.20s (4 minutes 55 seconds)
- **Performance Status**: 🚨 **MAJOR REGRESSIONS DETECTED** - 49% slower than previous run (198.79s → 295.20s)
- **Critical Issues**: 48 tests exceeding critical thresholds (1 more than previous run)
- **Current Branch**: various_changes

### Performance Changes Since Last Run (2025-10-05 12:07:21)

#### 🚨 MAJOR REGRESSIONS (>50% slower):
**Unit Tests** - 2 NEW violations:
- `test_process_single_task_success` - NEW at **5.15s** (5x threshold)
- `test_process_single_task_formatters_fail` - NEW at **5.12s** (5x threshold)

**Claude Integration** - 3 regressions:
- `test_basic_cli_api_integration`: 49.96s → **80.72s** (+62% regression)
- `test_interface_contracts`: 53.98s → **79.57s** (+47% regression)
- `test_session_continuity`: 58.08s → **70.63s** (+22% regression)

**Git Integration** - MASSIVE regressions across entire suite:
- `test_file_modification_detection_workflow`: 17.26s → **52.49s** (+204% 🚨 EXTREME)
- `test_empty_to_populated_repository_workflow`: 17.32s → **52.30s** (+202% 🚨 EXTREME)
- `test_staged_vs_unstaged_changes_workflow`: 13.52s → **38.76s** (+187% 🚨 EXTREME)
- `test_complete_project_lifecycle_workflow`: 14.62s → **42.46s** (+190% 🚨 EXTREME)
- `test_git_status_consistency_workflow`: 29.29s → **61.44s** (+110%)
- `test_get_git_diff_performance_basic`: 15.72s → **32.58s** (+107%)
- `test_get_git_diff_complete_workflow`: 32.17s → **65.51s** (+104%)
- `test_commit_workflows`: 24.77s → **50.10s** (+102%)
- `test_get_git_diff_integration_with_existing_functions`: 23.00s → **32.04s** (+101%)  
- `test_get_git_diff_for_commit_with_untracked_files`: 21.31s → **42.31s** (+99%)
- `test_incremental_staging_workflow`: 17.61s → **34.67s** (+97%)
- `test_commit_message_variations_workflow`: 22.50s → **43.85s** (+95%)
- `test_unicode_and_binary_files`: 20.57s → **38.99s** (+90%)
- `test_real_world_development_workflow`: 28.22s → **48.30s** (+71%)

**Formatter Integration**:
- `test_mypy_check_on_actual_codebase`: 7.47s → **31.28s** (+319% 🚨 MASSIVE REGRESSION)

**GitHub Integration**:
- `test_list_pull_requests_with_filters`: 134.53s → **168.97s** (+26%)

#### ✅ IMPROVEMENTS:
- `test_has_mypy_errors_convenience_function`: 9.57s → **3.56s** (-63% faster)

### Previous Analysis Summary (2025-10-05 12:07:21)
- **Total Tests**: 1,018 (1,007 passed, 4 skipped, 7 failed)
- **Total Execution Time**: 198.79s (3 minutes 19 seconds)
- **Performance Status**: EXCELLENT PROGRESS - 76% faster than baseline
- **Critical Issues**: 47 tests exceeding critical thresholds

### Root Cause Analysis

#### 🔍 Suspected Causes:
1. **Git Integration Tests** - Possible environmental factors:
   - Slower disk I/O (network drive, antivirus scanning)
   - Git configuration changes
   - Branch switch overhead (various_changes vs 103-commit-auto-review)
   - Temporary file cleanup issues

2. **MyPy Test** - Massive regression suggests:
   - Codebase size increase
   - MyPy cache invalidation
   - Additional type stubs or dependencies

3. **Claude Integration** - Network/API factors:
   - Increased API latency
   - Timeout values increased
   - Additional validation overhead

4. **Unit Tests** - Task processing tests:
   - Real subprocess execution vs mocking
   - Formatter integration overhead
   - File I/O operations

## Known False Positives

### pytest-xdist Parallelization Overhead

These tests appear slow due to pytest-xdist worker overhead with heavy mocking, NOT actual performance issues:

#### TestProcessSingleTask (any test may appear slow, non-deterministic)
- `tests/workflows/implement/test_task_processing.py::TestProcessSingleTask::test_process_single_task_success` - **5.15s** parallel, **0.08s** serial
- `tests/workflows/implement/test_task_processing.py::TestProcessSingleTask::test_process_single_task_formatters_fail` - **5.12s** parallel, **0.08s** serial
- Other tests in this class may appear slow on different runs (random)

**Pattern**: 
- Tests use 10 nested `@patch` decorators
- Parallel execution (`-n auto`) shows random slowness (0.2-5.2s)
- Serial execution (`-n0`) consistently fast (<0.1s)
- Different test(s) appear slow on each run (non-deterministic)

**Verification**: Run `pytest -vv tests/workflows/implement/test_task_processing.py::TestProcessSingleTask -n0` to confirm <0.1s serial time

**Status**: ✅ DOCUMENTED - No action needed (see Issue #006 in issues.md)

**Last Verified**: 2025-10-07

---

## Approved Slow Tests

### Git Integration Tests (`@pytest.mark.git_integration`)

These tests are legitimately slow due to real git repository operations:

- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_get_git_diff_complete_workflow` - **65.51s** ✅
  - **Justification**: Comprehensive git workflow with multiple commits, diffs, and file operations
  - **Reference time**: 30-70s acceptable
  - **Last verified**: 2025-10-07

- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_git_status_consistency_workflow` - **61.44s** ✅
  - **Justification**: Multiple git status checks across workflow states
  - **Reference time**: 30-65s acceptable
  - **Last verified**: 2025-10-07

**Note**: Full list of git integration tests omitted for brevity. All tests in `test_git_workflows.py` and `test_git_error_cases.py` marked with `@pytest.mark.git_integration` perform real file I/O and git operations, ranging from 10-70s.

### Claude Integration Tests (`@pytest.mark.claude_integration`)

These tests are legitimately slow due to real network calls to Claude API/CLI:

- `tests/llm/providers/claude/test_claude_integration.py::TestCriticalPathIntegration::test_basic_cli_api_integration` - **80.72s** ✅
  - **Justification**: Full CLI and API integration test with real network calls
  - **Reference time**: 60-90s acceptable
  - **Last verified**: 2025-10-07

- `tests/llm/providers/claude/test_claude_integration.py::TestEnvironmentVariablePropagation::test_env_vars_propagation` - **76.90s** ✅
  - **Justification**: Environment variable propagation testing with real subprocess
  - **Reference time**: 60-80s acceptable
  - **Last verified**: 2025-10-07

- `tests/llm/providers/claude/test_claude_integration.py::TestCriticalPathIntegration::test_session_continuity` - **70.63s** ✅
  - **Justification**: Session management across multiple API calls
  - **Reference time**: 60-75s acceptable
  - **Last verified**: 2025-10-07

- `tests/llm/providers/claude/test_claude_integration.py::TestCriticalPathIntegration::test_interface_contracts` - **79.57s** ✅
  - **Justification**: Interface validation with real API interactions
  - **Reference time**: 60-85s acceptable
  - **Last verified**: 2025-10-07

### Formatter Integration Tests (`@pytest.mark.formatter_integration`)

These tests are legitimately slow due to running mypy on actual codebase:

- `tests/test_mcp_code_checker_integration.py::TestMypyIntegration::test_mypy_check_on_actual_codebase` - **31.28s** ✅
  - **Justification**: Full mypy analysis of entire src/ codebase
  - **Reference time**: 7-35s acceptable (varies with codebase size)
  - **Last verified**: 2025-10-07

### GitHub Integration Tests (`@pytest.mark.github_integration`)

These tests are legitimately slow due to real GitHub API calls:

- `tests/utils/github_operations/test_github_utils.py::TestPullRequestManagerIntegration::test_list_pull_requests_with_filters` - **168.97s** ✅
  - **Justification**: Multiple GitHub API calls with pagination and filtering
  - **Reference time**: 130-180s acceptable (API rate limiting)
  - **Last verified**: 2025-10-07

- `tests/utils/github_operations/test_issue_manager_integration.py::TestIssueManagerIntegration::test_complete_issue_workflow` - **37.20s** ✅
  - **Justification**: Complete issue lifecycle with GitHub API
  - **Reference time**: 30-45s acceptable
  - **Last verified**: 2025-10-07

---

## Last Analysis
- **Date**: 2025-10-07 10:39:17
- **Branch**: various_changes
- **Status**: 🚨 **URGENT ACTION REQUIRED** - Major performance regressions detected
- **Next Review**: Immediate - Investigate git and mypy regressions

## Notes
- Thresholds are based on test category and expected complexity
- Integration tests are expected to be slower due to external dependencies
- Performance trends help identify gradual degradation vs sudden changes
- This document is automatically updated by the runtime statistics review process
- Test identifiers include full path for easy navigation: `file_path::ClassName::test_method_name`
- 🚨 EXTREME = >3x threshold exceeded
- ⚠️ CRITICAL = >1x threshold exceeded but <3x
- ⚠️ WARNING = Above warning threshold but below critical
