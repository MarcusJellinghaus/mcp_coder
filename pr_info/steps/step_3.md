# Step 3: Validation - Integration Tests & Performance Measurement

## LLM Prompt for This Step

```
You are implementing Step 3 of the performance optimization project outlined in pr_info/steps/summary.md.

CONTEXT: Steps 1-2 are complete - unit tests pass with lazy verification implementation. Now we validate the optimization works correctly in real integration scenarios.

TASK: Run integration tests, measure performance improvements, and verify error handling still provides helpful messages when Claude CLI is actually missing.

GOAL: Confirm 25-40% performance improvement and validate error handling quality.

REFERENCE:
- Summary: pr_info/steps/summary.md
- Step 1 (tests): pr_info/steps/step_1.md
- Step 2 (implementation): pr_info/steps/step_2.md
- Integration tests: tests/llm/providers/claude/test_claude_integration.py
```

## WHERE: Validation Scope

### Integration Tests to Run
**File**: `tests/llm/providers/claude/test_claude_integration.py`  
**Class**: `TestCriticalPathIntegration`  
**Tests**: 
- `test_interface_contracts` (expected: 79s → ~50s)
- `test_basic_cli_api_integration` (expected: 62s → ~45s)
- `test_session_continuity` (expected: 61s → ~45s)

### Error Scenario Testing
**Manual Testing**: Verify helpful error messages when CLI is missing
**Approach**: Temporarily rename Claude CLI, run API call, check error message

## WHAT: Validation Criteria

### 1. Integration Tests Must Pass
All integration tests should pass without modification (behavior unchanged).

### 2. Performance Improvement
**Target**: 25-40% reduction in integration test runtime  
**Measurement**: Compare before/after durations for each test

### 3. Error Message Quality
When Claude CLI is missing, error message must be helpful and actionable.

### 4. No Regressions
All other tests must continue to pass (no side effects).

## HOW: Validation Process

### Phase 1: Baseline Performance (Optional)
If you want to compare before/after, run tests before implementation:
```bash
# Optional: Get baseline (only if you haven't started implementation)
pytest tests/llm/providers/claude/test_claude_integration.py::TestCriticalPathIntegration -v --durations=0
```

### Phase 2: Run Integration Tests
```bash
# Run critical path integration tests
pytest tests/llm/providers/claude/test_claude_integration.py::TestCriticalPathIntegration -v --durations=0

# Run all Claude integration tests
pytest tests/llm/providers/claude/test_claude_integration.py -v --durations=0

# Run all Claude tests (unit + integration)
pytest tests/llm/providers/claude/ -v --durations=10
```

### Phase 3: Error Scenario Validation
Manual testing to verify error messages are helpful.

### Phase 4: Full Test Suite
```bash
# Ensure no regressions in other tests
pytest tests/llm/ -v -m "not git_integration and not github_integration and not formatter_integration"
```

## ALGORITHM: Performance Measurement

```python
# Pseudocode for performance comparison
tests_to_measure = [
    "test_interface_contracts",
    "test_basic_cli_api_integration", 
    "test_session_continuity"
]

FOR each test IN tests_to_measure:
    # 1. Get baseline (from docs or fresh run)
    baseline_duration = get_baseline(test)
    
    # 2. Run test with optimization
    optimized_duration = run_test(test)
    
    # 3. Calculate improvement
    improvement = (baseline_duration - optimized_duration) / baseline_duration * 100
    
    # 4. Validate improvement
    ASSERT improvement >= 25%  # Target: 25-40%
    
    # 5. Log results
    PRINT(f"{test}: {baseline_duration}s → {optimized_duration}s ({improvement}% faster)")
```

## DATA: Expected Results

### Performance Baselines (from docs/tests/performance_data)
```python
baseline_performance = {
    "test_interface_contracts": 79.57,  # seconds
    "test_basic_cli_api_integration": 62.41,
    "test_session_continuity": 61.20,
    "test_env_vars_propagation": 73.05
}
```

