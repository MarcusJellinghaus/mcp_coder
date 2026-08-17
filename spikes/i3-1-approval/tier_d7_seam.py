"""Tier D7 — approval-bridge seam, modelled STANDALONE (#1044).

Models the interceptor -> ``q`` plumbing seam (D7) without touching the real
call chain ``prompt_llm_stream`` -> ``ask_langchain_stream`` -> ``_ask_agent_stream``.
D7 is "recorded as a recommendation; nothing ships", so this small faithful
model demonstrates the lifecycle + failure mode and yields the recommendation
with zero production churn.

Proves:
  * D7 — an ``ApprovalBridge`` is attached per-stream on a single-instance
    ``Gateway`` and detached in ``try/finally`` (the CORRECT lifecycle); each
    turn's interceptor reads ``gw.bridge.q`` and sees ONLY its own queue.
  * D7 failure mode — omitting the detach leaves turn 2 reading turn 1's STALE
    ``q`` (the bug I3.2 must guard against).
  * gotcha #2 — the side channel is genuinely reachable: the "interceptor"
    puts a real ``approval_request`` ``StreamEvent`` onto a real
    ``queue.Queue`` and the assertion ``get()``s it back off the turn's own
    queue (not merely asserted in prose).

Run directly::

    python spikes/i3-1-approval/tier_d7_seam.py

Exits 0 with a ``PASS: <mechanic>`` line per demonstrated mechanic; any failed
assertion raises ``AssertionError`` (non-zero exit).

Recommendation carried into FINDINGS (Step 6): thread an ``ApprovalBridge``
``prompt_llm_stream`` -> ``ask_langchain_stream`` -> ``_ask_agent_stream``,
attached/detached PER STREAM in ``try/finally``; the parameter must stay
OPTIONAL because ``ask_langchain_stream`` is also called by non-iCoder CLI
paths that must keep working with it absent. The stale-``q`` scenario is the
failure mode I3.2 must guard against.

Two frictions I3.2 will otherwise hit cold (FINDINGS content only — named, not
resolved here):
  (a) Provider-agnostic-interface tension. ``prompt_llm_stream``
      (``src/mcp_coder/llm/interface.py``, ``provider: str = "claude"``) is the
      PROVIDER-AGNOSTIC interface, and I2.3 / #1043 D1 explicitly REJECTED
      threading a langchain-permissions object through it. D7 prescribes exactly
      that.
  (b) The no-MCP branch the parameter must cross. ``ask_langchain_stream``
      (``llm/providers/langchain/__init__.py``) branches to ``_ask_text_stream``
      when ``mcp_config`` is absent — so the bridge parameter has to traverse
      that path as a NO-OP.
"""

from __future__ import annotations

import queue
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

# The real shipped shape: ``StreamEvent = dict[str, object]`` (llm/types.py).
StreamEvent = dict[str, object]


@dataclass
class ApprovalBridge:
    """Per-stream bridge modelling the object threaded
    ``prompt_llm_stream`` -> ``ask_langchain_stream`` -> ``_ask_agent_stream``.

    Wraps the per-turn ``queue.Queue`` (a REAL queue, not a sentinel) that the
    interceptor targets for its side-channel ``approval_request`` events.
    """

    q: "queue.Queue[StreamEvent]"


class Gateway:
    """Built ONCE at startup (mirrors the real single-instance gateway).

    Holds at most one attached bridge at a time; the interceptor reads
    ``gw.bridge.q`` at call time.
    """

    bridge: ApprovalBridge | None = None


@contextmanager
def attach_bridge(gw: Gateway, bridge: ApprovalBridge) -> Iterator[ApprovalBridge]:
    """Attach on enter, detach on exit — the CORRECT per-stream lifecycle.

    Sets ``gw.bridge = bridge`` on enter and ``gw.bridge = None`` in a
    ``finally`` (so the detach happens even if the stream raises). This is the
    shape I3.2 must thread through the three real functions.
    """
    gw.bridge = bridge
    try:
        yield bridge
    finally:
        gw.bridge = None


def prompt_llm_stream_model(
    gw: Gateway, q: "queue.Queue[StreamEvent]", *, detach: bool
) -> "queue.Queue[StreamEvent]":
    """Model of the real call chain for one turn.

    ``detach=True`` runs the correct ``attach_bridge`` try/finally lifecycle and
    returns the ``q`` the interceptor observed via ``gw.bridge``.
    ``detach=False`` reproduces the bug: it attaches WITHOUT ever detaching,
    leaving the gateway pointing at this turn's ``q`` after the turn ends.
    """
    if detach:
        with attach_bridge(gw, ApprovalBridge(q)):
            # The "interceptor" reads the gateway at call time.
            assert gw.bridge is not None
            return gw.bridge.q
    # Bug reproduction: attach, never detach.
    gw.bridge = ApprovalBridge(q)
    return gw.bridge.q


