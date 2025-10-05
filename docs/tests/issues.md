# Test Performance Issues and Review Queue

## Overview
This document tracks test performance issues that require human review and action items for test optimization.

## Active Issues

### PRIORITY 1 - Critical Unit Test Violations (Immediate Action Required)

#### Issue #001: Unit Test Performance Violations
**Status**: 🔴 Critical  
**Impact**: High - Unit tests should be fast for development workflow  
**Tests Affected**: 3 critical violations

**Violations**:
1. `test_cli_help_via_python_module` - **10.20s** (10x threshold)
2. `test_log_function_call_with_exception` - **5.76s** (5.7x threshold)  
3. `test_timeout_handling` - **1.06s** (1.1x threshold)

**Recommended Actions**:
- Investigate why CLI help command takes 10+ seconds
- Review exception logging performance - likely I/O bound
- Optimize timeout handling test - may be actually timing out
- Consider mocking external dependencies
- Split complex test scenarios into smaller units

### PRIORITY 2 - Git Integration Test Performance Crisis

#### Issue #002: Git Workflow Tests Extremely Slow
**Status**: 🔴 Critical  
**Impact**: Extreme - 20 tests taking 60-135s each (avg 90s)  
**Total Impact**: ~30 minutes for git tests alone

**Root Cause Analysis Needed**:
- Tests are performing actual git operations in real repositories
- May be creating large file structures or deep commit histories
- Possible I/O bottlenecks or subprocess overhead

**Recommended Actions**:
1. **Immediate**: Add `@pytest.mark.slow` to tests >60s
2. **Short-term**: Implement git operation mocking for unit-style tests
3. **Medium-term**: Reduce repository size/complexity in test fixtures
4. **Long-term**: Split into unit tests (mocked) and integration tests (real git)

### PRIORITY 3 - Formatter Integration Optimization

#### Issue #003: MyPy Integration Tests Resource-Intensive
**Status**: 🟡 Warning  
**Impact**: Medium - 12 tests >8s, with 3 tests >30s

**Analysis**:
- MyPy analysis on actual codebase is expensive
- Configuration conflict tests taking 33+ seconds
- Error handling scenarios are also slow

**Recommended Actions**:
- Use smaller, focused code samples for mypy tests
- Mock mypy results for configuration testing
- Separate "mypy integration" from "mypy performance" tests
- Consider caching mypy results between test runs

### PRIORITY 4 - External Integration Test Optimization

#### Issue #004: Claude CLI/API Integration Tests
**Status**: 🟡 Warning  
**Impact**: Medium - Network dependent, highly variable (48-98s)

**Recommended Actions**:
- Implement proper mocking for non-integration test scenarios
- Add retry logic with exponential backoff
- Consider running these tests separately in CI (nightly builds)
- Add `@pytest.mark.integration` and exclude from regular test runs

#### Issue #005: GitHub Integration Tests
**Status**: 🟡 Warning  
**Impact**: Medium - API rate limiting causing delays (138s max)

**Recommended Actions**:
- Implement GitHub API mocking for most test scenarios
- Use test-specific repositories to avoid rate limits
- Add proper error handling for rate limit scenarios
- Consider running these tests in separate CI pipeline

## Review Queue

### Tests Requiring Immediate Review
1. **Unit Tests >1s** - Should be optimized immediately
2. **Git workflow tests** - Need architectural review
3. **MyPy integration tests** - Resource usage optimization needed

### Tests for Future Optimization
1. Claude integration tests - Consider CI/CD pipeline changes
2. GitHub integration tests - API usage optimization
3. Formatter integration tests - Caching strategies

### Marker Recommendations
Based on performance analysis, recommend adding these pytest markers:

```python
# Add to extremely slow tests (>60s)
@pytest.mark.slow
@pytest.mark.integration

# Add to network-dependent tests
@pytest.mark.external_api
@pytest.mark.requires_network

# Add to tests requiring real git operations
@pytest.mark.git_integration

# Add to tests requiring real filesystem operations
@pytest.mark.filesystem
```

## Completed Actions

*No actions completed yet - first analysis run*

## Performance Optimization Strategies

### Immediate Actions (This Sprint)
1. Fix the 3 critical unit test violations
2. Add appropriate pytest markers to slow tests
3. Implement basic mocking for git operations in unit tests

### Short-term Actions (Next Sprint)
1. Optimize git integration test architecture
2. Implement mypy result caching
3. Add CI configuration to run slow tests separately

### Long-term Actions (Next Quarter)
1. Comprehensive test architecture review
2. Performance regression testing in CI
3. Automated performance monitoring and alerting

## Process Notes
- Issues are automatically detected and added by the runtime statistics review process
- Each issue includes priority level, impact assessment, and recommended actions
- Issues should be reviewed and addressed in priority order
- Mark issues as completed when resolved and document the solution
- Performance thresholds may need adjustment based on infrastructure capabilities

## Monitoring Recommendations
1. Set up automated performance regression detection
2. Add performance metrics to CI/CD pipeline
3. Create alerts for tests exceeding 2x normal execution time
4. Regular review of test execution patterns and bottlenecks
