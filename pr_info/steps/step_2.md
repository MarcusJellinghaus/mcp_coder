# Step 2 — Repoint non-stream error-path patches to `run_agent` (test-only)

> Read `pr_info/steps/summary.md` first. This step implements the **Non-stream (`run_agent`)
> leak — test-only** fix for the three error-path tests.

## Goal

Stop constructing an unawaited `run_agent` coroutine in the three non-stream error-path
tests by patching the async boundary function `run_agent` (as an `AsyncMock`) instead of
patching `asyncio.run`.

## WHERE

- File: `tests/llm/providers/langchain/test_langchain_provider.py`
- Import line (currently `from unittest.mock import MagicMock, patch`)
- Three tests:
  - `test_connection_error_raises_llm_connection_error` (~line 495) — `side_effect=ConnectionError(...)`
  - `test_non_connection_error_propagates` (~line 518) — `side_effect=RuntimeError(...)`
  - `test_auth_error_raises_llm_auth_error` (~line 553) — `side_effect=_FakeAuthError(...)`
- Module constant already present: `_MOD = "mcp_coder.llm.providers.langchain"`

## WHAT

Add `AsyncMock` to the mock import, and at each of the three sites change the patch target
and add `new_callable=AsyncMock`, keeping the existing `side_effect=` payload unchanged.

```python
from unittest.mock import AsyncMock, MagicMock, patch
```

```python
# before
patch(f"{_MOD}.asyncio.run", side_effect=ConnectionError("Connection refused"))
# after
patch(
    f"{_MOD}.agent.run_agent",
    new_callable=AsyncMock,
    side_effect=ConnectionError("Connection refused"),
)
```

Apply the identical transform to the `RuntimeError` and `_FakeAuthError` sites (payloads
unchanged). Leave every other patch in those `with` blocks untouched — including
`patch(f"{_MOD}.agent._check_agent_dependencies")` and, in the auth test,
`patch(f"{_MOD}.OPENAI_AUTH_ERRORS", (_FakeAuthError,))`.

## HOW (integration)

- Patch target must be `f"{_MOD}.agent.run_agent"` (source-module attribute), **not**
  `f"{_MOD}.run_agent"` — `_ask_agent` imports `run_agent` locally at call time, so only the
  source-module attribute is live. This mirrors the existing `{_MOD}.agent._check_agent_dependencies`
  patches in the same `with` blocks.
- `new_callable=AsyncMock` makes `patch` construct `AsyncMock(side_effect=...)`, so
  `run_agent` is now awaitable and no bare coroutine object is created.
- No `as` capture is needed for these three (they only assert the raised exception type).

## ALGORITHM

Not applicable — mechanical patch-target/kwarg edit; test bodies (the `pytest.raises`
assertions) are unchanged.

## DATA

- No data-structure changes. Each test still asserts the mapped exception is raised
  (`LLMConnectionError`, `RuntimeError`, `LLMAuthError`).

## LLM prompt

> Implement Step 2 as described in `pr_info/steps/step_2.md` (context in
> `pr_info/steps/summary.md`). In `tests/llm/providers/langchain/test_langchain_provider.py`,
> add `AsyncMock` to the `unittest.mock` import. In the three tests
> `test_connection_error_raises_llm_connection_error`, `test_non_connection_error_propagates`,
> and `test_auth_error_raises_llm_auth_error`, change the patch target from
> `f"{_MOD}.asyncio.run"` to `f"{_MOD}.agent.run_agent"` and add `new_callable=AsyncMock`,
> keeping each existing `side_effect=` argument and all other patches unchanged. Then run
> pylint, mypy, and the unit pytest subset (excluding integration markers, `-n auto`) and
> confirm all pass with no coroutine warnings from these tests. Use MCP tools only. Commit as
> one commit.
