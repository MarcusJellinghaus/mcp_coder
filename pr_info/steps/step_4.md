# Step 4: Update Interface Layer with Environment Variables

## Context
Read `pr_info/steps/summary.md` for full context. This step adds `env_vars` to public API functions.

## WHERE

**Modified files:**
- `src/mcp_coder/llm/interface.py`
- `src/mcp_coder/llm/providers/claude/claude_code_interface.py`
- `tests/llm/test_interface.py`
- `tests/llm/providers/claude/test_claude_code_interface.py`

## WHAT

### Updated Function Signatures

**In llm/interface.py:**
```python
def ask_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = LLM_DEFAULT_TIMEOUT_SECONDS,
    env_vars: dict[str, str] | None = None,  # NEW
) -> str:

def prompt_llm(
    question: str,
    provider: str = "claude",
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = LLM_DEFAULT_TIMEOUT_SECONDS,
    env_vars: dict[str, str] | None = None,  # NEW
) -> LLMResponseDict:
```

**In claude_code_interface.py:**
```python
def ask_claude_code(
    question: str,
    method: str = "cli",
    session_id: str | None = None,
    timeout: int = 30,
    env_vars: dict[str, str] | None = None,  # NEW
) -> str:
```

## HOW

**ask_llm() integration:**
```python
if provider == "claude":
    return ask_claude_code(
        question, method=method, session_id=session_id, timeout=timeout,
        env_vars=env_vars  # NEW
    )
```

**prompt_llm() integration:**
```python
if provider == "claude":
    if method == "cli":
        return ask_claude_code_cli(question, session_id=session_id, timeout=timeout,
                                   env_vars=env_vars)  # NEW
    elif method == "api":
        return ask_claude_code_api(question, session_id=session_id, timeout=timeout,
                                   env_vars=env_vars)  # NEW
```

**ask_claude_code() integration:**
```python
if method == "cli":
    result = ask_claude_code_cli(question, session_id=session_id, timeout=timeout,
                                 env_vars=env_vars)  # NEW
    return result["text"]
elif method == "api":
    result = ask_claude_code_api(question, session_id=session_id, timeout=timeout,
                                 env_vars=env_vars)  # NEW
    return result["text"]
```

## ALGORITHM

```
1. Accept env_vars parameter in all three functions
2. Thread env_vars to underlying provider functions
3. No logic changes - pure parameter passing
4. Maintain backward compatibility (env_vars=None)
```

## DATA

**No data structure changes** - same inputs/outputs as before, just with optional env_vars

## Test Coverage

**New tests:**
```python
def test_ask_llm_with_env_vars()
def test_prompt_llm_with_env_vars()
def test_ask_claude_code_with_env_vars()
```

**Extend existing:**
- Verify backward compatibility

## LLM Prompt

```
Context: Read pr_info/steps/summary.md and pr_info/steps/step_4.md

Task: Add env_vars parameter to interface layer (3 functions).

Changes:
1. Update ask_llm() in llm/interface.py - thread to ask_claude_code()
2. Update prompt_llm() in llm/interface.py - thread to CLI/API providers
3. Update ask_claude_code() in claude_code_interface.py - thread to CLI/API
4. Update docstrings

Tests:
1. Add 3 tests in tests/llm/test_interface.py
2. Add 1 test in tests/llm/providers/claude/test_claude_code_interface.py
3. Verify env_vars threaded correctly
4. Run tests

Follow TDD: Write tests first, then implementation.
```