def emit_approval_request(
    gw: Gateway, *, approval_id: str, tool_name: str, args: dict[str, object]
) -> None:
    """Interceptor side: put a real ``approval_request`` ``StreamEvent`` onto
    ``gw.bridge.q`` (gotcha #2).

    Reads the currently-attached bridge's queue and ``put()``s the event I3.2
    pinned. If no bridge is attached (post-detach), the side channel has nowhere
    to go — that is the D7 seam.
    """
    if gw.bridge is None:
        raise RuntimeError("no bridge attached — the side channel has nowhere to go")
    event: StreamEvent = {
        "type": "approval_request",
        "approval_id": approval_id,
        "tool_name": tool_name,
        "args": args,
        "source": "interceptor",
    }
    gw.bridge.q.put(event)


def scenario_correct() -> None:
    """Two turns, each with the correct attach/detach lifecycle; each turn's
    interceptor sees ONLY its own queue, and the gateway is clean between turns.
    """
    gw = Gateway()
    assert gw.bridge is None, "gateway must start with no bridge attached"

    q1: "queue.Queue[StreamEvent]" = queue.Queue()
    observed_1 = prompt_llm_stream_model(gw, q1, detach=True)
    assert observed_1 is q1, "turn 1 interceptor must observe its own q1"
    assert gw.bridge is None, "detach must clear the gateway after turn 1"

    q2: "queue.Queue[StreamEvent]" = queue.Queue()
    observed_2 = prompt_llm_stream_model(gw, q2, detach=True)
    assert observed_2 is q2, "turn 2 interceptor must observe its own q2"
    assert observed_2 is not q1, "turn 2 must NOT observe the turn-1 queue"
    assert gw.bridge is None, "detach must clear the gateway after turn 2"

    print("PASS: attach-detach-lifecycle")


def scenario_stale_q() -> None:
    """Detach omitted -> turn 2 sees turn 1's STALE q (the bug).

    Reproduces exactly the failure mode D7's recommendation guards against: a
    bridge from turn 1 is never detached, so when turn 2 begins without
    attaching a fresh bridge, the interceptor reads the gateway and wrongly
    targets turn 1's queue.
    """
    gw = Gateway()

    # turn 1: attached, but NO detach (bug reproduction).
    q1: "queue.Queue[StreamEvent]" = queue.Queue()
    prompt_llm_stream_model(gw, q1, detach=False)
    assert gw.bridge is not None and gw.bridge.q is q1

    # turn 2: begins WITHOUT attaching a fresh bridge; the interceptor reads
    # the gateway and gets the stale queue.
    q2: "queue.Queue[StreamEvent]" = queue.Queue()
    assert gw.bridge is not None
    observed = gw.bridge.q
    assert observed is q1 and observed is not q2, (
        "stale-q not reproduced: turn 2 must wrongly target turn 1's queue"
    )

    print("PASS: stale-q-failure-reproduced")


def scenario_side_channel() -> None:
    """Interceptor emits a real ``approval_request``; reachable off q (#2).

    ``q`` is a real ``queue.Queue``; the interceptor ``put()``s the pinned event
    and the assertion ``get_nowait()``s it straight back off the turn's own
    queue — proving the side channel is genuinely reachable from inside the
    interceptor. After the context exits (detach), the gateway is clear, so a
    further emit has nowhere to go (the D7 seam).
    """
    gw = Gateway()
    q: "queue.Queue[StreamEvent]" = queue.Queue()

    with attach_bridge(gw, ApprovalBridge(q)):
        emit_approval_request(
            gw, approval_id="a", tool_name="ping", args={"text": "hi"}
        )
        got = q.get_nowait()  # side channel is reachable from inside
        assert got["type"] == "approval_request", f"wrong event type: {got!r}"
        assert got["approval_id"] == "a", f"wrong approval_id: {got!r}"
        assert got["tool_name"] == "ping" and got["args"] == {"text": "hi"}

    # After detach the seam is closed: emitting has nowhere to go.
    assert gw.bridge is None, "detach must clear the gateway"
    nowhere = False
    try:
        emit_approval_request(gw, approval_id="b", tool_name="ping", args={})
    except RuntimeError:
        nowhere = True
    assert nowhere, "post-detach emit must fail — the side channel has nowhere to go"

    print("PASS: side-channel-emit-reachable")


def main() -> None:
    """Run every D7 seam scenario."""
    scenario_correct()
    scenario_stale_q()
    scenario_side_channel()


if __name__ == "__main__":
    main()
