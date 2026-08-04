# Step 4 — D7 approval-bridge seam (standalone model)

**Commit:** `spike(i3.1): D7 seam — attach/detach lifecycle + stale-q failure mode`

Read `pr_info/steps/summary.md` first. This step models the interceptor→`q` plumbing seam (D7)
**standalone** — it does **not** modify the real `prompt_llm_stream` / `ask_langchain_stream` /
`_ask_agent_stream`. D7 is explicitly "recorded as a recommendation; nothing ships", so a small
faithful model demonstrates the attach/detach lifecycle and the **stale-`q`-across-turns** failure
mode, and yields the recommendation, with zero production churn.

## WHERE

- Create `spikes/i3-1-approval/tier_d7_seam.py` (self-contained).

## WHAT — functions / signatures

```python
from dataclasses import dataclass
from contextlib import contextmanager

@dataclass
class ApprovalBridge:
    """Threaded prompt_llm_stream -> ask_langchain_stream -> _ask_agent_stream, per stream."""
    q: object                       # stands in for the per-turn queue.Queue

class Gateway:
    """Built ONCE at startup (mirrors the real single-instance gateway)."""
    bridge: ApprovalBridge | None = None

@contextmanager
def attach_bridge(gw: Gateway, bridge: ApprovalBridge):
    """try/finally attach on enter, detach on exit — the CORRECT lifecycle."""

def prompt_llm_stream_model(gw, q, *, detach: bool) -> object:
    """Model of the real call chain; detach=False reproduces the bug."""

def scenario_correct() -> None:   # two turns, each sees ONLY its own q
def scenario_stale_q() -> None:   # detach omitted -> turn 2 sees turn 1's stale q (the bug)
```

## HOW — integration points

- `Gateway` is instantiated once (startup analog). Each "turn" builds a fresh `ApprovalBridge`
  wrapping a distinct sentinel `q` object (e.g. `q1 = object()`, `q2 = object()`).
- `attach_bridge` sets `gw.bridge = bridge` on enter and `gw.bridge = None` in a `finally` —
  the shape I3.2 must thread through the three real functions.
- The "interceptor" reads `gw.bridge.q` at call time; the assertion compares it to the turn's
  own `q`.

## ALGORITHM — stale-q failure (scenario_stale_q, D7)

```
turn 1: gw.bridge = ApprovalBridge(q1)     # attached, but NO detach (bug reproduction)
assert gw.bridge.q is q1
turn 2: begins without attaching a fresh bridge
observed = gw.bridge.q                      # interceptor reads the gateway
assert observed is q1 and observed is not q2   # STALE: turn 2 wrongly targets turn 1's queue
# scenario_correct repeats with attach_bridge()'s try/finally -> observed is q2
```

## DATA

- `q` sentinels are opaque `object()` instances (identity comparison only — no real queue needed).
- Prints `PASS: attach-detach-lifecycle`, `PASS: stale-q-failure-reproduced`; exits 0.

## Recommendation to carry into FINDINGS (Step 6)

State the shape explicitly: an `ApprovalBridge` threaded
`prompt_llm_stream → ask_langchain_stream → _ask_agent_stream`, attached/detached **per stream in
`try/finally`**; the parameter must stay **optional** because `ask_langchain_stream` is also called
by non-iCoder CLI paths that must keep working with it absent. The stale-`q` scenario is the
failure mode I3.2 must guard against.

## Definition of done

- `python spikes/i3-1-approval/tier_d7_seam.py` exits 0, all PASS lines, repeatable.
- Standard `src`/`tests` fast unit suite still green.
