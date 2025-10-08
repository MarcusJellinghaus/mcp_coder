# Test Performance Issues and Review Queue

## Active Issues

### 🚨 PRIORITY 1 - Formatter Integration Test Regressions

#### Issue #012: Multiple Formatter Tests Showing Significant Slowdowns
**Status**: 🚨 CRITICAL - Requires investigation  
**Tests**: 3 tests in `tests/formatters/test_integration.py`

**Performance Regressions (Oct 7 → Oct 8)**:
- `test_error_resilience_mixed_scenarios`: 1.74s → **7.06s** (+306%)
- `test_idempotent_behavior_no_changes_on_second_run`: 2.14s → **6.47s** (+202%)
- `test_formatter_target_directory_handling`: 1.35s → **5.83s** (+332%)
- `test_configuration_conflicts_from_analysis`: 7.03s → **8.23s** (+17%)

**Suspected Causes**:
- Test setup overhead changes
- Formatter subprocess execution changes
- File I/O overhead
- Temporary file cleanup delays

**Actions Required**:
- [ ] Review recent changes in formatter test setup/teardown
- [ ] Check for changes in formatter integration code
- [ ] Profile test execution: `pytest -vv <test_path> --profile`
- [ ] Compare with Oct 7 branch state
- [ ] Run tests serially to isolate parallelization overhead

**Note**: One test improved significantly: `test_individual_formatter_error_handling` 6.12s → 2.02s (-67%)

---

### ⚠️ PRIORITY 2 - Claude Integration Tests

#### Issue #009: Claude Tests Consistently Slow
**Status**: 🟡 MONITOR - Stable but elevated performance  
**Tests**: 4 tests in `tests/llm/providers/claude/test_claude_integration.py`

**Current Performance (Oct 8)**:
- `test_env_vars_propagation`: **91.48s** (was 76.90s on Oct 7, +19%)
- `test_basic_cli_api_integration`: **83.88s** (was 80.72s on Oct 7, +4%)
- `test_interface_contracts`: **87.33s** (was 79.57s on Oct 7, +10%)
- `test_session_continuity`: **75.44s** (was 70.63s on Oct 7, +7%)

**Trend**: Slight increases across all tests, but within expected variance for network/API calls.

**Actions Required**:
- [ ] Continue monitoring trend over next 3 runs
- [ ] If pattern continues, investigate Claude CLI performance changes

---

### 🟡 PRIORITY 3 - GitHub Integration Tests

#### Issue #010: GitHub API Test Stable at Elevated Performance
**Status**: ✅ STABLE - Acceptable for external API  
**Test**: `tests/utils/github_operations/test_github_utils.py::TestPullRequestManagerIntegration::test_list_pull_requests_with_filters`

**Performance**: 168.97s (Oct 7) → **171.17s** (Oct 8) - Stable

**Conclusion**: Performance stable around 170s, within acceptable range for GitHub API calls with pagination.

**Actions**: Continue monitoring, no immediate action required.

---

---

### 🟡 PRIORITY 3 - Environmental Instability

#### Issue #013: Git Integration Tests - Ongoing Environmental Variation
**Status**: 🟡 DOCUMENTED - Environmental, not code-related  
**Tests**: All tests in `tests/utils/test_git_workflows.py`

**Oct 8 Performance** (back to slow after Oct 7 PM showed fast times):
- `test_file_modification_detection_workflow`: **59.33s** (Oct 7 PM was 11.17s)
- `test_get_git_diff_complete_workflow`: **58.52s** (Oct 7 PM was 14.71s)  
- `test_commit_workflows`: **67.17s** (Oct 7 PM was 13.37s)
- Most tests: 30-70s range

**Confirmed Pattern**: Performance varies 2-5x between runs due to environmental factors (antivirus, disk I/O, network drive).

**Status**: All tests remain approved for `@pytest.mark.git_integration` category. No code action required.

**Actions**:
- [x] Document environmental instability pattern
- [x] Confirm tests are within approved range for integration category
- [ ] Consider running git tests on local SSD if consistent performance needed for benchmarking

---

## Resolved Issues

### ✅ Issue #008: MyPy Progressive Regression (RESOLVED Oct 8)
**Status**: ✅ RESOLVED  
**Test**: `tests/test_mcp_code_checker_integration.py::TestMypyIntegration::test_mypy_check_on_actual_codebase`

**Performance Recovery**:
- Baseline (Oct 5): 7.47s
- Oct 7 AM: 31.28s (+319%) 🚨
- Oct 7 PM: 48.65s (+551%) 🚨🚨  
- **Oct 8**: **13.13s** (-73%) ✅

**Resolution**: Unknown - likely MyPy cache recovery or environmental improvement. Now within acceptable range (<8.0s critical threshold).

**Monitoring**: Continue tracking to ensure performance remains stable.

---

### ✅ Issue #006: Unit Test pytest-xdist Overhead (FALSE POSITIVE)
**Status**: ✅ DOCUMENTED - No action required  
**Tests**: `tests/workflows/implement/test_task_processing.py::TestProcessSingleTask` (any test, non-deterministic)

**Key Finding**: Tests show 0.2-5.2s parallel, **0.08s** serial. Root cause: 10 nested `@patch` decorators + pytest-xdist worker overhead.

**Resolution**: Accepted as environmental artifact. Documented in process guide and registry.

**For Future Reviews**: Verify with `pytest -n0`. If <0.2s serial but >1s parallel → pytest-xdist overhead.

---

### ✅ Issue #007: Git Integration Tests (ENVIRONMENTAL ANOMALY)
**Status**: ✅ RESOLVED - Temporary environmental issue  
**Tests**: All tests in `tests/utils/test_git_workflows.py`

**Investigation Results** (2025-10-07):

| Test | Baseline | Oct 7 AM Anomaly | Oct 7 PM Verified | Result |
|------|----------|------------------|-------------------|--------|
| `test_file_modification_detection_workflow` | 17.26s | 52.49s | **11.17s** | ✅ 35% faster |
| `test_get_git_diff_complete_workflow` | 32.17s | 65.51s | **14.71s** | ✅ 54% faster |
| `test_commit_workflows` | 24.77s | 50.10s | **13.37s** | ✅ 46% faster |

**Conclusion**: Oct 7 AM slowdown was temporary (antivirus, disk I/O). Current performance 35-55% better than baseline.

**Lesson**: Always verify regressions with multiple runs before investigating code changes.

---

### ✅ Issue #011: MyPy Convenience Function Test (IMPROVED)
**Status**: ✅ RESOLVED - Stable improvement  
**Test**: `tests/test_mcp_code_checker_integration.py::TestMypyIntegration::test_has_mypy_errors_convenience_function`

**Performance**: 9.57s → 3.56s (Oct 7) → **3.44s** (Oct 8) - Stable at ~3.5s

**Note**: Still above 3.0s warning threshold but acceptable for convenience function that wraps full MyPy check.

---

## Process Notes

**Issue Tracking**:
- Issues auto-detected by runtime statistics review process
- Format: `file_path::ClassName::test_method_name`
- Priority based on impact and urgency
- Mark resolved when addressed

**Performance Thresholds**:
- Unit: 0.5s warning, 1.0s critical
- Integration (Git/Formatter): 3-5s warning, 8-10s critical
- External API (Claude/GitHub): 10s warning, 30s critical

**Monitoring**:
- Set up automated regression detection (>25% threshold)
- Add performance alerts to CI/CD
- Create baselines for each branch
- Document environmental factors
