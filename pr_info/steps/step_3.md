# Step 3 — Repoint + strengthen `test_agent_mode_passes_system_messages` (test-only)

> Read `pr_info/steps/summary.md` first. This step implements the **Non-stream (`run_agent`)
> leak — test-only** fix for the system-messages passthrough test, and strengthens its
> assertion.

## Goal

Remove the unawaited-coroutine leak in `test_agent_mode_passes_system_messages` by patching
`run_agent` as an `AsyncMock`, and make the test actually guard the passthrough its docstring
claims by asserting the `system_messages` argument content instead of only `.called`.

## WHERE

- File: `tests/llm/providers/langchain/test_langchain_provider_system_messages.py`
- Import line (currently `from unittest.mock import MagicMock, patch`)
- Test: `TestAskLangchainPassesSystemMessages.test_agent_mode_passes_system_messages` (~line 203)
- Module constant already present: `_MOD = "mcp_coder.llm.providers.langchain"`
- Reference: `_build_system_messages` (`__init__.py:64-68`) turns `system_prompt="sys"` +
  `project_prompt="proj"` into `[SystemMessage("sys"), SystemMessage("proj")]` in that order.

## WHAT

Add `AsyncMock` to the import, repoint the patch, and replace the weak assertion.

```python
from unittest.mock import AsyncMock, MagicMock, patch
```

```python
# before
patch(
    f"{_MOD}.asyncio.run",
    return_value=("response", [], {"agent_steps": 0, "total_tool_calls": 0}),
) as mock_run,
# after
patch(
    f"{_MOD}.agent.run_agent",
    new_callable=AsyncMock,
    return_value=("response", [], {"agent_steps": 0, "total_tool_calls": 0}),
) as mock_run,
```

```python
# before
assert mock_run.called
# after
mock_run.assert_called_once()
system_messages = mock_run.call_args.kwargs["system_messages"]
assert [m.content for m in system_messages] == ["sys", "proj"]
```

## HOW (integration)

- Patch target must be `f"{_MOD}.agent.run_agent"` (source-module attribute), **not**
  `f"{_MOD}.run_agent"` — same reason as Step 2.
- `new_callable=AsyncMock` + `as mock_run` returns the constructed `AsyncMock`, so the
  strengthened assertion reads `mock_run.call_args` directly.
- `run_agent` receives `system_messages` as a keyword argument in `_ask_agent`
  (`system_messages=system_messages`), so read it from `call_args.kwargs`.
- Keep the `ask_langchain(...)` call with `system_prompt="sys"`, `project_prompt="proj"`
  unchanged.

## ALGORITHM

```
patch run_agent as AsyncMock(return_value=("response", [], stats))
call ask_langchain(system_prompt="sys", project_prompt="proj")
assert run_agent called exactly once
msgs = run_agent.call_args.kwargs["system_messages"]
assert [m.content for m in msgs] == ["sys", "proj"]   # order + content guarded
```

## DATA

- `mock_run.call_args.kwargs["system_messages"]`: a 2-element list of `SystemMessage`
  objects; assertion checks their `.content` equals `["sys", "proj"]`.

## LLM prompt

> Implement Step 3 as described in `pr_info/steps/step_3.md` (context in
> `pr_info/steps/summary.md`). In
> `tests/llm/providers/langchain/test_langchain_provider_system_messages.py`, add `AsyncMock`
> to the `unittest.mock` import. In `test_agent_mode_passes_system_messages`, change the patch
> target from `f"{_MOD}.asyncio.run"` to `f"{_MOD}.agent.run_agent"`, add
> `new_callable=AsyncMock`, keep `return_value` and the `as mock_run` capture, and replace
> `assert mock_run.called` with `mock_run.assert_called_once()` plus an assertion that
> `mock_run.call_args.kwargs["system_messages"]` is a list whose element `.content` values
> equal `["sys", "proj"]`. Then run pylint, mypy, and the unit pytest subset (excluding
> integration markers, `-n auto`) and confirm all pass. Use MCP tools only. Commit as one
> commit.
