# Step 3: Add Integration Tests for CLI Wrapper

## Goal
Create tests for the refactored `execute_prompt` function to verify it correctly maps argparse.Namespace parameters to the new `prompt_claude` function calls.

## WHERE
- **File**: `tests/cli/commands/test_prompt.py`
- **Section**: Add new test class `TestExecutePromptWrapper` 

## WHAT
Add test class to verify CLI wrapper functionality:

### Test Methods
```python
class TestExecutePromptWrapper:
    def test_execute_prompt_calls_prompt_claude_correctly(self) -> None
    def test_execute_prompt_with_default_args(self) -> None
    def test_execute_prompt_with_save_parameters(self) -> None
    def test_execute_prompt_parameter_mapping(self) -> None
```

## HOW
- **Integration**: Add to existing test file after save function tests
- **Mocking**: Mock `prompt_claude` function to verify it's called correctly
- **Assertions**: Verify parameter mapping from argparse.Namespace to function arguments

## ALGORITHM
```
1. Create argparse.Namespace with various parameter combinations
2. Mock prompt_claude function to capture calls
3. Call execute_prompt with test args
4. Verify prompt_claude called with correctly mapped parameters
5. Assert return value passed through correctly
```

## DATA

### Test Argparse.Namespace Examples
```python
# Full parameters
args = argparse.Namespace(
    prompt="Test prompt",
    verbosity="verbose",
    timeout=45,
    store_response=True,
    continue_from="test.json",
    save_conversation_md="test.md",
    save_conversation_full_json="test_full.json"
)

# Minimal parameters
args = argparse.Namespace(prompt="Simple test")
```

### Expected Function Calls
```python
# Full parameter mapping
prompt_claude(
    prompt="Test prompt",
    verbosity="verbose", 
    timeout=45,
    store_response=True,
    continue_from="test.json",
    continue_latest=False,  # from getattr(args, "continue", False)
    save_conversation_md="test.md",
    save_conversation_full_json="test_full.json"
)

# Default parameter mapping  
prompt_claude(
    prompt="Simple test",
    verbosity="just-text",  # default
    timeout=30,  # default
    store_response=False,  # default
    continue_from=None,  # default
    continue_latest=False,  # default
    save_conversation_md=None,  # default
    save_conversation_full_json=None  # default
)
```

### Return Value Verification
- **Success**: `execute_prompt` returns `0` when `prompt_claude` returns `0`
- **Error**: `execute_prompt` returns `1` when `prompt_claude` returns `1`

## Implementation Notes
- Tests verify parameter mapping without testing core logic
- Mock `prompt_claude` to isolate wrapper functionality
- Test both explicit and default parameter values
- Verify `getattr()` usage for optional parameters

## LLM Prompt for Implementation

```
Please implement Step 3 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Add tests for the CLI wrapper functionality to tests/cli/commands/test_prompt.py.

Create a test class TestExecutePromptWrapper with methods to verify that execute_prompt() correctly maps argparse.Namespace parameters to prompt_claude() function calls.

Test scenarios:
1. Full parameter mapping with all arguments provided
2. Default parameter handling when minimal args provided  
3. Correct handling of new save parameters (save_conversation_md, save_conversation_full_json)
4. Return value pass-through from prompt_claude to execute_prompt

Use @patch to mock prompt_claude and verify it's called with the correct parameters. Test both success and error return codes.

The execute_prompt function should use getattr() for optional parameters with appropriate defaults.
```
