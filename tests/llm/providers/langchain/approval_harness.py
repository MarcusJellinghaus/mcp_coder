"""Shared, typed fixtures for the in-band approval tests (#1045).

Deliberately **not** named ``test_*``: pytest does not collect this module. It
holds one copy each of the three pieces every approval test in this directory
needs, so Steps 3, 7 and 11 do not grow three divergent fakes:

* :func:`make_fake_chat_model` — a scripted ``BaseChatModel`` that asks for one
  tool call and then answers with plain text;
* :class:`Gate` + :func:`make_blocking_tool` — a per-run cross-thread handoff
  and a tool coroutine that parks on it, which is how a test stands in for "an
  approval is pending on the agent loop";
* :func:`wait_for` — polling with a deadline, so no test sleeps blindly.

It lives under ``tests/llm/providers/langchain/`` on purpose. ``.importlinter``'s
``test_module_independence`` contract forbids ``tests.icoder`` <-> ``tests.llm``
imports, and this directory's ``conftest.py`` already redirects ``Path.home()``
to ``tmp_path`` for every non-integration test, which is what keeps
``run_agent_stream``'s unconditional session-history write out of the
developer's real home directory.

**Every** ``pytest.importorskip`` and every langchain import lives *inside* a
function, and ``BaseChatModel`` is subclassed inside one too. Two CI jobs make
the obvious module-scope version wrong:

* ``isort --check --profile=black --float-to-top`` floats imports above
  module-level statements, so a module-level ``importorskip`` would end up
  *below* the langchain import it was meant to guard and would guard nothing;
* the mypy job installs only ``.[typecheck]``, so ``BaseChatModel`` resolves to
  ``Any`` and a module-scope subclass trips ``disallow_subclassing_any`` under
  ``--strict`` — hence the ``# type: ignore[misc]`` on the class line.

``importorskip`` rather than a plain import, because this directory's conftest
injects ``MagicMock`` modules when langchain is genuinely absent and these
fixtures need the **real** packages. Precedent for the whole shape:
``tests/icoder/test_icoder_permission_wiring.py``.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from unittest.mock import Mock

import pytest

#: The tool name the fake model asks for, and the default blocking-tool name.
TOOL_NAME = "ping"


def require_real_langchain(*packages: str) -> None:
    """Skip the calling test unless *packages* are importable **for real**.

    ``pytest.importorskip`` alone is not sufficient in this directory. Its
    ``conftest.py`` installs ``MagicMock`` entries in ``sys.modules`` for every
    langchain package that is genuinely absent, and ``importorskip`` resolves
    through ``sys.modules`` — so on a base install it hands back the mock and
    the test proceeds against a fake ``BaseChatModel``, failing with a confusing
    ``AttributeError`` instead of skipping. The mock check below is what turns
    that into a clean skip.

    Args:
        *packages: Top-level package names, e.g. ``"langchain_core"``.
    """
    for name in packages:
        module = pytest.importorskip(name)
        if isinstance(module, Mock):
            pytest.skip(
                f"{name} is mocked by conftest: the real package is not installed"
            )


def make_fake_chat_model() -> Any:
    """Build a two-invoke fake chat model: one tool call, then the text ``done``.

    Invoke 1 returns an ``AIMessage`` carrying a single ``ping`` tool call with
    ``args={}``; every later invoke returns ``AIMessage("done")``. ``args`` must
    satisfy the tool schema or ``ToolNode`` rejects the call *before* the tool
    coroutine runs — which is why the blocking tool takes no arguments.

    Only the **async** ``_agenerate`` is implemented. ``BaseChatModel``'s
    default ``_agenerate`` delegates to ``run_in_executor``, i.e. a thread-pool
    thread with no running loop, where ``asyncio.get_running_loop()`` raises;
    ``_generate`` exists only to satisfy the ABC. ``bind_tools`` must be
    overridden too: ``create_react_agent`` calls it and the base implementation
    raises.

    Returns:
        A fresh model instance whose ``invoke_count`` attribute counts invokes —
        the discriminator for "the turn did not re-plan".
    """
    require_real_langchain("langchain_core")

    from langchain_core.language_models.chat_models import (  # pylint: disable=import-error
        BaseChatModel,
    )
    from langchain_core.messages import AIMessage  # pylint: disable=import-error
    from langchain_core.outputs import (  # pylint: disable=import-error
        ChatGeneration,
        ChatResult,
    )

    class _FakeChatModel(BaseChatModel):  # type: ignore[misc]
        """Scripted model: tool call on the first invoke, plain text after."""

        invoke_count: int = 0

        def bind_tools(self, tools: Any, **kw: Any) -> "_FakeChatModel":
            return self

        def _generate(self, messages, stop=None, run_manager=None, **kw):  # type: ignore[no-untyped-def]
            raise NotImplementedError(
                "_FakeChatModel implements _agenerate, not _generate"
            )

        async def _agenerate(self, messages, stop=None, run_manager=None, **kw):  # type: ignore[no-untyped-def]
            self.invoke_count += 1
            if self.invoke_count == 1:
                message = AIMessage(
                    content="",
                    tool_calls=[{"name": TOOL_NAME, "args": {}, "id": "call_1"}],
                )
            else:
                message = AIMessage(content="done")
            return ChatResult(generations=[ChatGeneration(message=message)])

        @property
        def _llm_type(self) -> str:
            return "fake-approval"

    return _FakeChatModel()


@dataclass
class Gate:
    """Per-run handoff: the agent loop plus the Future a blocking tool awaits.

    One fresh instance per run, bound into the tool by
    :func:`make_blocking_tool`. It must not be shared: a run that never resolves
    leaves ``fired`` true forever, so the next run's wait would pass immediately
    and act on a stale loop and a stale Future.

    Attributes:
        loop: The agent loop, captured with ``get_running_loop()`` *inside* the
            tool coroutine. A build-time handle would name a different loop —
            ``asyncio.run`` creates one per turn.
        future: The Future the parked coroutine is awaiting.
        fired: Set once ``loop`` and ``future`` are both published.
    """

    loop: asyncio.AbstractEventLoop | None = None
    future: asyncio.Future[str] | None = None
    fired: bool = False


def make_blocking_tool(gate: Gate, name: str = TOOL_NAME) -> Any:
    """Build a ``StructuredTool`` whose coroutine parks on *gate*'s Future.

    The coroutine takes **no** arguments: ``ToolNode`` validates the model's
    ``args`` against the tool schema before the coroutine runs, so a tool with
    required parameters would be rejected without ever blocking.

    Args:
        gate: The per-run handoff this tool publishes its loop and Future onto.
        name: The tool name the model must ask for.

    Returns:
        A ``StructuredTool`` usable with ``create_react_agent``.
    """
    require_real_langchain("langchain_core")

    from langchain_core.tools import StructuredTool  # pylint: disable=import-error

    async def _blocking_call() -> str:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[str] = loop.create_future()
        gate.loop = loop
        gate.future = future
        # Published last: a driver polling `fired` must never see a half-filled
        # gate and reach for a loop or Future that is not there yet.
        gate.fired = True
        return await future

    return StructuredTool.from_function(
        coroutine=_blocking_call,
        name=name,
        description="Blocks until the cross-thread Future is resolved.",
    )


def wait_for(pred: Callable[[], bool], timeout: float = 5.0) -> bool:
    """Poll *pred* until it is true or *timeout* seconds elapse.

    Args:
        pred: The condition to poll.
        timeout: How long to keep polling, in seconds.

    Returns:
        Whether the condition became true within the deadline.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if pred():
            return True
        time.sleep(0.01)
    return bool(pred())
