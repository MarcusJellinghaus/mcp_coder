"""Runtime approval engine: the in-band pause behind an ``ask`` policy.

The engine is the pure-asyncio half of the two-loop approval bridge. A tool-call
interceptor running on the **agent loop** calls :meth:`ApprovalEngine.request_approval`,
which registers an :class:`asyncio.Future`, emits one ``approval_request``
``StreamEvent`` through the turn's queue, and awaits the human answer. The UI
thread answers through :meth:`ApprovalEngine.resolve_pending` (or aborts the turn
through :meth:`ApprovalEngine.cancel_all`); the provider owns the per-turn
lifecycle through :meth:`ApprovalEngine.attach` / :meth:`ApprovalEngine.detach`.

The module is a leaf by contract (``permissions_leaf_isolation``): no Textual, no
langchain, no ``icoder.core`` / ``icoder.ui`` / ``icoder.services``. The deny
``ToolMessage`` a refusal turns into is built by the gateway, never here.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, NamedTuple
from uuid import uuid4

if TYPE_CHECKING:  # pragma: no cover - typing-only, see module docstring
    # Typing-only on purpose. A runtime import would eagerly execute the
    # langchain provider package's ``__init__`` for every importer of
    # ``icoder.permissions``. The import-linter edge is still recorded (grimp is
    # AST-based) and is legal: importing a *submodule* creates no edge to its
    # parent package, and ``approval_bridge`` imports no ``langchain_*``.
    from mcp_coder.llm.providers.langchain.approval_bridge import ApprovalBridge
    from mcp_coder.llm.types import StreamEvent

logger = logging.getLogger(__name__)

_DENY_UNAVAILABLE = (
    "This tool requires approval, but no approval prompt was reachable, so the "
    "call was refused without asking the user. Choose a different approach or "
    "ask the user how to proceed."
)


@dataclass(frozen=True)
class ApprovalDecision:
    """One answer to one approval request.

    Attributes:
        outcome: ``"allow"`` runs the call, ``"deny"`` refuses it.
        scope: How long the answer lasts. ``"session"`` / ``"persist"`` are
            allow-only in v1 — a deny is always once-only.
        reason: Optional deny-text override carried through to the gateway,
            which uses it in place of its own "denied by the user" wording.
            Set by the two producers that deny *without* asking anybody (the
            engine's fail-closed deny and the interim UI auto-deny), so the
            model is never told a user refused a call nobody was asked about.
            Ignored on an ``allow``.
    """

    outcome: Literal["allow", "deny"]
    scope: Literal["once", "session", "persist"] = "once"
    reason: str | None = None

    def __post_init__(self) -> None:
        """Reject a deny carrying a durable scope (deny is once-only in v1).

        Raises:
            ValueError: If ``outcome`` is ``"deny"`` and ``scope`` is not
                ``"once"``.
        """
        if self.outcome == "deny" and self.scope != "once":
            raise ValueError(
                f"deny is once-only; got scope={self.scope!r}. "
                "Durable scopes are allow-only."
            )


class _PendingApproval(NamedTuple):
    """One registered approval: the future to resolve and the event to emit."""

    future: asyncio.Future[ApprovalDecision]
    payload: StreamEvent


def _set_if_pending(
    future: asyncio.Future[ApprovalDecision], decision: ApprovalDecision
) -> None:
    """Resolve *future* with *decision* unless it is already done.

    Runs **on the agent loop** (scheduled with ``call_soon_threadsafe``), so the
    future may have been cancelled between the scheduling and this call.

    Args:
        future: The future the interceptor coroutine is awaiting.
        decision: The answer to hand it.
    """
    if not future.done():
        future.set_result(decision)


class ApprovalEngine:
    """One insertion-ordered dict serving as registry, FIFO order and counter.

    **Why there is no lock.** The registry is mutated on the **agent loop** in
    the normal case: interceptor coroutines run there, and both cross-thread
    entry points (:meth:`resolve_pending`, :meth:`cancel_all`) only hand their
    bodies over with ``call_soon_threadsafe``. Three members are nevertheless
    touched *off* that loop, so this is **not** a single-threaded object:

    * :meth:`attach` / :meth:`detach` rebind ``_pending``, ``_emit``, ``_loop``
      (and ``_cancelled``, on ``attach``) from the **consumer thread** —
      ``_ask_agent_stream``'s body and its ``finally``. ``detach()`` runs
      *before* ``thread.join(timeout=5)``, i.e. deliberately **while the agent
      loop is still live**: cancelling the pending futures is precisely what
      lets that join succeed. So ``detach()`` can race an interceptor coroutine
      that is still unwinding on the agent loop.
    * :meth:`cancel_all` sets ``_cancelled`` from the **Textual thread** before
      scheduling the cancellations onto the loop.
    * :meth:`pending` is a cross-thread ``len()`` read (the consumer thread uses
      it to suspend the two streaming timeouts).

    Each of those is a single attribute rebind or one ``len()`` — atomic under
    the GIL — so no lock is needed. Two consequences are *coded*, not assumed:
    the ``self._emit is not None`` guard in :meth:`request_approval`'s
    ``finally`` (the sink may already be gone when a racing ``detach()`` won),
    and the cancel-then-clear order in :meth:`detach`.

    **Documented deviation from R3's mechanism (approved).** R3 specifies a
    serial lock held around the emit. There is no lock here; its *guarantee* —
    at most one ``approval_request`` outstanding, so the UI renders exactly one
    modal — is strictly preserved, and by construction rather than by
    discipline: the entry is inserted **before** the emit, and only the front
    entry of the dict is ever emitted.

    **Why the loop handle is taken inside the coroutine.** ``_loop`` is set from
    ``asyncio.get_running_loop()`` inside :meth:`request_approval`, never from a
    handle captured at build time: a build-time handle would target the
    ``MCPManager`` daemon loop, and the cross-thread resolve would silently
    never wake the awaiting coroutine.

    **Why the direct UI cancel channel exists.** The three generic cancel paths
    (``cancel_event``, the TUI ``_cancel_event``, ``GeneratorExit``) are all
    gated on an event arriving from the generator, and an interceptor blocked on
    an approval emits none — so none of them can *trigger* a cancel while the
    consumer sits in ``q.get``. They remain wired as a post-resolution backstop
    only; :meth:`cancel_all` is the path that actually unwinds a pending turn.

    **Why detach() clears the registry.** ``asyncio.run`` is called once per
    turn, so the loop object differs every turn. A future left over from turn N
    belongs to a dead loop and can never be resolved from turn N+1 — it would
    only park the next interceptor forever.
    """

    def __init__(self) -> None:
        """Create a detached engine with an empty registry."""
        self._pending: dict[str, _PendingApproval] = {}
        self._emit: Callable[[StreamEvent], None] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._cancelled = False

    # -- per-turn lifecycle (consumer thread) --------------------------------

    def attach(self, emit: Callable[[StreamEvent], None]) -> None:
        """Bind the per-turn event sink and reset per-turn state.

        Args:
            emit: Callable pushing a ``StreamEvent`` into the turn's queue.
        """
        self._pending.clear()
        self._emit = emit
        self._loop = None
        self._cancelled = False

    def detach(self) -> None:
        """Cancel still-pending approvals, unbind the sink, clear the registry.

        Cancels **before** clearing: after the clear nothing can reach these
        futures again, and an interceptor parked on one keeps the daemon agent
        thread alive for the rest of the process (``GeneratorExit`` *is*
        reachable while an approval is pending). The caller must in turn run
        ``detach()`` **before** ``thread.join(timeout=5)``, so the parked
        interceptor unwinds while the join waits; joining first burns the full
        five seconds and returns with the thread still alive.

        ``_cancelled`` deliberately survives: ``AppCore.stream_llm`` reads it
        *after* this has already run, to decide whether the turn may be
        recorded.
        """
        loop = self._loop
        if loop is not None:
            for entry in list(self._pending.values()):
                try:
                    loop.call_soon_threadsafe(entry.future.cancel)
                except RuntimeError:
                    # The agent loop is already closed, because the turn
                    # finished on its own and ``asyncio.run`` returned. Nothing
                    # is parked, so there is nothing to cancel — and this runs
                    # inside a ``finally`` that must not raise.
                    logger.debug(
                        "detach(): agent loop already closed; nothing to cancel"
                    )
                    break
        self._pending.clear()
        self._emit = None
        self._loop = None

    def pending(self) -> int:
        """Return the number of approvals awaiting a human decision.

        Returns:
            The size of the registry (read cross-thread).
        """
        return len(self._pending)

    def is_attached(self) -> bool:
        """Report whether a per-turn event sink is currently bound.

        Returns:
            ``True`` between :meth:`attach` and :meth:`detach`.
        """
        return self._emit is not None

    def pending_ids(self) -> tuple[str, ...]:
        """Return the pending approval ids in arrival order.

        Insertion happens before any ``await``, so this is genuine arrival
        order rather than wake order.

        Returns:
            The registered approval ids, oldest first.
        """
        return tuple(self._pending)

    @property
    def cancelled(self) -> bool:
        """Whether this turn was cancelled through :meth:`cancel_all`.

        Reset by :meth:`attach`, **not** by :meth:`detach`.

        Returns:
            ``True`` once :meth:`cancel_all` ran for the current turn.
        """
        return self._cancelled

    # -- the agent loop side --------------------------------------------------

    async def request_approval(
        self, *, tool_name: str, args: Mapping[str, object], source: str
    ) -> ApprovalDecision:
        """Ask the human about one tool call and await the answer.

        Called from the tool-call interceptor, on the agent loop.

        Args:
            tool_name: The canonical ``mcp__server__tool`` name being called.
            args: The call arguments (copied into the emitted payload).
            source: Plain-string provenance of the decision that asked, as
                produced by ``gateway._source_label``: the bare layer name for
                a ``Layer`` (``"user"`` / ``"project"`` / ``"local"`` /
                ``"runtime"``), ``"frame"`` for a ``Frame``, ``"default"``
                otherwise — never a ``Decision.Source`` dataclass, so the
                payload stays JSON-safe.

        Returns:
            The decision to apply. A fail-closed deny carrying
            ``_DENY_UNAVAILABLE`` when no prompt is reachable (detached, or the
            turn is already cancelled) — never a bare deny, which the gateway
            would render to the model as "denied by the user".
        """
        if self._cancelled or self._emit is None:
            return ApprovalDecision("deny", "once", reason=_DENY_UNAVAILABLE)
        self._loop = asyncio.get_running_loop()
        approval_id = uuid4().hex
        future: asyncio.Future[ApprovalDecision] = self._loop.create_future()
        self._pending[approval_id] = _PendingApproval(
            future, _payload(approval_id, tool_name, args, source)
        )
        # Re-check AFTER the insert, not only before it. Both teardown paths
        # walk the registry from another thread, so either can run between the
        # guard above and this insert and miss this entry: ``detach()`` cancels
        # then clears, and ``cancel_all()`` schedules nothing at all when it
        # reads ``_loop`` while it is still ``None`` — which is exactly the
        # state a turn is in until its *first* approval assigns it two lines
        # up. Cancelling here is what the teardown would have done; without it
        # the interceptor parks on a future nothing can reach, and since a
        # pending approval suspends both streaming timeouts that wedges the
        # turn permanently.
        # (Read the sink through :meth:`is_attached` rather than testing the
        # attribute again: a second `self._emit is None` test looks unreachable
        # to a single-threaded type checker, which is precisely the assumption
        # this re-check exists to deny.)
        if self._cancelled or not self.is_attached():
            future.cancel()
        elif len(self._pending) == 1:  # only the front entry is ever emitted
            self._emit_front()
        try:
            return await future  # CancelledError propagates to the gateway
        finally:
            self._pending.pop(approval_id, None)
            # ``detach()`` runs on the consumer thread while this coroutine is
            # still unwinding, so the sink may already be gone.
            if not self._cancelled and self._emit is not None:
                self._emit_front()  # promote the next entry, FIFO by arrival

    # -- the UI thread side ---------------------------------------------------

    def resolve_pending(self, approval_id: str, decision: ApprovalDecision) -> None:
        """Answer one pending approval from the UI thread.

        Unknown or already-answered ids are ignored, so a late click on a
        superseded modal is harmless.

        Args:
            approval_id: The id carried by the ``approval_request`` event.
            decision: The human's answer.
        """
        entry, loop = self._pending.get(approval_id), self._loop
        if entry is not None and loop is not None:
            loop.call_soon_threadsafe(_set_if_pending, entry.future, decision)

    def cancel_all(self) -> None:
        """Abort every pending approval and mark the turn cancelled.

        The direct UI → engine cancel channel: the generic cancel paths cannot
        reach an interceptor parked on an approval. Sets ``_cancelled`` on the
        Textual thread (which also stops any further emit), then cancels the
        futures **on the agent loop**.
        """
        self._cancelled = True
        loop = self._loop
        if loop is not None:
            loop.call_soon_threadsafe(self._cancel_all_on_loop)

    # -- internals ------------------------------------------------------------

    def _cancel_all_on_loop(self) -> None:
        """Cancel every registered future; runs on the agent loop."""
        for entry in list(self._pending.values()):
            entry.future.cancel()

    def _emit_front(self) -> None:
        """Emit the ``approval_request`` of the oldest registered approval."""
        emit = self._emit
        if emit is None:
            return
        front = next(iter(self._pending.values()), None)
        if front is not None:
            emit(front.payload)


def _payload(
    approval_id: str, tool_name: str, args: Mapping[str, object], source: str
) -> StreamEvent:
    """Build the JSON-safe ``approval_request`` event for one approval.

    Args:
        approval_id: The registry key the UI answers with.
        tool_name: The canonical tool name being called.
        args: The call arguments (copied, so later mutation cannot leak).
        source: Plain-string provenance of the asking decision.

    Returns:
        The ``StreamEvent`` to push into the turn's queue.
    """
    return {
        "type": "approval_request",
        "approval_id": approval_id,
        "tool_name": tool_name,
        "args": dict(args),
        "source": source,
    }


if TYPE_CHECKING:
    # Structural conformance, proven by mypy and costing nothing at runtime:
    # the engine must stay assignable to the provider's seam Protocol.
    _bridge_conformance: ApprovalBridge = ApprovalEngine()


__all__ = ["ApprovalDecision", "ApprovalEngine"]
