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
      it to suspend the two streaming timeouts), and :attr:`turn_aborted` is a
      cross-thread ``bool`` read (``AppCore`` uses it to decide whether the turn
      may be recorded).

    Each of those is a single attribute rebind or one ``len()`` — atomic under
    the GIL — so no lock is needed. Two consequences are *coded*, not assumed:
    the ``self._emit is not None`` guard in :meth:`request_approval`'s
    ``finally`` (the sink may already be gone when a racing ``detach()`` won),
    the cancel-then-clear order in :meth:`detach`, and reading the loop handle
    **once into a local** in :meth:`request_approval` (``detach()`` nulls
    ``_loop`` last, so a re-read off the instance could yield ``None`` between
    the assignment and the ``create_future()`` call).

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
        self._turn_aborted = False

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
        self._turn_aborted = False

    def detach(self) -> None:
        """Cancel still-pending approvals, unbind the sink, clear the registry.

        Cancels **before** clearing: after the clear nothing can reach these
        futures again, and an interceptor parked on one keeps the daemon agent
        thread alive for the rest of the process (``GeneratorExit`` *is*
        reachable while an approval is pending). The caller must in turn run
        ``detach()`` **before** ``thread.join(timeout=5)``, so the parked
        interceptor unwinds while the join waits; joining first burns the full
        five seconds and returns with the thread still alive.

        ``_cancelled`` and ``_turn_aborted`` deliberately survive:
        ``AppCore.stream_llm`` reads the latter *after* this has already run, to
        decide whether the turn may be recorded.
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
        """Whether a cancel was *requested* for this turn.

        Set by every :meth:`cancel_all`, including one that found nothing to
        cancel. It stops further emits and unwinds later approval requests with
        ``asyncio.CancelledError``, so it is a statement about the channel, not
        about the turn's outcome — use :attr:`turn_aborted` for that. Reset by
        :meth:`attach`, **not** by :meth:`detach`.

        Returns:
            ``True`` once :meth:`cancel_all` ran for the current turn.
        """
        return self._cancelled

    @property
    def turn_aborted(self) -> bool:
        """Whether this turn was actually unwound by the direct cancel channel.

        Narrower than :attr:`cancelled` on purpose, and the two must not be
        conflated. A cancel only unwinds the provider generator — skipping its
        ``done`` event, which is the entire reason ``AppCore`` gates the turn
        record on this — when there was a parked interceptor to unpark. A
        :meth:`cancel_all` with nothing pending changes nothing about the turn:
        it is an idle key press, or app shutdown while an ordinary turn is still
        streaming, and that turn either completes normally (and must be
        recorded) or is torn down by the generic cancel path, whose teardown
        never reaches the gate anyway.

        Reset by :meth:`attach`, **not** by :meth:`detach` — the read happens
        after ``detach()`` has already run in the provider's ``finally``.

        Returns:
            ``True`` once at least one pending approval was cancelled through
            :meth:`cancel_all` during the current turn.
        """
        return self._turn_aborted

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
            ``_DENY_UNAVAILABLE`` when no prompt is reachable because nothing is
            attached — never a bare deny, which the gateway would render to the
            model as "denied by the user".

        Raises:
            asyncio.CancelledError: If the turn is already cancelled. A deny
                would invite the model to re-plan around a refusal on a turn the
                user asked to abandon; unwinding is the designed cancel
                semantics (R7), and the gateway propagates this untouched.
        """
        # Two conditions, two different answers. ``_cancelled`` is set by every
        # ``cancel_all()`` and reset only by ``attach()``, so an Escape press
        # with nothing pending arms it for the rest of the turn: an ``ask``
        # reached in that window belongs to a turn the user abandoned and must
        # unwind, not deny. A missing sink is the other case — a non-iCoder
        # caller, or any window before ``attach`` — where fail-closed denial is
        # the required behaviour (§2.11).
        if self._cancelled:
            raise asyncio.CancelledError
        if self._emit is None:
            return ApprovalDecision("deny", "once", reason=_DENY_UNAVAILABLE)
        # Bind the loop to a local and create the future from *that*: a racing
        # ``detach()`` nulls ``self._loop`` as its last act, so reading the
        # attribute back would raise ``AttributeError`` here instead of letting
        # the post-insert re-check below cancel this entry cleanly. The
        # instance attribute is still assigned, for the cross-thread
        # ``resolve_pending`` / ``cancel_all`` paths.
        loop = self._loop = asyncio.get_running_loop()
        approval_id = uuid4().hex
        future: asyncio.Future[ApprovalDecision] = loop.create_future()
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
            if self.cancelled:
                # The cancel channel unparks this interceptor after all, so the
                # turn really is aborted — ``_cancel_all_on_loop`` could not
                # record that for an entry it never saw. Read through the
                # property for the same reason ``is_attached()`` exists above:
                # a bare ``self._cancelled`` re-test is narrowed to unreachable.
                self._turn_aborted = True
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
        """Abort every pending approval.

        The direct UI → engine cancel channel: the generic cancel paths cannot
        reach an interceptor parked on an approval. Sets ``_cancelled`` on the
        Textual thread (which also stops any further emit), then cancels the
        futures **on the agent loop**.

        Marking the *turn* aborted is left to the two sites that know whether
        anything was actually unparked (see :attr:`turn_aborted`) — this method
        is also called on a bare key press and on app shutdown, neither of which
        need have a turn to abort.
        """
        self._cancelled = True
        loop = self._loop
        if loop is not None:
            try:
                loop.call_soon_threadsafe(self._cancel_all_on_loop)
            except RuntimeError:
                # Same hazard as in :meth:`detach`, reached from the Textual
                # thread: ``_loop`` stays bound until ``detach()`` nulls it, and
                # ``asyncio.run`` may have closed that loop first. A closed loop
                # means nothing is parked, so there is nothing to cancel — and
                # this runs on a key press and on app shutdown, neither of which
                # may raise.
                logger.debug(
                    "cancel_all(): agent loop already closed; nothing to cancel"
                )

    # -- internals ------------------------------------------------------------

    def _cancel_all_on_loop(self) -> None:
        """Cancel every registered future; runs on the agent loop.

        Also raises ``_turn_aborted`` when it finds anything to cancel. This is
        the authoritative site rather than :meth:`cancel_all`: it reads the
        registry *on the loop that owns it*, at the moment of the cancellation,
        so it cannot mistake an approval registered a moment later for one this
        cancel unparked (nor the reverse).
        """
        if self._pending:
            self._turn_aborted = True
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
