# Test Performance Issues and Review Queue

## Overview
This document tracks test performance issues that require human review and action items for test optimization.

## Active Issues

### PRIORITY 1 - Critical Unit Test Violations (Immediate Action Required)

#### Issue #001: Unit Test Performance Violations
**Status**: 🔴 Critical  
**Impact**: High - Unit tests should be fast for development workflow  
**Tests Affected**: 3 critical violations

**Specific Test Locations**:
1. `tests/cli/test_main.py::TestCLIIntegration::test_cli_help_via_python_module` - **10.20s** (10x threshold)
2. `tests/utils/test_log_utils.py::TestLogFunctionCall::test_log_function_call_with_exception` - **5.76s** (5.7x threshold)  
3. `tests/llm/providers/claude/test_claude_code_api.py::TestAskClaudeCodeApiAsync::test_timeout_handling` - **1.06s** (1.1x threshold)

**Recommended Actions**:
- **File 1**: `tests/cli/test_main.py` - Investigate CLI help command performance, likely subprocess overhead
- **File 2**: `tests/utils/test_log_utils.py` - Review exception logging performance, possibly I/O bound
- **File 3**: `tests/llm/providers/claude/test_claude_code_api.py` - Optimize timeout handling test, may be actually timing out
- Consider mocking external dependencies in all three locations
- Split complex test scenarios into smaller units

### PRIORITY 2 - Git Integration Test Performance Crisis

#### Issue #002: Git Workflow Tests Extremely Slow
**Status**: 🔴 Critical  
**Impact**: Extreme - 20 tests taking 60-135s each (avg 90s)  
**Total Impact**: ~30 minutes for git tests alone  
**Primary File**: `tests/utils/test_git_workflows.py`

**Most Critical Tests in TestGitWorkflows class**:
1. `test_commit_message_variations_workflow` - **135.89s**
2. `test_git_status_consistency_workflow` - **129.30s**  
3. `test_commit_workflows` - **107.08s**
4. `test_get_git_diff_integration_with_existing_functions` - **106.81s**
5. `test_empty_to_populated_repository_workflow` - **106.46s**

**Additional Critical Test**:
- `tests/utils/test_git_error_cases.py::TestGitErrorCases::test_concurrent_access_simulation` - **59.91s**

**Root Cause Analysis Needed**:
- Tests are performing actual git operations in real repositories
- May be creating large file structures or deep commit histories
- Possible I/O bottlenecks or subprocess overhead

**Recommended Actions**:
1. **Immediate**: Add `@pytest.mark.slow` to all tests >60s in `tests/utils/test_git_workflows.py`
2. **Short-term**: Implement git operation mocking for unit-style tests
3. **Medium-term**: Reduce repository size/complexity in test fixtures
4. **Long-term**: Split into unit tests (mocked) and integration tests (real git)

### PRIORITY 3 - Formatter Integration Optimization

#### Issue #003: MyPy Integration Tests Resource-Intensive
**Status**: 🟡 Warning  
**Impact**: Medium - 12 tests >8s, with 3 tests >30s

**Primary Files & Tests**:
- `tests/test_mcp_code_checker_integration.py::TestMypyIntegration`:
  - `test_has_mypy_errors_convenience_function` - **37.32s**
  - `test_mypy_check_on_actual_codebase` - **34.10s**
  - `test_mypy_check_clean_code` - **26.30s**
  - `test_mypy_check_with_type_errors` - **23.05s**

- `tests/formatters/test_integration.py`:
  - `TestAnalysisBasedScenarios::test_configuration_conflicts_from_analysis` - **33.62s**
  - `TestCompleteFormattingWorkflow::test_error_resilience_mixed_scenarios` - **15.85s**
  - `TestCompleteFormattingWorkflow::test_idempotent_behavior_no_changes_on_second_run` - **14.82s**
  - `TestCompleteFormattingWorkflow::test_complete_formatting_workflow_with_exit_codes` - **11.75s**
  - `TestQualityGatesValidation::test_individual_formatter_error_handling` - **11.38s**
  - `TestAnalysisBasedScenarios::test_step0_code_samples_from_analysis` - **10.88s**
  - `TestQualityGatesValidation::test_formatter_target_directory_handling` - **8.23s**

- `tests/formatters/test_main_api.py::TestAPIExportsAndImports::test_re_exports_work_from_init` - **11.00s**

**Analysis**:
- MyPy analysis on actual codebase is expensive
- Configuration conflict tests taking 33+ seconds
- Error handling scenarios are also slow

**Recommended Actions**:
- Use smaller, focused code samples for mypy tests in `test_mcp_code_checker_integration.py`
- Mock mypy results for configuration testing in `test_integration.py`
- Separate "mypy integration" from "mypy performance" tests
- Consider caching mypy results between test runs

### PRIORITY 4 - External Integration Test Optimization

#### Issue #004: Claude CLI/API Integration Tests
**Status**: 🟡 Warning  
**Impact**: Medium - Network dependent, highly variable

**Primary Files & Critical Tests**:
- `tests/llm/providers/claude/test_claude_cli_verification.py::TestVerifyCommandIntegration::test_verify_command_structure` - **98.72s**
- `tests/llm/providers/claude/test_claude_integration.py`:
  - `TestCriticalPathIntegration::test_basic_cli_api_integration` - **~30s**
  - `TestCriticalPathIntegration::test_interface_contracts` - **~30s**
  - `TestCriticalPathIntegration::test_session_continuity` - **~30s**

**Recommended Actions**:
- Add retry logic with exponential backoff for remaining verification tests
- Consider running CLI verification tests separately in CI (nightly builds)

