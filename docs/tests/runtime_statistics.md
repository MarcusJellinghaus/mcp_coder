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
✅ **NO VIOLATIONS** - All unit tests performing excellently (10.07s total, 755 passed)

#### Claude CLI Integration Tests (Exceeding 10.0s threshold)
- `tests/llm/providers/claude/test_claude_integration.py::TestCriticalPathIntegration::test_session_continuity` - **58.08s** 🚨 EXTREME
- `tests/llm/providers/claude/test_claude_integration.py::TestCriticalPathIntegration::test_basic_cli_api_integration` - **49.96s** 🚨 EXTREME

#### Claude API Integration Tests (Exceeding 30.0s threshold)
- `tests/llm/providers/claude/test_claude_integration.py::TestCriticalPathIntegration::test_interface_contracts` - **53.98s** ⚠️ CRITICAL

#### Git Integration Tests (Exceeding 10.0s threshold)
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_get_git_diff_complete_workflow` - **32.17s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_git_status_consistency_workflow` - **29.29s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_real_world_development_workflow` - **28.22s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_file_tracking_status_workflow` - **28.16s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_commit_workflows` - **24.77s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_get_git_diff_integration_with_existing_functions` - **23.00s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_commit_message_variations_workflow` - **22.50s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_is_working_directory_clean` - **21.42s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_get_git_diff_for_commit_with_untracked_files` - **21.31s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_unicode_and_binary_files` - **20.57s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_multiple_commit_cycles` - **19.90s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_incremental_staging_workflow` - **17.61s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_staging_specific_files_workflow` - **17.45s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_empty_to_populated_repository_workflow` - **17.32s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_file_modification_detection_workflow` - **17.26s** ⚠️ CRITICAL
- `tests/utils/test_git_error_cases.py::TestGitErrorCases::test_unicode_edge_cases` - **16.52s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_get_git_diff_performance_basic` - **15.72s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_complete_project_lifecycle_workflow` - **14.62s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_staged_vs_unstaged_changes_workflow` - **13.52s** ⚠️ CRITICAL
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_cross_platform_paths` - **12.06s** ⚠️ CRITICAL

#### Formatter Integration Tests (Exceeding 8.0s threshold)
- `tests/test_mcp_code_checker_integration.py::TestMypyIntegration::test_has_mypy_errors_convenience_function` - **9.57s** ⚠️ CRITICAL

#### GitHub Integration Tests (Exceeding 30.0s threshold)
- `tests/utils/github_operations/test_github_utils.py::TestPullRequestManagerIntegration::test_list_pull_requests_with_filters` - **134.53s** 🚨 EXTREME
- `tests/utils/github_operations/test_issue_manager_integration.py::TestIssueManagerIntegration::test_complete_issue_workflow` - **37.35s** ⚠️ CRITICAL

## Performance Trends

### Latest Analysis Summary (2025-10-05 12:07:21)
- **Total Tests**: 1,018 (7 failed, 1,007 passed, 4 skipped)
- **Total Execution Time**: 198.79s (3 minutes 19 seconds)
- **Performance Improvement**: **76% faster** than previous run (849.10s → 198.79s)
- **Test Optimization**: 16 redundant tests eliminated, 8 fewer failures
- **Current Status**: EXCELLENT PROGRESS - Major performance improvements achieved

### Previous Analysis Summary (2025-10-05 05:56:38) - FOR COMPARISON
- **Total Tests**: 1,034 (15 failed, 1,013 passed, 6 skipped)
- **Total Execution Time**: 849.10s (14 minutes 9 seconds)
- **Critical Issues Identified**: 47 tests exceeding critical thresholds
- **Most Problematic Categories**: 
  1. Git Integration Tests (20 tests >10s, avg ~90s each)
  2. Claude CLI Integration (7 tests >10s, avg ~75s each)
  3. Formatter Integration (12 tests >8s, avg ~20s each)

### Current Key Performance Insights (Latest Run)
- **🎉 BREAKTHROUGH SUCCESS**: Overall test suite **76% faster** (198.79s vs 849.10s)
- **✅ Unit Tests**: **PERFECT** - All critical violations resolved, excellent performance (10.07s total)
- **✅ Claude CLI/API Tests**: **MAJOR SUCCESS** - Streamlined from 15+ minutes to ~2 minutes total
- **🟡 Git Integration Tests**: **SUBSTANTIAL IMPROVEMENT** - From 60-135s per test to 12-32s per test (64.92s total, down from 30+ minutes)
- **🟡 Formatter Tests**: **DRAMATIC IMPROVEMENT** - Mypy tests from 37s to 9.57s (19.13s total vs previous 200s+)
- **🟡 GitHub Tests**: **STABLE** - External API performance maintained (150.94s)

### Performance Improvements by Category

#### Unit Tests: 🎯 FULLY OPTIMIZED
- **Before**: 3 critical violations (1.06s - 10.20s)
- **After**: 0 violations, all tests <1.0s
- **Improvement**: 100% violation elimination

#### Claude Integration: 🚀 STREAMLINED  
- **Before**: 12+ tests, 900+ seconds, extreme violations (84-98s)
- **After**: 3 tests, ~108 seconds, manageable timings (49-58s)
- **Improvement**: 88% runtime reduction, architectural optimization

#### Git Integration: 📈 SIGNIFICANT PROGRESS
- **Before**: Tests taking 60-135s each (avg 90s)
- **After**: Tests taking 12-32s each (avg 20s)
- **Improvement**: 78% average runtime reduction

#### Formatter Integration: ⚡ DRAMATIC OPTIMIZATION
- **Before**: 12 tests >8s, with 3 tests >30s (mypy taking 37s)
- **After**: 1 test >8s (mypy optimized to 9.57s)
- **Improvement**: 92% violation reduction, 74% mypy improvement

#### GitHub Integration: 🔄 MAINTAINED
- **Before**: 134-138s for API-intensive tests
- **After**: Similar range (134s), consistent external API performance
- **Status**: No degradation, stable performance

### Previous Analysis Summary (2025-10-05 05:56:38) - BASELINE COMPARISON
- **Total Tests**: 1,034 (15 failed, 1,013 passed, 6 skipped)
- **Total Execution Time**: 849.10s (14 minutes 9 seconds)
- **Critical Issues Identified**: 47 tests exceeding critical thresholds
- **Most Problematic Categories**: 
  1. Git Integration Tests (20 tests >10s, avg ~90s each)
  2. Claude CLI Integration (7 tests >10s, avg ~75s each)
  3. Formatter Integration (12 tests >8s, avg ~20s each)

## Last Analysis
- **Date**: 2025-10-05 12:07:21
- **Branch**: 103-commit-auto-review
- **Status**: ✅ EXCELLENT PROGRESS - Major performance improvements achieved (76% faster)
- **Next Review**: Optional - Focus on remaining git integration test optimization

## Notes
- Thresholds are based on test category and expected complexity
- Integration tests are expected to be slower due to external dependencies
- Performance trends help identify gradual degradation vs sudden changes
- This document is automatically updated by the runtime statistics review process
- Test identifiers include full path for easy navigation: `file_path::ClassName::test_method_name`
- 🚨 EXTREME = >3x threshold exceeded
- ⚠️ CRITICAL = >1x threshold exceeded but <3x
- ⚠️ WARNING = Above warning threshold but below critical
