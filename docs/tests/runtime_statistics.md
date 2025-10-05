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
- `tests/cli/test_main.py::TestCLIIntegration::test_cli_help_via_python_module` - **10.20s** ⚠️ CRITICAL
- `tests/utils/test_log_utils.py::TestLogFunctionCall::test_log_function_call_with_exception` - **5.76s** ⚠️ CRITICAL
- `tests/llm/providers/claude/test_claude_code_api.py::TestAskClaudeCodeApiAsync::test_timeout_handling` - **1.06s** ⚠️ CRITICAL

#### Claude CLI Integration Tests (Exceeding 10.0s threshold)
- `test_verify_command_structure` - **98.72s** 🚨 EXTREME
- `test_cli_with_session` - **85.58s** 🚨 EXTREME
- `test_cli_accepts_session_id` - **84.11s** 🚨 EXTREME
- `test_simple_cli_question` - **84.10s** 🚨 EXTREME
- `test_cli_session_continuity_real` - **70.34s** 🚨 EXTREME
- `test_real_verification` - **54.60s** 🚨 EXTREME
- `test_ask_llm_cli_paris_question` - **48.22s** 🚨 EXTREME

#### Claude API Integration Tests (Exceeding 30.0s threshold)
- `test_api_with_session` - **94.70s** 🚨 EXTREME
- `test_simple_api_question` - **77.62s** ⚠️ CRITICAL
- `test_api_basic_call_without_session` - **77.26s** ⚠️ CRITICAL
- `test_ask_llm_api_paris_question` - **73.70s** ⚠️ CRITICAL
- `test_api_session_continuity_real` - **73.66s** ⚠️ CRITICAL
- `test_api_cost_tracking` - **56.05s** ⚠️ CRITICAL

#### Git Integration Tests (Exceeding 10.0s threshold)
- `test_commit_message_variations_workflow` - **135.89s** 🚨 EXTREME
- `test_git_status_consistency_workflow` - **129.30s** 🚨 EXTREME
- `test_commit_workflows` - **107.08s** 🚨 EXTREME
- `test_get_git_diff_integration_with_existing_functions` - **106.81s** 🚨 EXTREME
- `test_empty_to_populated_repository_workflow` - **106.46s** 🚨 EXTREME
- `test_multiple_commit_cycles` - **106.32s** 🚨 EXTREME
- `test_get_git_diff_complete_workflow` - **105.46s** 🚨 EXTREME
- `test_real_world_development_workflow` - **99.96s** 🚨 EXTREME
- `test_unicode_and_binary_files` - **89.63s** 🚨 EXTREME
- `test_file_tracking_status_workflow` - **88.13s** 🚨 EXTREME
- `test_complete_project_lifecycle_workflow` - **86.99s** 🚨 EXTREME
- `test_file_modification_detection_workflow` - **86.31s** 🚨 EXTREME
- `test_staged_vs_unstaged_changes_workflow` - **79.28s** 🚨 EXTREME
- `test_modify_existing_files_workflow` - **72.46s** 🚨 EXTREME
- `test_mixed_file_operations_workflow` - **67.12s** 🚨 EXTREME
- `test_staging_all_changes_workflow` - **65.12s** 🚨 EXTREME
- `test_cross_platform_paths` - **62.07s** 🚨 EXTREME
- `test_staging_specific_files_workflow` - **60.16s** 🚨 EXTREME
- `test_concurrent_access_simulation` - **59.91s** 🚨 EXTREME
- `test_is_working_directory_clean` - **58.44s** 🚨 EXTREME

#### Formatter Integration Tests (Exceeding 8.0s threshold)
- `test_has_mypy_errors_convenience_function` - **37.32s** 🚨 EXTREME
- `test_mypy_check_on_actual_codebase` - **34.10s** 🚨 EXTREME
- `test_configuration_conflicts_from_analysis` - **33.62s** 🚨 EXTREME
- `test_mypy_check_clean_code` - **26.30s** ⚠️ CRITICAL
- `test_mypy_check_with_type_errors` - **23.05s** ⚠️ CRITICAL
- `test_error_resilience_mixed_scenarios` - **15.85s** ⚠️ CRITICAL
- `test_idempotent_behavior_no_changes_on_second_run` - **14.82s** ⚠️ CRITICAL
- `test_complete_formatting_workflow_with_exit_codes` - **11.75s** ⚠️ CRITICAL
- `test_individual_formatter_error_handling` - **11.38s** ⚠️ CRITICAL
- `test_re_exports_work_from_init` - **11.00s** ⚠️ CRITICAL
- `test_step0_code_samples_from_analysis` - **10.88s** ⚠️ CRITICAL
- `test_formatter_target_directory_handling` - **8.23s** ⚠️ WARNING

#### GitHub Integration Tests (Exceeding 30.0s threshold)
- `test_list_pull_requests_with_filters` - **138.35s** 🚨 EXTREME
- `test_complete_issue_workflow` - **41.08s** ⚠️ CRITICAL
- `test_pr_manager_lifecycle` - **38.96s** ⚠️ CRITICAL

## Performance Trends

### Analysis Summary (2025-10-05)
- **Total Tests**: 1,034 (15 failed, 1,013 passed, 6 skipped)
- **Total Execution Time**: 849.10s (14 minutes 9 seconds)
- **Critical Issues Identified**: 47 tests exceeding critical thresholds
- **Most Problematic Categories**: 
  1. Git Integration Tests (20 tests >10s, avg ~90s each)
  2. Claude CLI Integration (7 tests >10s, avg ~75s each)
  3. Formatter Integration (12 tests >8s, avg ~20s each)

### Key Performance Insights
- **Git integration tests** show extreme performance degradation (60-135s per test)
- **Claude CLI/API tests** are network-dependent and highly variable
- **Unit tests** have 3 critical violations that should be addressed immediately
- **Formatter tests** running mypy checks are resource-intensive

## Last Analysis
- **Date**: 2025-10-05 05:56:38
- **Branch**: 103-commit-auto-review
- **Status**: ✅ Complete - Critical issues identified and documented
- **Next Review**: Recommended after performance optimizations

## Notes
- Thresholds are based on test category and expected complexity
- Integration tests are expected to be slower due to external dependencies
- Performance trends help identify gradual degradation vs sudden changes
- This document is automatically updated by the runtime statistics review process
- 🚨 EXTREME = >3x threshold exceeded
- ⚠️ CRITICAL = >1x threshold exceeded but <3x
- ⚠️ WARNING = Above warning threshold but below critical
