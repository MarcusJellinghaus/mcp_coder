# Step 2: Add `reset_session()` to `LLMService` protocol + implementations

> **Context:** See `pr_info/steps/summary.md` for full issue context and architecture.

## Goal

Add a `reset_session()` method to the `LLMService` protocol and implement it in both `RealLLMService` and `FakeLLMService`. The method sets `session_id` to `None`, starting a fresh conversation on the next `stream()` call.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/icoder/services/llm_service.py` | Modify — add method to protocol + both classes |
| `tests/icoder/test_llm_service.py` | Modify — add tests |

## WHAT

### `LLMService` protocol

```python
def reset_session(self) -> None:
    """Reset session state to start a new conversation."""
```

### `RealLLMService` implementation

```python
def reset_session(self) -> None:
    self._session_id = None
```

### `FakeLLMService` implementation

```python
def reset_session(self) -> None:
    self._session_id = None
```

## HOW

- Method added to existing protocol — all implementations must have it.
- No new imports needed.
- `runtime_checkable` protocol already in place — `isinstance()` checks will cover the new method.

## ALGORITHM (pseudocode)

```
reset_session():
    self._session_id = None
```

## DATA

- Input: none
- Output: `None`
- Side effect: `session_id` property returns `None` after call

## Tests (TDD — write first)

### `test_llm_service.py` — add three tests:

1. **`test_fake_reset_session`** — Set session_id via a `done` event, call `reset_session()`, assert `session_id is None`.
2. **`test_real_reset_session`** — Create `RealLLMService`, set `_session_id` to a value via monkeypatch or stream, call `reset_session()`, assert `session_id is None`.
3. **`test_protocol_has_reset_session`** — Verify both implementations still satisfy `isinstance(service, LLMService)` (existing tests already do this, but confirm they still pass).

## Commit

```
feat(icoder): add reset_session() to LLMService protocol
```

## LLM Prompt

```
Implement Step 2 from pr_info/steps/step_2.md (see pr_info/steps/summary.md for context).

Add reset_session() method to LLMService protocol, RealLLMService, and FakeLLMService in llm_service.py.
Add tests in test_llm_service.py. Run all code quality checks. Commit when green.
```
