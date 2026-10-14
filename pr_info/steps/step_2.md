# Step 2 — Shared scripted `BaseChatModel` test double

Read `pr_info/steps/summary.md` first for overall context and the rationale
for the module's location.

Part of issue #1171. Consolidates 4 near-identical `BaseChatModel` test
doubles (`_FakeChatModel` in `approval_harness.py`; `_TwoCallModel` and
`_LoopingModel` in `test_approval_integration.py`; `_ScriptedModel` in
`test_icoder_permission_wiring.py`) into one factory, and replaces their
`_generate`/`_agenerate` overrides' untyped params (the source of 10 of the
64 `ANN001`/`ANN003`/`ANN202` findings) with the real `langchain_core`
signature, removing the stale `# type: ignore[no-untyped-def]` comments.

## Precondition check

Run `mcp__mcp-tools-py__run_ruff_check` with
`select=["ANN001","ANN002","ANN003","ANN201","ANN202","ANN204"]`,
`max_issues=10`. If it does not report exactly 4 `_generate`/`_agenerate`
pairs at `tests/llm/providers/langchain/approval_harness.py`,
`tests/llm/providers/langchain/test_approval_integration.py` (x2), and
`tests/icoder/test_icoder_permission_wiring.py`, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- New: `tests/langchain_doubles.py`
- New: `tests/test_langchain_doubles.py`
- Modify: `tests/llm/providers/langchain/approval_harness.py`
- Modify: `tests/llm/providers/langchain/test_approval_integration.py`
- Modify: `tests/icoder/test_icoder_permission_wiring.py`

`tests/langchain_doubles.py` sits at the top level of `tests/`, a sibling of
`tests/conftest.py` — **not** under `tests.llm` or `tests.icoder` or
`tests.utils`. `.importlinter`'s `test_module_independence` contract lists
`tests.llm` and `tests.icoder` as mutually independent; a module outside
every listed package lets both sides import it with no `.importlinter` edit.

## WHAT

`tests/langchain_doubles.py`:

```python
def make_scripted_chat_model(
    next_message: Callable[[int], Any],
    llm_type: str,
) -> Any:
    """Build a BaseChatModel test double driven by *next_message*.

    *next_message* receives the 1-based invoke count and returns the
    AIMessage for that invoke. Callers decide via its logic when (or
    whether) to stop returning tool calls.

    The caller must already have confirmed langchain_core is importable
    (e.g. via `pytest.importorskip`) before calling this.
    """
```

