"""Seam between the langchain consumer loop and the runtime approval engine.

``layered_architecture`` places ``mcp_coder.icoder`` **above**
``mcp_coder.llm``, so the langchain provider cannot import the engine that
implements the in-band approval pause
(:class:`mcp_coder.icoder.permissions.approval.ApprovalEngine`). This module
holds the structural type it talks to instead: the provider depends on the
Protocol, the engine satisfies it structurally, and the dependency arrow keeps
pointing downward.

**No langchain import at any scope** — not even inside a function. ``grimp``
(import-linter's AST backend) records function-level imports as real edges, and
the engine side imports this module, so any langchain import here would drag
``langchain_core`` into the ``permissions_leaf_isolation`` contract.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from mcp_coder.llm.types import StreamEvent


class ApprovalBridge(Protocol):
    """Per-turn lifecycle of the approval engine, as the provider sees it.

    The provider owns the turn, so it owns the lifecycle: it binds the sink at
    the top of ``_ask_agent_stream`` and unbinds it in the same ``try``'s
    ``finally``. It never resolves an approval — that is the UI's side of the
    engine, which this Protocol deliberately does not expose.
    """

    def attach(self, emit: Callable[[StreamEvent], None]) -> None:
        """Bind the per-turn event sink and reset per-turn state.

        Args:
            emit: Callable pushing a ``StreamEvent`` into the turn's queue.
        """

    def detach(self) -> None:
        """Cancel still-pending approvals, unbind the sink, clear the registry.

        Called from the consumer thread **before** the agent thread is joined,
        so an interceptor parked on an approval unwinds while the join waits.
        """

    def pending(self) -> int:
        """Return the number of approvals awaiting a human decision.

        Read cross-thread (from the consumer thread) to suspend the two
        streaming timeouts while a human is being asked.

        Returns:
            The number of approvals currently registered and unanswered.
        """
