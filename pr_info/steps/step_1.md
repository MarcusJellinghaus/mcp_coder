# Step 1: Test-Driven Development - Update Unit Tests for Lazy Verification

## LLM Prompt for This Step

```
You are implementing Step 1 of the performance optimization project outlined in pr_info/steps/summary.md.

CONTEXT: We are removing redundant Claude CLI verification calls by implementing lazy verification. The SDK already validates CLI availability, so we only need to verify on SDK failures to provide better error messages.

TASK: Update unit tests in tests/llm/providers/claude/test_claude_code_api.py to expect lazy verification behavior (verification only called on SDK failure, not on every call).

FOLLOW: Test-Driven Development - update tests FIRST, then implementation in Step 2.

REFERENCE: 
- Summary: pr_info/steps/summary.md
- Current file: tests/llm/providers/claude/test_claude_code_api.py
- Target class: TestCreateClaudeClient (lines 31-91)
```

## WHERE: File Location

**File**: `tests/llm/providers/claude/test_claude_code_api.py`  
**Class**: `TestCreateClaudeClient` (lines 31-91)  
**Action**: MODIFY existing tests + ADD new test

## WHAT: Test Changes Required

### 1. Update Existing Test: `test_create_claude_client_basic`
**Current Behavior**: Expects `_verify_claude_before_use` to be called  
**New Behavior**: Should NOT expect verification in happy path

**Function Signature**:
```python
def test_create_claude_client_basic(self, mock_options_class: MagicMock) -> None:
    """Test that _create_claude_client creates basic options WITHOUT preemptive verification."""
```

### 2. Update Existing Test: `test_create_claude_client_verification_fails`
**Current Behavior**: Verification fails, raises RuntimeError  
**New Behavior**: SDK raises CLINotFoundError, then verification provides diagnostics

**Function Signature**:
```python
def test_create_claude_client_sdk_failure_triggers_verification(
    self, mock_options_class: MagicMock
) -> None:
    """Test that SDK failure triggers verification for diagnostics."""
```

### 3. Update Existing Test: `test_create_claude_client_with_env`
**Current Behavior**: Expects verification before creating options  
**New Behavior**: Should NOT expect verification in happy path

**Function Signature**:
```python
def test_create_claude_client_with_env(self, mock_options_class: MagicMock) -> None:
    """Test that _create_claude_client passes env WITHOUT preemptive verification."""
```



## Core Test Logic

```python
# Test 1: Happy Path - No verification in success case
mock_options_class.return_value = mock_options
result = _create_claude_client()
mock_verify.assert_not_called()  # Key assertion

# Test 2: SDK Failure - Verification only after failure
mock_options_class.side_effect = CLINotFoundError("CLI not found")
mock_verify.return_value = (False, None, "Detailed error")
with pytest.raises(RuntimeError):
    _create_claude_client()
mock_verify.assert_called_once()  # Called for diagnostics

# Test 3: With Environment - No verification in success case
env_vars = {"MCP_CODER_PROJECT_DIR": "/test/project"}
mock_options_class.return_value = mock_options
result = _create_claude_client(env=env_vars)
mock_verify.assert_not_called()
```

**Note:** Verify that test file structure matches code structure during implementation.

## Implementation Details

### Test 1: Update `test_create_claude_client_basic`

```python
@patch("mcp_coder.llm.providers.claude.claude_code_api.ClaudeCodeOptions")
@patch("mcp_coder.llm.providers.claude.claude_code_api._verify_claude_before_use")
def test_create_claude_client_basic(
    self, mock_verify: MagicMock, mock_options_class: MagicMock
) -> None:
    """Test that _create_claude_client creates basic options WITHOUT preemptive verification."""
    # Setup
    mock_options = MagicMock()
    mock_options_class.return_value = mock_options

    # Execute
    result = _create_claude_client()

    # Verify
    mock_verify.assert_not_called()  # ← Changed from assert_called_once
    mock_options_class.assert_called_once_with(env={})
    assert result == mock_options
```

### Test 2: Rename and Update Verification Failure Test

```python
@patch("mcp_coder.llm.providers.claude.claude_code_api.ClaudeCodeOptions")
@patch("mcp_coder.llm.providers.claude.claude_code_api._verify_claude_before_use")
def test_create_claude_client_sdk_failure_triggers_verification(
    self, mock_verify: MagicMock, mock_options_class: MagicMock
) -> None:
    """Test that SDK failure triggers verification for diagnostics."""
    # Setup - SDK raises CLINotFoundError
    mock_options_class.side_effect = CLINotFoundError("Claude Code not found")
    mock_verify.return_value = (False, None, "Claude CLI not found")

    # Execute & Verify
    with pytest.raises(RuntimeError, match="Claude CLI verification failed: Claude CLI not found"):
        _create_claude_client()

    mock_options_class.assert_called_once()
    mock_verify.assert_called_once()  # ← Called AFTER SDK failure
```

### Test 3: Update `test_create_claude_client_with_env`

```python
@patch("mcp_coder.llm.providers.claude.claude_code_api.ClaudeCodeOptions")
@patch("mcp_coder.llm.providers.claude.claude_code_api._verify_claude_before_use")
def test_create_claude_client_with_env(
    self, mock_verify: MagicMock, mock_options_class: MagicMock
) -> None:
    """Test that _create_claude_client passes env WITHOUT preemptive verification."""
    # Setup
    mock_options = MagicMock()
    mock_options_class.return_value = mock_options
    env_vars = {"MCP_CODER_PROJECT_DIR": "/test/project"}

    # Execute
    result = _create_claude_client(env=env_vars)

    # Verify
    mock_verify.assert_not_called()  # ← Changed from assert_called_once
    mock_options_class.assert_called_once_with(env=env_vars)
    assert result == mock_options
```



## Expected Test Results

### Before Implementation (Step 1 Complete)
```
tests/llm/providers/claude/test_claude_code_api.py::TestCreateClaudeClient
  ✗ test_create_claude_client_basic - FAILED (expects no verification)
  ✗ test_create_claude_client_sdk_failure_triggers_verification - FAILED (new behavior)
  ✗ test_create_claude_client_with_env - FAILED (expects no verification)
```

### After Implementation (Step 2 Complete)
```
tests/llm/providers/claude/test_claude_code_api.py::TestCreateClaudeClient
  ✓ test_create_claude_client_basic - PASSED
  ✓ test_create_claude_client_sdk_failure_triggers_verification - PASSED
  ✓ test_create_claude_client_with_env - PASSED
```

## Validation

Run tests to confirm they fail as expected:
```bash
pytest tests/llm/providers/claude/test_claude_code_api.py::TestCreateClaudeClient -v
```

Expected output: 4 failing tests (this is correct TDD - tests fail before implementation).

## Next Step

Proceed to **Step 2**: Implement lazy verification in `_create_claude_client()` to make these tests pass.
