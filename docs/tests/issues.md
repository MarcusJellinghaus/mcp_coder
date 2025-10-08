# Test Performance Issues and Review Queue

## Active Issues

### 🚨 PRIORITY 1 - MyPy Progressive Regression

#### Issue #008: MyPy Test Getting Progressively Slower
**Status**: 🚨 CRITICAL - Requires urgent investigation  
**Test**: `tests/test_mcp_code_checker_integration.py::TestMypyIntegration::test_mypy_check_on_actual_codebase`

**Performance Trend**:
- Baseline (Oct 5): 7.47s
- Oct 7 AM: 31.28s (+319%)
- Oct 7 PM: **48.65s** (+551%) 🚨🚨

**Suspected Causes**: Codebase growth, MyPy cache invalidation, type stub changes, import graph complexity

**Actions Required**:
- [ ] Compare file count: `git diff --stat 103-commit-auto-review...various_changes`
- [ ] Check MyPy cache validity
- [ ] Run with verbose output: `mypy --verbose src/`
- [ ] Review dependencies: `git diff pyproject.toml`

**Next Steps**: Implement MyPy cache warming, consider splitting test scopes, add performance metrics to CI

---

### ⚠️ PRIORITY 2 - Claude Integration Tests

#### Issue #009: Claude Tests 22-62% Slower
**Status**: ⚠️ MONITOR - Likely network/API latency  
**Tests**: 3 tests in `tests/llm/providers/claude/test_claude_integration.py`

**Current Performance**:
- `test_basic_cli_api_integration`: 49.96s → **80.72s** (+62%)
- `test_interface_contracts`: 53.98s → **79.57s** (+47%)
- `test_session_continuity`: 58.08s → **70.63s** (+22%)

**Actions Required**:
- [ ] Check Claude CLI version: `claude --version`
- [ ] Monitor API response times
- [ ] Review for new validations or timeout changes

---

### 🟡 PRIORITY 3 - GitHub Integration Tests

#### Issue #010: GitHub API Test 26% Slower
**Status**: 🟡 MONITOR - External API variation  
**Test**: `tests/utils/github_operations/test_github_utils.py::TestPullRequestManagerIntegration::test_list_pull_requests_with_filters`

**Performance**: 134.53s → 168.97s (+26%)

**Actions Required**:
- [ ] Monitor trend over next 3 runs
- [ ] Check GitHub API rate limits during test execution

---

## Resolved Issues

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
**Status**: ✅ RESOLVED - 63% faster  
**Test**: `tests/test_mcp_code_checker_integration.py::TestMypyIntegration::test_has_mypy_errors_convenience_function`

**Performance**: 9.57s → **3.56s** (-63%)

**Note**: Still above 3.0s warning threshold but significant improvement.

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
