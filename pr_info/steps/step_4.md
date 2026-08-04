# Step 4 — D7 approval-bridge seam (standalone model) + Gotcha #2 side-channel emit

**Commit:** `spike(i3.1): D7 seam — attach/detach lifecycle, stale-q, side-channel emit`

Read `pr_info/steps/summary.md` first. This step models the interceptor→`q` plumbing seam (D7)
**standalone** — it does **not** modify the real `prompt_llm_stream` / `ask_langchain_stream` /
`_ask_agent_stream`. D7 is explicitly "recorded as a recommendation; nothing ships", so a small
faithful model demonstrates the attach/detach lifecycle and the **stale-`q`-across-turns** failure
mode, and yields the recommendation, with zero production churn.

It also closes gotcha **#2** (side-channel pending-approval event) **end-to-end** rather than by
prose: the `q` in this model is a **real `queue.Queue`**, the "interceptor" **puts a real
`approval_request` `StreamEvent` onto it** (the shape `#1045` pinned), and the assertion `get()`s
that event back off the turn's own queue — proving the side channel is genuinely reachable from
inside the interceptor, not merely asserted in FINDINGS.

## WHERE

- Create `spikes/i3-1-approval/tier_d7_seam.py` (self-contained).

## WHAT — functions / signatures

```python
from dataclasses import dataclass
from contextlib import contextmanager
import queue

@dataclass
class ApprovalBridge:
    """Threaded prompt_llm_stream -> ask_langchain_stream -> _ask_agent_stream, per stream."""
    q: "queue.Queue"                # the per-turn queue.Queue (real, not a sentinel)

class Gateway:
    """Built ONCE at startup (mirrors the real single-instance gateway)."""
    bridge: ApprovalBridge | None = None

@contextmanager
def attach_bridge(gw: Gateway, bridge: ApprovalBridge):
    """try/finally attach on enter, detach on exit — the CORRECT lifecycle."""

def prompt_llm_stream_model(gw, q, *, detach: bool) -> object:
    """Model of the real call chain; detach=False reproduces the bug."""

def emit_approval_request(gw, *, approval_id: str, tool_name: str, args: dict) -> None:
    """Interceptor side: put a real approval_request StreamEvent onto gw.bridge.q (gotcha #2)."""

def scenario_correct() -> None:      # two turns, each sees ONLY its own q
def scenario_stale_q() -> None:      # detach omitted -> turn 2 sees turn 1's stale q (the bug)
def scenario_side_channel() -> None: # interceptor emits a real approval_request; reachable off q (#2)
```

## HOW — integration points

- `Gateway` is instantiated once (startup analog). Each "turn" builds a fresh `ApprovalBridge`
  wrapping a distinct **real `queue.Queue`** (e.g. `q1 = queue.Queue()`, `q2 = queue.Queue()`);
  distinct instances still give the identity comparison the stale-`q` check needs.
- `attach_bridge` sets `gw.bridge = bridge` on enter and `gw.bridge = None` in a `finally` —
  the shape I3.2 must thread through the three real functions.
- The "interceptor" reads `gw.bridge.q` at call time; the stale-`q` assertion compares it to the
  turn's own `q`, and `emit_approval_request` uses it to `put()` the side-channel event.

## ALGORITHM — stale-q failure (scenario_stale_q, D7)

```
turn 1: gw.bridge = ApprovalBridge(q1)     # attached, but NO detach (bug reproduction)
assert gw.bridge.q is q1
turn 2: begins without attaching a fresh bridge
observed = gw.bridge.q                      # interceptor reads the gateway
assert observed is q1 and observed is not q2   # STALE: turn 2 wrongly targets turn 1's queue
# scenario_correct repeats with attach_bridge()'s try/finally -> observed is q2
```

## ALGORITHM — side-channel emit (scenario_side_channel, #2)

```
turn: with attach_bridge(gw, ApprovalBridge(q))     # q is a real queue.Queue
event = {"type":"approval_request","approval_id":"a","tool_name":"ping","args":{"text":"hi"},
         "source":"..."}
emit_approval_request(gw, approval_id="a", tool_name="ping", args={"text":"hi"})  # interceptor puts it
got = q.get_nowait()                                 # side channel is reachable from inside
assert got["type"] == "approval_request" and got["approval_id"] == "a"   # #2: emit round-trips
# after the context exits (detach), gw.bridge is None -> emitting would have nowhere to go (the D7 seam)
```

## DATA

- Each turn's `q` is a **real `queue.Queue`**; the stale-`q` check uses instance identity, and the
  side-channel check uses a real `put()`/`get_nowait()` round-trip of an `approval_request` event.
- Prints `PASS: attach-detach-lifecycle`, `PASS: stale-q-failure-reproduced`,
  `PASS: side-channel-emit-reachable`; exits 0.

## Recommendation to carry into FINDINGS (Step 6)

State the shape explicitly: an `ApprovalBridge` threaded
`prompt_llm_stream → ask_langchain_stream → _ask_agent_stream`, attached/detached **per stream in
`try/finally`**; the parameter must stay **optional** because `ask_langchain_stream` is also called
by non-iCoder CLI paths that must keep working with it absent. The stale-`q` scenario is the
failure mode I3.2 must guard against.

## Definition of done

- `python spikes/i3-1-approval/tier_d7_seam.py` exits 0, all PASS lines, repeatable.
- Standard `src`/`tests` fast unit suite still green.
