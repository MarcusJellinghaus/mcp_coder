# Issue #765: `/clear` should reset LLM session

## Summary

The `/clear` command in iCoder only clears the visual output log but does not reset the LLM session. After `/clear`, the next message continues the previous conversation (same `session_id`). This change makes `/clear` a true "fresh start" — both visually and conversationally.

## Architectural / Design Changes

### New `reset_session` flag on `Response` dataclass

`Response` gains a `reset_session: bool = False` field, following the existing flag pattern used by `clear_output`, `quit`, and `send_to_llm`. Command handlers declare *intent* via flags; `AppCore` acts on them. This keeps command handlers decoupled from services.

### New `reset_session()` method on `LLMService` protocol

The `LLMService` protocol gains a `reset_session() -> None` method. Both concrete implementations (`RealLLMService`, `FakeLLMService`) implement it by setting `self._session_id = None`. This is the only way to reset session state through the protocol boundary.

### `AppCore` as the central actor

`AppCore.handle_input()` inspects the `reset_session` flag after dispatching a command. When `True`, it calls `self._llm_service.reset_session()` and emits a `"session_reset"` event. This keeps session lifecycle management in `AppCore` (the central router), not in the UI layer or command handlers.

### No new files, no new abstractions

This is a 4-file change that extends existing patterns. No new modules, classes, or abstractions are introduced.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/icoder/core/types.py` | Add `reset_session: bool = False` to `Response` |
| `src/mcp_coder/icoder/services/llm_service.py` | Add `reset_session()` to protocol + both implementations |
| `src/mcp_coder/icoder/core/commands/clear.py` | Set `reset_session=True` in `/clear` handler |
| `src/mcp_coder/icoder/core/app_core.py` | Handle `reset_session` flag, call service, emit event |
| `tests/icoder/test_types.py` | Test `reset_session` field defaults and explicit value |
| `tests/icoder/test_llm_service.py` | Test `reset_session()` on both implementations |
| `tests/icoder/test_app_core.py` | Test `/clear` resets session and emits event |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Add `reset_session` field to `Response` + tests | `feat(icoder): add reset_session flag to Response dataclass` |
| 2 | Add `reset_session()` to `LLMService` protocol + implementations + tests | `feat(icoder): add reset_session() to LLMService protocol` |
| 3 | Wire `/clear` → `reset_session` flag + `AppCore` handling + tests | `feat(icoder): /clear resets LLM session (#765)` |
