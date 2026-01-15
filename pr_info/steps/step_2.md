# Step 2: Remove Unnecessary Decorators + Fix LLM Logging

## LLM Prompt
```
Implement Step 2 of Issue #228 (see pr_info/steps/summary.md).
1. Remove @log_function_call from config helper functions to reduce verbosity
2. Remove env_vars and prompt content from LLM logging
Follow TDD: write tests first, then implement.
```

## Overview

Two changes to reduce log verbosity and remove sensitive data:
1. Remove `@log_function_call` from low-level config helpers
2. Remove `env_vars` and `prompt` content from LLM request logging

---

## Part A: Remove Decorators from Config Helpers

### WHERE

**File to modify**: `src/mcp_coder/utils/user_config.py`

### WHAT

Remove `@log_function_call` decorator from these functions:
- `get_config_file_path()` - Low-level helper, no logging needed
- `get_config_value()` - Called frequently, causes log spam

Keep `@log_function_call` on:
- `load_config()` - Higher-level, redaction handles secrets
- `create_default_config()` - Useful to log config creation

### HOW

Simply remove the decorator line:

**Before:**
```python
@log_function_call
def get_config_file_path() -> Path:
    ...

@log_function_call  
def get_config_value(section: str, key: str, ...) -> Optional[str]:
    ...
```

**After:**
```python
def get_config_file_path() -> Path:
    ...

def get_config_value(section: str, key: str, ...) -> Optional[str]:
    ...
```

### Impact

- **Before**: 6+ log lines per `get_config_value()` call
- **After**: 0 log lines per `get_config_value()` call (only `load_config()` logs once)

---

## Part B: Fix LLM Logging

### WHERE

**File to modify**: `src/mcp_coder/llm/providers/claude/logging_utils.py`

### WHAT

Modify `log_llm_request()` function to:
1. Remove `env_vars` from logged data entirely
2. Remove `prompt` content from logged data (keep only char count)

### HOW

**Before:**
```python
def log_llm_request(
    method: str,
    provider: str,
    session_id: str | None,
    prompt: str,
    timeout: int,
    env_vars: dict[str, str],
    cwd: str,
    command: list[str] | None = None,
    mcp_config: str | None = None,
) -> None:
    ...
    prompt_preview = f"{len(prompt)} chars"
    if len(prompt) > 250:
        prompt_preview += f" - {prompt[:250]}..."  # PROBLEM: logs prompt content
    else:
        prompt_preview += f" - {prompt}"  # PROBLEM: logs prompt content
    ...
    if env_vars:
        env_str = ", ".join(f"{k}={v}" for k, v in env_vars.items())  # PROBLEM
        log_lines.append(f"  env_vars: {env_str}")
```

**After:**
```python
def log_llm_request(
    method: str,
    provider: str,
    session_id: str | None,
    prompt: str,
    timeout: int,
    env_vars: dict[str, str],  # Keep param for API compatibility, but don't log
    cwd: str,
    command: list[str] | None = None,
    mcp_config: str | None = None,
) -> None:
    ...
    prompt_preview = f"{len(prompt)} chars"  # Only char count, no content
    ...
    # env_vars: removed from logging entirely
```

### ALGORITHM

```
function log_llm_request(...):
    prompt_preview = f"{len(prompt)} chars"  # NO content preview
    log_lines = [
        f"LLM Request (method={method}, provider={provider}, session={session_status})",
        f"  prompt: {prompt_preview}",
        f"  timeout: {timeout}s",
        f"  cwd: {cwd}",
        f"  mcp_config: {mcp_config}",
    ]
    if command: log_lines.insert(command info)
    # NO env_vars logging
    logger.debug(log_lines)
```

---

## Test Cases

### Part A Tests (in `tests/utils/test_user_config.py`)

No new tests needed - existing tests should still pass. The behavior is the same, just less logging.

### Part B Tests (in `tests/llm/providers/claude/test_logging_utils.py`)

1. `test_log_llm_request_does_not_log_env_vars` - Verify env_vars not in output
2. `test_log_llm_request_does_not_log_prompt_content` - Verify only char count logged

---

## DATA

### Log Output Before
```
LLM Request (method=cli, provider=claude, session=[new])
  prompt: 500 chars - You are an AI assistant. Here is a secret token: ghp_xxx...
  timeout: 300s
  cwd: /project
  mcp_config: .mcp.json
  env_vars: GITHUB_TOKEN=ghp_secret, API_KEY=sk-secret
```

### Log Output After
```
LLM Request (method=cli, provider=claude, session=[new])
  prompt: 500 chars
  timeout: 300s
  cwd: /project
  mcp_config: .mcp.json
```
