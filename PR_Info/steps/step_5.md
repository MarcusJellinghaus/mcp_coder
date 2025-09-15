# Step 5: Comprehensive Testing and Validation

## Objective
Ensure the refactored architecture works correctly with comprehensive testing and validation that both CLI and API methods function identically.

## WHERE
- `tests/test_integration_full.py` (new) - Essential integration tests
- Update existing test files with additional edge cases

## WHAT
### Main Test Functions:
```python
# test_integration_full.py
def test_cli_vs_api_basic_functionality()  # Both methods work identically
def test_error_handling_differences()      # Document different error types
def test_timeout_behavior()               # Test timeout handling for both methods
def test_response_consistency()           # Ensure responses are equivalent
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
5. Verify both methods produce consistent results
6. Document acceptable differences in error handling
```

## DATA
### Test Coverage:
- **Functional Tests**: Basic Q&A, timeout handling, error cases
- **Integration Tests**: Real Claude Code CLI and API calls
- **Consistency Tests**: Verify CLI and API produce equivalent results
- **Edge Case Tests**: Error conditions, timeouts, malformed inputs

### Performance Metrics:
- Response time for equivalent queries
- Memory usage patterns
- Error recovery behavior
- Startup time differences

## Testing Strategy
- Focus on essential functionality and error handling
- Use both unit tests (mocked) and integration tests (real)
- Test error conditions and edge cases thoroughly
- Validate that both CLI and API methods work identically
- Document acceptable differences in error signatures between methods

## LLM Prompt for Implementation
```
I need to implement Step 5 of the LLM interface refactoring plan. Please:

1. Read the summary from pr_info/steps/summary.md to understand what we've built
2. Create essential tests that validate both CLI and API methods work identically
3. Add parameterized tests that run the same test cases against both implementations  
4. Create integration tests that verify real functionality (mark with @pytest.mark.integration)
5. Document that different error signatures between methods are acceptable
6. Add edge case testing to existing test files
7. Run the test suite and ensure core functionality passes

Focus on validating that CLI and API methods produce equivalent results and handle errors appropriately.
```
