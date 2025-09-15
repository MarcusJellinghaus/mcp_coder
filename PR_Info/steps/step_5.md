# Step 5: Comprehensive Testing and Validation

## Objective
Verify that both CLI and API methods work with a simple integration test.

## WHERE
- `tests/test_integration_simple.py` (new) - Single simple integration test

## WHAT
### Main Test Function:
```python
# test_integration_simple.py
@pytest.mark.parametrize("method", ["cli", "api"])
def test_both_methods_work(method):
    response = ask_llm("What is 2+2? Just answer a number!", method=method)
    assert response is not None
    assert len(response) > 0
    # Verify both methods give the correct answer
    assert int(response.strip()) == 4
```

## HOW
### Simple Integration:
- One parameterized test that runs against both CLI and API methods
- Specific math question with clear instruction for numeric response
- Verify both methods return the correct answer (not just any response)

### Testing Patterns:
```python
@pytest.mark.parametrize("method", ["cli", "api"])
def test_both_methods(method):
    response = ask_llm("What is 2+2? Just answer a number!", method=method)
    assert int(response.strip()) == 4
```

## ALGORITHM
```pseudocode
1. Create single test file
2. Add one parameterized test function
3. Run test against both CLI and API
4. Verify both return the correct answer (4)
5. Done
```

## DATA
### Test Coverage:
- **Correctness Verification**: Both methods return the correct answer to a simple math problem
- **Functional Validation**: Ensure both implementations actually work, not just respond

### Metrics:
- Both methods return the correct numerical answer (4)
- Both methods can parse simple instructions ("Just answer a number!")

## Testing Strategy
- Keep it simple: one test, basic verification
- Use existing test infrastructure (pytest + parameterize)
- Mark as integration test if using real Claude Code calls

## LLM Prompt for Implementation
```
I need to implement Step 5 of the LLM interface refactoring plan. Please:

1. Read the summary from pr_info/steps/summary.md to understand what we've built
2. Create tests/test_integration_simple.py with one parameterized test
3. Test that both CLI and API methods can correctly answer "What is 2+2? Just answer a number!"
4. Verify both return exactly "4" (or parseable as int 4)
5. Run pylint and mypy checks
6. Prepare git commit

Focus on simple verification that both methods work - no complex testing needed.
```