### Expected Improvements
```python
expected_performance = {
    "test_interface_contracts": {
        "baseline": 79.57,
        "optimized": ~50,  # 37% improvement
        "min_improvement": 25  # percent
    },
    "test_basic_cli_api_integration": {
        "baseline": 62.41,
        "optimized": ~45,  # 28% improvement
        "min_improvement": 25
    },
    "test_session_continuity": {
        "baseline": 61.20,
        "optimized": ~45,  # 26% improvement
        "min_improvement": 25
    }
}
```

### Success Criteria
```python
criteria = {
    "all_tests_pass": True,
    "performance_improvement": ">= 25%",
    "error_messages_helpful": True,
    "no_regressions": True
}
```

## Implementation Details

### Test Execution Commands

#### 1. Run Critical Path Tests (Primary Validation)
```bash
pytest tests/llm/providers/claude/test_claude_integration.py::TestCriticalPathIntegration \
    -v \
    --durations=0 \
    -m claude_api_integration
```

**Expected Output**:
```
tests/llm/providers/claude/test_claude_integration.py::TestCriticalPathIntegration::test_interface_contracts PASSED [~50s]
tests/llm/providers/claude/test_claude_integration.py::TestCriticalPathIntegration::test_basic_cli_api_integration PASSED [~45s]
tests/llm/providers/claude/test_claude_integration.py::TestCriticalPathIntegration::test_session_continuity PASSED [~45s]

=================== 3 passed in ~140s ===================
```

**Baseline Comparison**:
- Before: 79.57s + 62.41s + 61.20s = 203.18s total
- After: ~50s + ~45s + ~45s = ~140s total
- Improvement: ~31% faster

#### 2. Run All Claude Integration Tests
```bash
pytest tests/llm/providers/claude/ \
    -v \
    --durations=10 \
    -m "claude_cli_integration or claude_api_integration"
```

**Expected**: All tests pass, total runtime improves by ~45-60 seconds.

#### 3. Run Complete Claude Test Suite
```bash
pytest tests/llm/providers/claude/ -v --durations=10
```

**Expected**: 
- All unit tests pass (fast)
- All integration tests pass (faster than baseline)
- No test failures or regressions

### Error Scenario Testing

#### Test Case 1: Claude CLI Not Installed
```bash
# 1. Temporarily rename Claude CLI (backup first!)
# Windows: Rename C:\Users\<user>\.local\bin\claude.exe
# Linux/Mac: Rename ~/.local/bin/claude

# 2. Run a simple test
pytest tests/llm/providers/claude/test_claude_code_api.py::TestAskClaudeCodeApi::test_basic_question -v -s

# 3. Observe error message
# Expected: RuntimeError with helpful message about Claude CLI not found

# 4. Restore Claude CLI
```

**Expected Error Message**:
```
RuntimeError: Claude CLI verification failed: Claude Code CLI not found. 
Please ensure it's installed and accessible.
Install with: npm install -g @anthropic-ai/claude-code
Searched locations: [list of paths]
```

#### Test Case 2: Integration Test with Missing CLI
```python
# Create a temporary test to validate error handling
# File: tests/llm/providers/claude/test_error_handling_manual.py

import pytest
from unittest.mock import patch
from claude_code_sdk._errors import CLINotFoundError
from mcp_coder.llm.providers.claude.claude_code_api import ask_claude_code_api

@patch("mcp_coder.llm.providers.claude.claude_code_api.ClaudeCodeOptions")
@patch("mcp_coder.llm.providers.claude.claude_code_api._verify_claude_before_use")
def test_helpful_error_when_cli_missing(mock_verify, mock_options):
    """Verify error message is helpful when CLI is missing."""
    # Simulate SDK failure
    mock_options.side_effect = CLINotFoundError("Claude Code not found")
    
    # Simulate verification failure with helpful message
    mock_verify.return_value = (
        False,  # success
        None,   # path
        "Claude Code CLI not found. Please ensure it's installed and accessible.\n"
        "Install with: npm install -g @anthropic-ai/claude-code"
    )
    
    # Verify helpful error message
    with pytest.raises(RuntimeError) as exc_info:
        ask_claude_code_api("test question")
    
    error_msg = str(exc_info.value)
    assert "Claude CLI verification failed" in error_msg
    assert "npm install" in error_msg
    assert exc_info.value.__cause__ is not None  # Has original SDK error
```

### Performance Comparison Table

