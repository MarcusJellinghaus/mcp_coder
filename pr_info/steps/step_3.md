# Step 3: Update API Provider with Environment Variables

## Context
Read `pr_info/steps/summary.md` for full context. This step adds `env_vars` support to API provider.

## WHERE

**Modified files:**
- `src/mcp_coder/llm/providers/claude/claude_code_api.py`
- `tests/llm/providers/claude/test_claude_code_api.py`

## WHAT

### Updated Function Signatures

```python
def _create_claude_client(
    session_id: str | None = None,
    env: dict[str, str] | None = None  # NEW
) -> ClaudeCodeOptions:

def ask_claude_code_api(
    question: str,
    session_id: str | None = None,
    timeout: float = 30.0,
    env_vars: dict[str, str] | None = None,  # NEW
) -> LLMResponseDict:

async def ask_claude_code_api_detailed(
    question: str,
    timeout: float = 30.0,
    session_id: str | None = None,
    env_vars: dict[str, str] | None = None,  # NEW
) -> dict[str, Any]:

def ask_claude_code_api_detailed_sync(
    question: str,
    timeout: float = 30.0,
    session_id: str | None = None,
    env_vars: dict[str, str] | None = None,  # NEW
) -> dict[str, Any]:
```

## HOW

**Integration points:**

1. **_create_claude_client()** - Pass to ClaudeCodeOptions:
```python
if session_id:
    return ClaudeCodeOptions(resume=session_id, env=env or {})
return ClaudeCodeOptions(env=env or {})
```

2. **ask_claude_code_api()** - Pass to client:
```python
detailed = ask_claude_code_api_detailed_sync(question, timeout, session_id, env_vars)
```

3. **ask_claude_code_api_detailed()** - Pass to client:
```python
options = _create_claude_client(session_id, env=env_vars)
```

4. **ask_claude_code_api_detailed_sync()** - Pass to async:
```python
result = asyncio.run(ask_claude_code_api_detailed(question, timeout, session_id, env_vars))
```

## ALGORITHM

```
1. Update _create_claude_client to accept env parameter
2. Pass env to ClaudeCodeOptions(env=env or {})
3. Thread env_vars through all API functions
4. SDK handles environment variable propagation
```

## DATA

**Input:** Same as CLI - dict with MCP_CODER_* variables
**Output:** Same LLMResponseDict or detailed dict structure

## Test Coverage

**New tests:**
```python
def test_create_claude_client_with_env():
    """Test client creation with environment variables."""
    
def test_ask_claude_code_api_with_env_vars():
    """Test env_vars passed to SDK."""
    
def test_ask_claude_code_api_detailed_with_env_vars():
    """Test detailed API with env_vars."""
```

**Extend existing tests:**
- Verify backward compatibility with `env_vars=None`

## LLM Prompt

```
Context: Read pr_info/steps/summary.md and pr_info/steps/step_3.md

Task: Add env_vars parameter to API provider (4 functions).

Changes:
1. Update _create_claude_client(session_id, env) - pass env to ClaudeCodeOptions
2. Update ask_claude_code_api() - thread env_vars to detailed_sync
3. Update ask_claude_code_api_detailed() - pass env_vars to _create_claude_client
4. Update ask_claude_code_api_detailed_sync() - thread env_vars to async version
5. Update docstrings

Tests:
1. Add 3 new tests in tests/llm/providers/claude/test_claude_code_api.py
2. Verify env_vars passed to ClaudeCodeOptions
3. Run tests

Follow TDD: Write tests first, then implementation.
```
