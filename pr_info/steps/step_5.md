# Step 5 — `LLMService.set_session_id()`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step
> (`pr_info/steps/step_5.md`) with strict TDD. Tests first, then code.
> Run pylint, pytest, mypy via the mandatory MCP tools. Single commit.

## WHERE

- Modify: `src/mcp_coder/icoder/services/llm_service.py`
- Update tests: `tests/icoder/test_llm_service.py`

## WHAT

```python
@runtime_checkable
class LLMService(Protocol):
    ...
    def set_session_id(self, session_id: str | None) -> None:
        """Replace the current session_id. None = fresh conversation."""

class RealLLMService:
    def set_session_id(self, session_id: str | None) -> None:
        self._session_id = session_id

class FakeLLMService:
    def set_session_id(self, session_id: str | None) -> None:
        self._session_id = session_id
```

## HOW

- One-line setter on each implementation, plus the Protocol declaration.
- `reset_session()` stays as-is (semantically: "set to None"). The new
  setter accepts any value, including `None`, so a future refactor
  could express `reset_session()` as `set_session_id(None)`, but **do
  not refactor in this step** — keep the change additive.

## ALGORITHM

N/A — trivial setters.

## DATA

No new types. Protocol method returns `None`.

## Test Cases

1. `RealLLMService(session_id="abc").set_session_id("xyz")` →
   `service.session_id == "xyz"`.
2. `FakeLLMService().set_session_id("abc")` →
   `service.session_id == "abc"`.
3. `set_session_id(None)` → `service.session_id is None` on both impls.
4. `isinstance(service, LLMService)` (runtime_checkable Protocol) holds
   for both impls — guards against forgetting to add the method to one
   of them.

## Out of Scope

- Mid-run usage (`/load`) — Step 10.
