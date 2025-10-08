# Step 2: Implementation - Lazy Verification in `_create_claude_client()`

## LLM Prompt for This Step

```
You are implementing Step 2 of the performance optimization project outlined in pr_info/steps/summary.md.

CONTEXT: Step 1 (TDD) is complete - unit tests now expect lazy verification. The SDK validates CLI availability, so we only verify on SDK failures to provide better error messages.

TASK: Modify _create_claude_client() in src/mcp_coder/llm/providers/claude/claude_code_api.py to implement lazy verification pattern - remove preemptive verification, add try-except around SDK client creation, verify only on CLINotFoundError.

GOAL: Make Step 1 tests pass by implementing the optimized behavior.

REFERENCE:
- Summary: pr_info/steps/summary.md
- Step 1 tests: pr_info/steps/step_1.md
- Current file: src/mcp_coder/llm/providers/claude/claude_code_api.py
- Target function: _create_claude_client() (lines 206-241)
```

## WHERE: File Location

**File**: `src/mcp_coder/llm/providers/claude/claude_code_api.py`  
**Function**: `_create_claude_client()` (lines 206-241)  
**Action**: MODIFY implementation (remove preemptive verification, add exception handling)

## WHAT: Function Changes Required

### Current Function Signature (no changes)
```python
def _create_claude_client(
    session_id: str | None = None, 
    env: dict[str, str] | None = None
) -> ClaudeCodeOptions:
```

### Current Behavior (to be changed)
```python
def _create_claude_client(...) -> ClaudeCodeOptions:
    logger.debug("Creating Claude Code SDK client")
    
    # ❌ REMOVE: Preemptive verification (15-30s overhead)
    success, claude_path, error_msg = _verify_claude_before_use()
    if not success:
        raise RuntimeError(f"Claude CLI verification failed: {error_msg}")
    
    logger.debug("Claude CLI verified successfully at: %s", claude_path)
    
    # Create SDK options
    if session_id:
        return ClaudeCodeOptions(resume=session_id, env=env or {})
    else:
        return ClaudeCodeOptions(env=env or {})
```

### New Behavior (to be implemented)
```python
def _create_claude_client(...) -> ClaudeCodeOptions:
    logger.debug("Creating Claude Code SDK client")
    
    try:
        # ✅ NEW: Try SDK first (SDK validates internally)
        if session_id:
            return ClaudeCodeOptions(resume=session_id, env=env or {})
        else:
            return ClaudeCodeOptions(env=env or {})
    
    except CLINotFoundError as e:
        # ✅ NEW: Only verify on SDK failure (for better diagnostics)
        logger.error("SDK failed to find Claude CLI: %s", e)
        success, claude_path, error_msg = _verify_claude_before_use()
        
        if not success:
            raise RuntimeError(f"Claude CLI verification failed: {error_msg}") from e
        
        # If verification passed but SDK still failed, re-raise original error
        raise
```

## HOW: Integration Points

### Imports (add CLINotFoundError)
```python
from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    UserMessage,
    query,
)
from claude_code_sdk._errors import CLINotFoundError  # ← ADD THIS
```

### Logging Integration
```python
logger = logging.getLogger(__name__)

# New log messages
logger.debug("Creating Claude Code SDK client")  # Existing
logger.error("SDK failed to find Claude CLI: %s", e)  # New
logger.debug("Claude CLI verified at: %s", claude_path)  # Modified (only on error path)
```

### Exception Handling
```python
try:
    # Attempt SDK client creation
    return ClaudeCodeOptions(...)
except CLINotFoundError as e:
    # Lazy verification for diagnostics
    success, path, error = _verify_claude_before_use()
    if not success:
        raise RuntimeError(f"...{error}") from e
    raise  # Re-raise if verification unexpectedly passed
```

## ALGORITHM: Core Logic Pseudocode

```python
def _create_claude_client(session_id=None, env=None):
    # 1. Log start
    LOG("Creating Claude Code SDK client")
    
    # 2. Try SDK first (optimistic execution)
    TRY:
        IF session_id:
            RETURN ClaudeCodeOptions(resume=session_id, env=env or {})
        ELSE:
            RETURN ClaudeCodeOptions(env=env or {})
    
    # 3. On SDK failure, verify for diagnostics
    CATCH CLINotFoundError as sdk_error:
        LOG_ERROR("SDK failed to find Claude CLI")
        success, path, error = _verify_claude_before_use()
        
        # 4. Raise helpful error with verification context
        IF NOT success:
            RAISE RuntimeError(f"Claude CLI verification failed: {error}") FROM sdk_error
        
        # 5. If verification passed but SDK failed, re-raise
        RAISE sdk_error  # Unexpected: verification passed but SDK failed
```

## DATA: Input/Output Specifications

### Input Parameters
```python
session_id: str | None = None
    # Optional Claude session ID to resume conversation
    # Example: "abc123-session-id"

env: dict[str, str] | None = None
    # Optional environment variables for Claude Code SDK
    # Example: {"MCP_CODER_PROJECT_DIR": "/path/to/project"}
```

### Return Value
```python
ClaudeCodeOptions
    # Configured SDK options object ready for use with query()
    # Contains: session_id, env vars, default settings
```

### Exception Types
```python
RuntimeError
    # Raised when: Claude CLI verification fails after SDK failure
    # Message format: "Claude CLI verification failed: {detailed_error}"
    # Has __cause__: Original CLINotFoundError from SDK

CLINotFoundError
    # Re-raised when: Verification passes but SDK still fails (edge case)
    # Indicates: Unexpected state, should rarely occur
```

## Implementation Details

### Complete New Implementation

