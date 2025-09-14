# Step 5: Comprehensive Testing and Validation

## Objective
Ensure the refactored architecture works correctly with comprehensive testing, performance validation, and backward compatibility verification.

## WHERE
- `tests/test_integration_full.py` (new) - Full integration tests
- `tests/test_performance.py` (new) - Performance comparison tests  
- `tests/test_backward_compatibility.py` (new) - Compatibility validation
- Update existing test files with additional edge cases

## WHAT
### Main Test Functions:
```python
# test_integration_full.py
def test_cli_vs_api_consistency()  # Compare CLI and API responses
def test_error_handling_parity()   # Ensure same error behavior
def test_timeout_behavior()        # Test timeout handling

# test_performance.py  
def test_response_time_comparison() # Benchmark CLI vs API
def test_memory_usage()            # Monitor resource usage

# test_backward_compatibility.py
def test_existing_imports_work()   # Verify old import paths
def test_function_signatures()     # Ensure API compatibility
```

## HOW
### Integration Points:
- Run same test cases against both CLI and API methods
- Use parameterized tests to test both implementations
- Mock external dependencies for unit tests
- Use real Claude Code for integration tests (with markers)

### Testing Patterns:
```python
@pytest.mark.parametrize("method", ["cli", "api"])
def test_both_methods(method):
    response = ask_llm("Test question", method=method)
    assert response is not None
```

## ALGORITHM
```pseudocode
1. Set up test environment with both CLI and API available
2. Run identical test cases against both implementations
3. Compare response quality and consistency
4. Measure and compare performance metrics
5. Validate all existing import paths still work
6. Verify error handling behavior is identical
```

## DATA
### Test Coverage:
- **Functional Tests**: Basic Q&A, timeout handling, error cases
- **Integration Tests**: Real Claude Code CLI and API calls
- **Performance Tests**: Response time, memory usage comparison
- **Compatibility Tests**: Import paths, function signatures

### Performance Metrics:
- Response time for equivalent queries
- Memory usage patterns
- Error recovery behavior
- Startup time differences

## Testing Strategy
- Aim for >95% code coverage on new modules
- Use both unit tests (mocked) and integration tests (real)
- Test error conditions and edge cases thoroughly
- Validate that refactoring didn't break existing functionality
- Performance tests to ensure no regression

## LLM Prompt for Implementation
```
I need to implement Step 5 of the LLM interface refactoring plan. Please:

1. Read the summary from pr_info/steps/summary.md to understand what we've built
2. Create comprehensive tests that validate both CLI and API methods work correctly
3. Add parameterized tests that run the same test cases against both implementations  
4. Create integration tests that verify real functionality (mark with @pytest.mark.integration)
5. Add backward compatibility tests to ensure existing code still works
6. Include performance comparison tests to verify no significant regression
7. Run the full test suite and ensure everything passes

Focus on thorough validation that the refactoring achieved its goals without breaking anything.
```