Create a comparison table to document improvements:

| Test Name | Baseline (s) | Optimized (s) | Improvement | Status |
|-----------|-------------|---------------|-------------|--------|
| test_interface_contracts | 79.57 | ~50 | ~37% | ✅ Pass |
| test_basic_cli_api_integration | 62.41 | ~45 | ~28% | ✅ Pass |
| test_session_continuity | 61.20 | ~45 | ~26% | ✅ Pass |
| test_env_vars_propagation | 73.05 | ~55 | ~25% | ✅ Pass |
| **Total Integration Time** | **276.23** | **~195** | **~29%** | ✅ |

### Validation Checklist

```markdown
## Integration Test Validation

- [ ] All critical path tests pass
- [ ] test_interface_contracts improved by ≥25%
- [ ] test_basic_cli_api_integration improved by ≥25%
- [ ] test_session_continuity improved by ≥25%
- [ ] Total integration test time improved by ≥25%

## Error Handling Validation

- [ ] Error message includes "Claude CLI verification failed"
- [ ] Error message includes installation instructions
- [ ] Error message includes searched paths
- [ ] Original SDK exception preserved as __cause__

## Regression Testing

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] No new test failures introduced
- [ ] Logging output is appropriate

## Code Quality

- [ ] Pylint check passes
- [ ] Mypy check passes
- [ ] All tests pass
```

## Results Documentation

### Create Performance Report
After running tests, document the results:

```markdown
# Performance Optimization Results

## Test Environment
- Date: [current date]
- Branch: [branch name]
- Python: [version]
- Claude SDK: [version]

## Performance Improvements

### Integration Tests (Claude API)
| Test | Before | After | Improvement |
|------|--------|-------|-------------|
| test_interface_contracts | 79.57s | 50.2s | 36.9% ✅ |
| test_basic_cli_api_integration | 62.41s | 45.3s | 27.4% ✅ |
| test_session_continuity | 61.20s | 45.8s | 25.2% ✅ |
| test_env_vars_propagation | 73.05s | 54.1s | 25.9% ✅ |

**Total**: 276.23s → 195.4s (29.2% improvement) ✅

### Overall Test Suite Impact
- Integration tests: ~45-60s faster
- Unit tests: No change (already fast)
- Total improvement: ~81 seconds saved

## Validation Results

✅ All tests pass  
✅ Performance improvement exceeds 25% target  
✅ Error messages remain helpful  
✅ No regressions detected  

## Error Handling Quality

Tested error scenario: Claude CLI not found
```
RuntimeError: Claude CLI verification failed: Claude Code CLI not found. 
Please ensure it's installed and accessible.
Install with: npm install -g @anthropic-ai/claude-code
Searched locations: [...]
```

✅ Error message is helpful and actionable  
✅ Original exception preserved as __cause__  
```

## Troubleshooting

### Issue: Tests Still Slow
**Symptom**: Integration tests don't show expected improvement  
**Possible Causes**:
1. Implementation not applied correctly
2. Tests are actually running with real API calls (external factors)
3. Network latency affecting results

**Resolution**:
1. Verify `_verify_claude_before_use()` is not called in happy path
2. Check logs for "SDK failed to find Claude CLI" (should not appear in success cases)
3. Run tests multiple times to average out network variance

### Issue: Tests Fail After Changes
**Symptom**: Integration tests fail with errors  
**Possible Causes**:
1. SDK import missing (`CLINotFoundError`)
2. Exception handling incorrect
3. Logic error in try-except block

**Resolution**:
1. Verify `from claude_code_sdk._errors import CLINotFoundError` is present
2. Check exception handling preserves original error as `__cause__`
3. Review Step 2 implementation carefully

### Issue: Error Messages Less Helpful
**Symptom**: Error messages don't include verification details  
**Possible Causes**:
1. Verification not called on SDK failure
2. Error message not including verification result
3. Exception chain broken

**Resolution**:
1. Ensure `_verify_claude_before_use()` is called in except block
2. Verify `raise RuntimeError(...) from e` preserves exception chain
3. Test manually with Claude CLI renamed

## Next Step

Proceed to **Step 4**: Update documentation to reflect the optimization (optional but recommended).
