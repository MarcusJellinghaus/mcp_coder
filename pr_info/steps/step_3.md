# Step 3: LLM Service Timeout Constant + Agent Timeout Passthrough

> **Reference:** See `pr_info/steps/summary.md` for full context.

## Goal

Define `ICODER_LLM_TIMEOUT_SECONDS = 300` in the LLM service and pass it through
to `prompt_llm_stream()`. Align the LangChain agent streaming path to use the
caller's timeout instead of the hardcoded `_AGENT_NO_PROGRESS_TIMEOUT` constant.

## WHERE

- **Modify:** `src/mcp_coder/icoder/services/llm_service.py`
- **Modify:** `src/mcp_coder/llm/providers/langchain/__init__.py` — `_ask_agent_stream()`
- **Modify:** `tests/icoder/test_llm_service.py` (add timeout tests to existing file)

## WHAT

### `llm_service.py` — Add constant + pass timeout

```python
ICODER_LLM_TIMEOUT_SECONDS = 300  # 5-minute inactivity timeout for interactive use

class RealLLMService:
    def stream(self, question: str) -> Iterator[StreamEvent]:
        for event in prompt_llm_stream(
            question,
            provider=self._provider,
            session_id=self._session_id,
            timeout=ICODER_LLM_TIMEOUT_SECONDS,  # NEW — was missing (defaulted to 30)
            execution_dir=self._execution_dir,
            mcp_config=self._mcp_config,
            env_vars=self._env_vars,
        ):
            ...
```

### `langchain/__init__.py` — Agent timeout passthrough

In `_ask_agent_stream()`, replace the hardcoded `_AGENT_NO_PROGRESS_TIMEOUT` in
`q.get(timeout=...)` with the `timeout` parameter:

```python
# BEFORE:
event = q.get(timeout=_AGENT_NO_PROGRESS_TIMEOUT)

# AFTER:
event = q.get(timeout=timeout)
```

Also update the error message to reference the actual timeout value.

Remove `_AGENT_NO_PROGRESS_TIMEOUT` constant (now unused). Keep `_AGENT_OVERALL_TIMEOUT`
(still used for overall elapsed check).

Also raise the default `timeout` parameter in `ask_langchain_stream()` from 30s to
**600s** to preserve backward compatibility for non-icoder callers (matching the old
`_AGENT_NO_PROGRESS_TIMEOUT` value). iCoder's `RealLLMService` still passes
`ICODER_LLM_TIMEOUT_SECONDS = 300` explicitly.

### `test_llm_service.py` — Add tests to existing file

New tests (append to `tests/icoder/test_llm_service.py`):

1. **`test_real_llm_service_passes_timeout`**: Mock `prompt_llm_stream` and verify
   it's called with `timeout=ICODER_LLM_TIMEOUT_SECONDS` (300). Similar pattern to
   the existing `test_real_service_delegates_to_prompt_llm_stream` test.

2. **`test_icoder_timeout_constant_value`**: Assert `ICODER_LLM_TIMEOUT_SECONDS == 300`.

## HOW

- `unittest.mock.patch("mcp_coder.icoder.services.llm_service.prompt_llm_stream")`
  to intercept and inspect the call kwargs.
- The mock returns an iterator with a single `{"type": "done"}` event.

## ALGORITHM

No algorithm — this is wiring (add one kwarg, replace one constant reference).

## DATA

- `ICODER_LLM_TIMEOUT_SECONDS: int = 300` — module-level constant
- No changes to `StreamEvent`, `LLMService` protocol, or `RealLLMService` constructor

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for full context.

Implement step 3: Add ICODER_LLM_TIMEOUT_SECONDS constant in llm_service.py and pass
it to prompt_llm_stream(). In langchain/__init__.py _ask_agent_stream(), replace
_AGENT_NO_PROGRESS_TIMEOUT with the timeout parameter in q.get(). Write tests first
in tests/icoder/test_llm_service.py, then implement. Run all three MCP code quality
checks after changes. Commit message: "icoder: 5-minute inactivity timeout for LLM
calls"
```
