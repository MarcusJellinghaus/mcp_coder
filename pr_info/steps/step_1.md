# Step 1: `--timeout` CLI flag + `RealLLMService` timeout parameter

> **Context**: See [summary.md](summary.md) for full issue context.

## Goal
Make the iCoder inactivity timeout configurable via `--timeout` CLI flag, plumbed through `RealLLMService` to the existing `prompt_llm_stream(timeout=...)` parameter.

## Files Modified

| File | Change |
|------|--------|
| `tests/icoder/test_llm_service.py` | Add test for custom timeout, update existing timeout test |
| `tests/cli/test_parsers.py` | Add test for `--timeout` argument parsing (if icoder parser tests exist) |
| `src/mcp_coder/icoder/services/llm_service.py` | Add `timeout` param to `RealLLMService.__init__()` |
| `src/mcp_coder/cli/parsers.py` | Add `--timeout` argument to `add_icoder_parser()` |
| `src/mcp_coder/cli/commands/icoder.py` | Pass `args.timeout` to `RealLLMService` |

## Implementation Details

### 1. Tests first: `tests/icoder/test_llm_service.py`

**Add** `test_real_llm_service_custom_timeout`:
```python
def test_real_llm_service_custom_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """RealLLMService passes custom timeout to prompt_llm_stream."""
    captured_kwargs: dict[str, object] = {}
    fake_events: list[StreamEvent] = [{"type": "done"}]

    def mock_stream(question: str, **kwargs: object) -> Iterator[StreamEvent]:
        captured_kwargs.update(kwargs)
        yield from fake_events

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream",
        mock_stream,
    )
    service = RealLLMService(provider="claude", timeout=600)
    list(service.stream("hello"))
    assert captured_kwargs["timeout"] == 600
```

**Verify** existing `test_real_llm_service_passes_timeout` still passes (it uses `RealLLMService(provider="claude")` with no timeout — should get default 300).

### 2. Source: `src/mcp_coder/icoder/services/llm_service.py`

**WHERE**: `RealLLMService.__init__()` at line 35

**WHAT**: Add `timeout` parameter with default `ICODER_LLM_TIMEOUT_SECONDS`

**Signature change**:
```python
def __init__(
    self,
    provider: str = "claude",
    session_id: str | None = None,
    execution_dir: str | None = None,
    mcp_config: str | None = None,
    env_vars: dict[str, str] | None = None,
    timeout: int = ICODER_LLM_TIMEOUT_SECONDS,  # NEW
) -> None:
```

**Store** as `self._timeout = timeout` and use `timeout=self._timeout` in `stream()` instead of `timeout=ICODER_LLM_TIMEOUT_SECONDS`.

### 3. Source: `src/mcp_coder/cli/parsers.py`

**WHERE**: Inside `add_icoder_parser()`, after the `--execution-dir` argument (around line 485)

**WHAT**: Add one argument:
```python
icoder_parser.add_argument(
    "--timeout",
    type=int,
    default=300,
    metavar="SECONDS",
    help="LLM inactivity timeout in seconds — max silence before cancelling (default: 300)",
)
```

No custom validator needed — `type=int` handles non-integers, and `prompt_llm_stream` already validates `timeout > 0`.

### 4. Source: `src/mcp_coder/cli/commands/icoder.py`

**WHERE**: `execute_icoder()`, where `RealLLMService` is constructed (around line 92)

**WHAT**: Pass `timeout=args.timeout`:
```python
llm_service = RealLLMService(
    provider=provider,
    session_id=session_id,
    execution_dir=str(execution_dir),
    mcp_config=mcp_config,
    env_vars=env_vars,
    timeout=args.timeout,  # NEW
)
```

## LLM Prompt

```
Implement Step 1 from pr_info/steps/step_1.md.
Read pr_info/steps/summary.md for context.

This step adds a --timeout CLI flag for iCoder and plumbs it through RealLLMService.
Write tests first, then implement. Run all checks after.
```