```python
def _create_claude_client(
    session_id: str | None = None, env: dict[str, str] | None = None
) -> ClaudeCodeOptions:
    """Create a Claude Code SDK client with optional session resumption.

    Uses lazy verification: attempts SDK client creation first, only runs
    verification diagnostics if SDK raises CLINotFoundError.

    Args:
        session_id: Optional Claude session ID to resume conversation
        env: Optional environment variables to pass to Claude Code SDK

    Returns:
        ClaudeCodeOptions object configured for basic usage or session resumption

    Raises:
        RuntimeError: If Claude CLI cannot be found or verified
        CLINotFoundError: If SDK fails and verification unexpectedly passes

    Note:
        The SDK validates CLI availability internally. Verification only runs
        on failure to provide enhanced error diagnostics.
        
        Performance: 0-1s overhead (vs 15-30s with preemptive verification)
    """
    logger.debug("Creating Claude Code SDK client")

    try:
        # Attempt SDK client creation (SDK validates CLI internally)
        if session_id:
            logger.debug(f"Resuming session: {session_id}")
            return ClaudeCodeOptions(resume=session_id, env=env or {})
        else:
            return ClaudeCodeOptions(env=env or {})
    
    except CLINotFoundError as e:
        # SDK failed to find CLI - run verification for detailed diagnostics
        logger.error("SDK failed to find Claude CLI: %s", e)
        
        success, claude_path, error_msg = _verify_claude_before_use()
        
        if not success:
            logger.error("Claude verification failed: %s", error_msg)
            raise RuntimeError(f"Claude CLI verification failed: {error_msg}") from e
        
        # Edge case: verification passed but SDK failed
        # This shouldn't happen, but if it does, re-raise SDK error
        logger.warning(
            "Unexpected: verification succeeded at %s but SDK still failed",
            claude_path
        )
        raise
```

### Detailed Change Summary

**Lines to Remove** (~8 lines):
```python
# Remove these lines (212-220)
success, claude_path, error_msg = _verify_claude_before_use()

if not success:
    logger.error("Claude verification failed: %s", error_msg)
    raise RuntimeError(f"Claude CLI verification failed: {error_msg}")

logger.debug("Claude CLI verified successfully at: %s", claude_path)
```

**Lines to Add** (~15 lines):
```python
# Add try-except around ClaudeCodeOptions creation
try:
    # Existing options creation code
    if session_id:
        logger.debug(f"Resuming session: {session_id}")
        return ClaudeCodeOptions(resume=session_id, env=env or {})
    else:
        return ClaudeCodeOptions(env=env or {})

except CLINotFoundError as e:
    # New error handling with lazy verification
    logger.error("SDK failed to find Claude CLI: %s", e)
    success, claude_path, error_msg = _verify_claude_before_use()
    
    if not success:
        logger.error("Claude verification failed: %s", error_msg)
        raise RuntimeError(f"Claude CLI verification failed: {error_msg}") from e
    
    logger.warning(
        "Unexpected: verification succeeded at %s but SDK still failed",
        claude_path
    )
    raise
```

**Docstring Updates**:
```python
"""Create a Claude Code SDK client with optional session resumption.

Uses lazy verification: attempts SDK client creation first, only runs
verification diagnostics if SDK raises CLINotFoundError.

...

Note:
    The SDK validates CLI availability internally. Verification only runs
    on failure to provide enhanced error diagnostics.
    
    Performance: 0-1s overhead (vs 15-30s with preemptive verification)
"""
```

## Validation

### Step 1: Run Unit Tests
```bash
pytest tests/llm/providers/claude/test_claude_code_api.py::TestCreateClaudeClient -v
```

**Expected Result**: All 4 tests pass
```
✓ test_create_claude_client_basic
✓ test_create_claude_client_sdk_failure_triggers_verification
✓ test_create_claude_client_with_env
✓ test_create_claude_client_lazy_verification
```

### Step 2: Run Full Test File
```bash
pytest tests/llm/providers/claude/test_claude_code_api.py -v
```

**Expected Result**: All tests in file pass (no regressions)

### Step 3: Verify Logging Output
```bash
pytest tests/llm/providers/claude/test_claude_code_api.py::TestCreateClaudeClient -v -s --log-cli-level=DEBUG
```

**Expected Logs** (happy path):
```
DEBUG - Creating Claude Code SDK client
DEBUG - Resuming session: test-session-123
```

**Expected Logs** (error path):
```
DEBUG - Creating Claude Code SDK client
ERROR - SDK failed to find Claude CLI: Claude Code not found
ERROR - Claude verification failed: Claude CLI not found
```

## Code Quality Checks

### Complexity Analysis
- **Before**: Cyclomatic complexity = 3 (always verify + create)
- **After**: Cyclomatic complexity = 4 (try-except + conditional)
- **Change**: Minimal increase, acceptable for error handling

### Performance Analysis
- **Before**: Always 15-30s overhead
- **After**: 
  - Happy path: 0-1s overhead (SDK validation only)
  - Error path: 15-30s overhead (same as before)
- **Improvement**: 87-95% reduction in average overhead

### Error Message Quality
- **Before**: "Claude CLI verification failed: ..."
- **After**: "Claude CLI verification failed: ..." (same message)
- **Bonus**: Includes original SDK exception as `__cause__`

## Integration Impact

### Functions That Call `_create_claude_client()`
1. `_ask_claude_code_api_async()` - No changes needed
2. `ask_claude_code_api_detailed()` - No changes needed
3. `ask_claude_code_api_detailed_sync()` - No changes needed

All callers receive the same return type and exceptions - **100% backward compatible**.

### Performance Impact on Callers
- `ask_claude_code_api()`: 15-30s faster per call
- Integration tests: 25-40% faster overall
- Production API calls: 15-30s faster per request

## Next Step

Proceed to **Step 3**: Run integration tests and measure performance improvements.
