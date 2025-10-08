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

### 4. Add New Test: `test_create_claude_client_lazy_verification`
**New Test**: Verifies lazy verification behavior explicitly

**Function Signature**:
```python
def test_create_claude_client_lazy_verification(
    self, mock_options_class: MagicMock
) -> None:
    """Test that verification only runs when SDK raises CLINotFoundError."""
```

## HOW: Integration Points

### Imports (no changes needed)
```python
from unittest.mock import MagicMock, patch
from mcp_coder.llm.providers.claude.claude_code_api import _create_claude_client
from claude_code_sdk._errors import CLINotFoundError
```

### Mocking Strategy
```python
@patch("mcp_coder.llm.providers.claude.claude_code_api.ClaudeCodeOptions")
@patch("mcp_coder.llm.providers.claude.claude_code_api._verify_claude_before_use")
```

## ALGORITHM: Test Logic Pseudocode

### Test 1: Happy Path (No Verification)
```python
# GIVEN: SDK works fine (no exception)
mock_options_class.return_value = mock_options

# WHEN: Create client
result = _create_claude_client()

# THEN: 
#   - SDK options created
#   - Verification NOT called
#   - Returns options object
mock_options_class.assert_called_once_with(env={})
mock_verify.assert_not_called()  # ← KEY ASSERTION
assert result == mock_options
```

### Test 2: SDK Failure (Lazy Verification)
```python
# GIVEN: SDK raises CLINotFoundError
mock_options_class.side_effect = CLINotFoundError("CLI not found")
mock_verify.return_value = (False, None, "Detailed error")

# WHEN: Create client (expect exception)
with pytest.raises(RuntimeError, match="Detailed error"):
    _create_claude_client()

# THEN:
#   - SDK attempted first
#   - Verification called ONLY after SDK failure
#   - Helpful error message provided
mock_options_class.assert_called_once()
mock_verify.assert_called_once()  # ← Called for diagnostics
```

### Test 3: With Environment Variables
```python
# GIVEN: SDK works fine with env vars
env_vars = {"MCP_CODER_PROJECT_DIR": "/test/project"}
mock_options_class.return_value = mock_options

# WHEN: Create client with env
result = _create_claude_client(env=env_vars)

# THEN:
#   - SDK created with env vars
#   - Verification NOT called
mock_options_class.assert_called_once_with(env=env_vars)
mock_verify.assert_not_called()  # ← No preemptive verification
```

### Test 4: Explicit Lazy Verification Test
```python
# GIVEN: SDK works on first call, fails on second
mock_options_class.side_effect = [
    mock_options,  # First call: success
    CLINotFoundError("CLI not found")  # Second call: failure
]
mock_verify.return_value = (False, None, "CLI not found")

# WHEN: First call succeeds, second fails
result1 = _create_claude_client()
with pytest.raises(RuntimeError):
    _create_claude_client()

# THEN: Verification only called on second (failed) call
assert mock_verify.call_count == 1  # ← Only once, on failure
```

## DATA: Test Expectations

### Mock Return Values
```python
# Successful SDK creation
mock_options = MagicMock(spec=ClaudeCodeOptions)

# Verification result (only used on failure)
verification_result = (
    False,  # success: bool
    None,   # path: Optional[str]
    "Claude CLI verification failed: CLI not found"  # error: Optional[str]
)
```

### Expected Assertions
```python
# Happy path
mock_verify.assert_not_called()  # No verification in success case
mock_options_class.assert_called_once_with(env={})

# Error path  
mock_verify.assert_called_once()  # Verification only on SDK failure
# Error message includes verification details
with pytest.raises(RuntimeError, match="Claude CLI verification failed"):
```

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

### Test 4: Add New Lazy Verification Test

```python
@patch("mcp_coder.llm.providers.claude.claude_code_api.ClaudeCodeOptions")
@patch("mcp_coder.llm.providers.claude.claude_code_api._verify_claude_before_use")
def test_create_claude_client_lazy_verification(
    self, mock_verify: MagicMock, mock_options_class: MagicMock
) -> None:
    """Test that verification only runs when SDK raises CLINotFoundError."""
    # Setup - First call succeeds, second fails
    mock_options = MagicMock()
    mock_options_class.side_effect = [
        mock_options,  # First call: success
        CLINotFoundError("CLI not found")  # Second call: failure
    ]
    mock_verify.return_value = (False, None, "CLI not found in PATH")

    # Execute first call (success)
    result1 = _create_claude_client()
    assert result1 == mock_options
    assert mock_verify.call_count == 0  # No verification on success

    # Execute second call (failure)
    with pytest.raises(RuntimeError, match="CLI not found in PATH"):
        _create_claude_client()
    
    # Verify - verification called only once (on failure)
    assert mock_verify.call_count == 1
    mock_options_class.assert_has_calls([
        unittest.mock.call(env={}),
        unittest.mock.call(env={})
    ])
```

## Expected Test Results

### Before Implementation (Step 1 Complete)
```
tests/llm/providers/claude/test_claude_code_api.py::TestCreateClaudeClient
  ✗ test_create_claude_client_basic - FAILED (expects no verification)
  ✗ test_create_claude_client_sdk_failure_triggers_verification - FAILED (new behavior)
  ✗ test_create_claude_client_with_env - FAILED (expects no verification)
  ✗ test_create_claude_client_lazy_verification - FAILED (new test)
```

### After Implementation (Step 2 Complete)
```
tests/llm/providers/claude/test_claude_code_api.py::TestCreateClaudeClient
  ✓ test_create_claude_client_basic - PASSED
  ✓ test_create_claude_client_sdk_failure_triggers_verification - PASSED
  ✓ test_create_claude_client_with_env - PASSED
  ✓ test_create_claude_client_lazy_verification - PASSED
```

## Validation

Run tests to confirm they fail as expected:
```bash
pytest tests/llm/providers/claude/test_claude_code_api.py::TestCreateClaudeClient -v
```

Expected output: 4 failing tests (this is correct TDD - tests fail before implementation).

## Next Step

Proceed to **Step 2**: Implement lazy verification in `_create_claude_client()` to make these tests pass.