#### Issue #005: GitHub Integration Tests
**Status**: 🟡 Warning  
**Impact**: Medium - API rate limiting causing delays (138s max)

**Primary Files & Tests**:
- `tests/utils/github_operations/test_github_utils.py::TestPullRequestManagerIntegration::test_list_pull_requests_with_filters` - **138.35s**
- `tests/utils/github_operations/test_issue_manager_integration.py::TestIssueManagerIntegration::test_complete_issue_workflow` - **41.08s**
- `tests/utils/github_operations/test_github_utils.py::TestPullRequestManagerIntegration::test_pr_manager_lifecycle` - **38.96s**

**Recommended Actions**:
- Implement GitHub API mocking for most test scenarios
- Use test-specific repositories to avoid rate limits
- Add proper error handling for rate limit scenarios
- Consider running these tests in separate CI pipeline

## Review Queue

### Tests Requiring Immediate Review
1. **Unit Tests >1s** - `tests/cli/test_main.py`, `tests/utils/test_log_utils.py`, `tests/llm/providers/claude/test_claude_code_api.py`
2. **Git workflow tests** - `tests/utils/test_git_workflows.py` (entire TestGitWorkflows class)
3. **MyPy integration tests** - `tests/test_mcp_code_checker_integration.py` (TestMypyIntegration class)

### Tests for Future Optimization
1. GitHub integration tests - `tests/utils/github_operations/test_github_utils.py`
2. Formatter integration tests - `tests/formatters/test_integration.py`

### Marker Recommendations
Based on performance analysis, recommend adding these pytest markers to specific test files:

```python
# Add to tests/utils/test_git_workflows.py (all TestGitWorkflows methods >60s)
@pytest.mark.slow
@pytest.mark.integration

# Add to tests/llm/providers/claude/ files
@pytest.mark.external_api
@pytest.mark.requires_network

# Add to tests/utils/test_git_workflows.py and test_git_error_cases.py
@pytest.mark.git_integration

# Add to tests with filesystem operations
@pytest.mark.filesystem
```

## Completed Actions

### ✅ MAJOR: Claude Integration Test Streamlining (October 2025)
**Issue**: Issue #004 - Claude CLI/API Integration Tests  
**Action Taken**: Consolidated 12+ redundant integration tests into 3 critical path tests  
**Files Modified**:
- `tests/llm/providers/claude/test_claude_integration.py` - Replaced multiple test classes with `TestCriticalPathIntegration`
- `tests/llm/providers/claude/test_claude_executable_finder.py` - Removed `TestIntegration` class
- `tests/llm/test_interface.py` - Removed redundant real integration test classes

**Performance Impact**:
- **Before**: 12+ tests, ~900+ seconds (~15+ minutes)
- **After**: 3 tests, ~90 seconds (~1.5 minutes)
- **Improvement**: 87% runtime reduction

**Coverage Maintained**:
- ✅ CLI integration path testing
- ✅ API integration path testing  
- ✅ Session continuity workflow
- ✅ Interface contract validation
- ✅ Error propagation through function call tree

**Strategy Applied**: Critical path testing - focused on testing different failure modes at each layer instead of redundant happy path testing

**Tests Removed** (no longer needed):
- `test_simple_cli_question`, `test_simple_api_question` - Consolidated into `test_basic_cli_api_integration`
- `test_cli_with_session`, `test_api_with_session`, `test_*_session_continuity_real` - Consolidated into `test_session_continuity`
- `test_api_basic_call_without_session` - Covered by `test_interface_contracts`
- `test_api_cost_tracking` - Removed (business feature, not critical path)
- `test_real_verification` - Removed (installation verification not critical path)
- `test_ask_llm_*_paris_question` - Redundant with basic integration tests

**Tests Added** (streamlined):
- `test_basic_cli_api_integration` - Both CLI and API paths in one test
- `test_interface_contracts` - ask_llm vs prompt_llm return type validation
- `test_session_continuity` - Session management through full stack

## Performance Optimization Strategies

### Immediate Actions (This Sprint)
1. **Fix 3 critical unit test violations**:
   - `tests/cli/test_main.py::TestCLIIntegration::test_cli_help_via_python_module`
   - `tests/utils/test_log_utils.py::TestLogFunctionCall::test_log_function_call_with_exception`
   - `tests/llm/providers/claude/test_claude_code_api.py::TestAskClaudeCodeApiAsync::test_timeout_handling`

2. **Add pytest markers** to slow tests in:
   - `tests/utils/test_git_workflows.py` (entire TestGitWorkflows class)
   - `tests/test_mcp_code_checker_integration.py`

3. **Implement basic mocking** for git operations in unit tests

### Short-term Actions (Next Sprint)
1. **Optimize git integration test architecture** in `tests/utils/test_git_workflows.py`
2. **Implement mypy result caching** for `tests/test_mcp_code_checker_integration.py`
3. **Add CI configuration** to run slow tests separately

### Long-term Actions (Next Quarter)
1. **Comprehensive test architecture review** across all test files
2. **Performance regression testing** in CI
3. **Automated performance monitoring** and alerting

## Process Notes
- Issues are automatically detected and added by the runtime statistics review process
- Each issue includes complete test file paths and class names for immediate developer action
- Test identifiers follow format: `file_path::ClassName::test_method_name`
- Issues should be reviewed and addressed in priority order
- Mark issues as completed when resolved and document the solution
- Performance thresholds may need adjustment based on infrastructure capabilities

## Monitoring Recommendations
1. Set up automated performance regression detection
2. Add performance metrics to CI/CD pipeline
3. Create alerts for tests exceeding 2x normal execution time
4. Regular review of test execution patterns and bottlenecks
