# Step 1: Add Minimal Tests for Parameter Mapping

## Goal
Add minimal tests to verify the CLI wrapper correctly maps parameters from argparse.Namespace to the new `prompt_claude` function.

## WHERE
- **File**: `tests/cli/commands/test_prompt.py`
- **Section**: Add new test methods after existing `TestExecutePrompt` class

## WHAT
Add 2 test methods to verify parameter mapping:

### Test Methods
```python
def test_execute_prompt_calls_prompt_claude_with_correct_parameters(self) -> None
def test_execute_prompt_parameter_mapping_with_defaults(self) -> None
```

## HOW
- **Integration**: Add methods to existing test file  
- **Mocking**: Mock `prompt_claude` function to verify calls
- **Assertions**: Verify parameter mapping from argparse.Namespace to function arguments

## ALGORITHM
```
1. Create argparse.Namespace with test parameters
2. Mock prompt_claude function to capture calls
3. Call execute_prompt with test args
4. Verify prompt_claude called with correctly mapped parameters
5. Assert return value passed through correctly
```

## DATA

### Test Parameter Mapping
```python
# Test with full parameters
args = argparse.Namespace(
    prompt="Test prompt",
    verbosity="verbose", 
    timeout=45,
    store_response=True,
    continue_from="test.json",
    save_conversation_md="test.md",
    save_conversation_full_json="test_full.json"
)

# Expected function call
prompt_claude(
    prompt="Test prompt",
    verbosity="verbose",
    timeout=45, 
    store_response=True,
    continue_from="test.json",
    continue_latest=False,
    save_conversation_md="test.md",
    save_conversation_full_json="test_full.json"
)
```

## Implementation Notes
- Keep tests minimal since existing `TestExecutePrompt` covers business logic
- Focus only on parameter mapping verification
- Mock `prompt_claude` to isolate wrapper testing

## LLM Prompt for Implementation

```
Please implement Step 1 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Add 2 minimal test methods to tests/cli/commands/test_prompt.py to verify parameter mapping from execute_prompt to the new prompt_claude function.

Add these methods after the existing TestExecutePrompt class:

1. test_execute_prompt_calls_prompt_claude_with_correct_parameters() - Test full parameter mapping
2. test_execute_prompt_parameter_mapping_with_defaults() - Test default parameter handling

Use @patch to mock prompt_claude and verify it's called with the correct parameters mapped from argparse.Namespace.

The function signature to test against:
```python  
def prompt_claude(
    prompt: str,
    verbosity: str = "just-text",
    timeout: int = 30,
    store_response: bool = False,
    continue_from: Optional[str] = None,
    continue_latest: bool = False,
    save_conversation_md: Optional[str] = None,
    save_conversation_full_json: Optional[str] = None
) -> int
```

Keep tests minimal - existing TestExecutePrompt already covers business logic comprehensively.
```