Internally defines and returns an instance of one locally-scoped
`_ScriptedChatModel(BaseChatModel)` class (same reason the current code
defines classes inside functions: keeps `langchain_core` imports — and the
`BaseChatModel` subclass — out of module scope, so collection doesn't fail
when the package isn't installed, and so the mypy job that runs without the
`langchain` extra doesn't trip `disallow_subclassing_any`).

## HOW

`tests/langchain_doubles.py` module structure:

```python
from __future__ import annotations

from collections.abc import Callable
from typing import Any


def make_scripted_chat_model(next_message: Callable[[int], Any], llm_type: str) -> Any:
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import BaseMessage
    from langchain_core.callbacks import (
        AsyncCallbackManagerForLLMRun,
        CallbackManagerForLLMRun,
    )
    from langchain_core.outputs import ChatGeneration, ChatResult

    class _ScriptedChatModel(BaseChatModel):  # type: ignore[misc]
        invoke_count: int = 0

        def bind_tools(self, tools: Any, **kw: Any) -> "_ScriptedChatModel":
            return self

        def _generate(
            self,
            messages: list[BaseMessage],
            stop: list[str] | None = None,
            run_manager: CallbackManagerForLLMRun | None = None,
            **kwargs: Any,
        ) -> ChatResult:
            raise NotImplementedError("scripted model implements _agenerate")

        async def _agenerate(
            self,
            messages: list[BaseMessage],
            stop: list[str] | None = None,
            run_manager: AsyncCallbackManagerForLLMRun | None = None,
            **kwargs: Any,
        ) -> ChatResult:
            self.invoke_count += 1
            message = next_message(self.invoke_count)
            return ChatResult(generations=[ChatGeneration(message=message)])

        @property
        def _llm_type(self) -> str:
            return llm_type

    return _ScriptedChatModel()
```

Migration at each existing call site — replace the local class with a call
to the factory, keeping each site's own `require_real_langchain` /
`pytest.importorskip` guard exactly as today (that guard does NOT move into
the shared module — `tests/icoder/conftest.py` has no mock-injection, so the
icoder call site never needed `require_real_langchain`'s extra Mock check,
and should keep not needing it):

- `approval_harness.py::make_fake_chat_model()` — body becomes:
  ```python
  from langchain_core.messages import AIMessage

  def _next(n: int) -> AIMessage:
      if n == 1:
          return AIMessage(content="", tool_calls=[{"name": TOOL_NAME, "args": {}, "id": "call_1"}])
      return AIMessage(content="done")

  return make_scripted_chat_model(_next, llm_type="fake-approval")
  ```
  Add `from tests.langchain_doubles import make_scripted_chat_model` at module
  level (safe: this import has no langchain dependency itself).

- `test_approval_integration.py`'s two-call-model builder — same shape, but
  `_next` returns both tool calls (`TOOL_NAME` and `_UNGATED`) on invoke 1,
  `llm_type="fake-approval-two-call"`.

- `test_approval_integration.py`'s `_make_looping_model(tool_name)` — `_next`
  always returns one tool call for `tool_name` with
  `id=f"call_{n}"`, never "done"; `llm_type="fake-approval-looping"`.

- `test_icoder_permission_wiring.py`'s inline `_ScriptedModel` — `_next`
  returns the `"do_it"` tool call on invoke 1, `AIMessage("done")` after;
  `llm_type="fake-approval"` (match whatever string the existing
  `_llm_type` returns — check before changing).

Remove the now-dead `BaseChatModel`/`ChatGeneration`/`ChatResult` imports and
the `# type: ignore[misc]`/`# type: ignore[no-untyped-def]` comments at each
migrated call site (the factory owns them now); keep each site's own
`AIMessage` import since the `_next` closures still construct messages.

## ALGORITHM

```
make_scripted_chat_model(next_message, llm_type):
    define _ScriptedChatModel(BaseChatModel) locally
    _agenerate: increment invoke_count, call next_message(invoke_count),
                wrap result in ChatResult/ChatGeneration
    _generate: raise NotImplementedError (async-only double)
    _llm_type: return llm_type
    return an instance
```

## DATA

Return type: `Any` (the real type is a dynamically-defined `BaseChatModel`
subclass; `Any` is correct here per the `ANN401` exclusion rationale — same
as the current `make_fake_chat_model() -> Any`).

## TDD

Write `tests/test_langchain_doubles.py` first:

```python
import asyncio

import pytest

from tests.langchain_doubles import make_scripted_chat_model


def test_scripted_model_tool_call_then_done() -> None:
    pytest.importorskip("langchain_core")
    from langchain_core.messages import AIMessage

    def next_message(n: int) -> AIMessage:
        if n == 1:
            return AIMessage(content="", tool_calls=[{"name": "ping", "args": {}, "id": "call_1"}])
        return AIMessage(content="done")

    model = make_scripted_chat_model(next_message, llm_type="test-scripted")

    assert model._llm_type == "test-scripted"
    assert model.bind_tools([]) is model
    with pytest.raises(NotImplementedError):
        model._generate(messages=[])

    first = asyncio.run(model._agenerate(messages=[]))
    assert first.generations[0].message.tool_calls[0]["name"] == "ping"

    second = asyncio.run(model._agenerate(messages=[]))
    assert second.generations[0].message.content == "done"
```

Then implement `tests/langchain_doubles.py` to make it pass, then migrate
the 4 call sites.

## Verification

- `mcp__mcp-tools-py__run_pytest_check` targeting
  `tests/test_langchain_doubles.py` first, then the full fast suite:
  `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
  — if `langchain_core` isn't installed in this environment, the new test
  and the migrated call sites must all skip cleanly, not error.
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_lint_imports_check` (confirm no new violation —
  none expected, since the new module is outside every contract-listed
  package)
- `mcp__mcp-tools-py__run_format_code`, then commit.

## Commit

One commit:
`refactor(tests): consolidate scripted BaseChatModel doubles into shared factory`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement
> step 2 exactly as specified: write the test first
> (`tests/test_langchain_doubles.py`), then `tests/langchain_doubles.py`,
> then migrate the 4 call sites in `approval_harness.py`,
> `test_approval_integration.py` (x2), and `test_icoder_permission_wiring.py`
> to use the shared factory, removing the stale `# type: ignore` comments.
> Run the verification commands listed in the step, fix anything they
> report, then run `run_format_code` and commit with the given message. If
> the precondition check fails, write one line to `pr_info/.blocked.txt` and
> stop.
