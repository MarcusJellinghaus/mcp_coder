# Step 3 — Tier B (pause): dual-timeout defeat via pending counter

**Commit:** `spike(i3.1): Tier B pause — pending counter defeats both timeouts`

Read `pr_info/steps/summary.md` first. This step demonstrates the **pause** mechanism (D1) that
lets a legitimately paused turn survive both the inactivity `q.get(timeout=…)` and the
`_AGENT_OVERALL_TIMEOUT` wall-clock cap (gotcha **#4**). It reuses the Tier B setup (fake model +
blocking tool) but with a **pause-aware** copy of the consumer. Keepalives are recorded as the
**rejected** alternative — demonstrated, not implemented.

## WHERE

- Create `spikes/i3-1-approval/tier_b_pause.py`. It **imports** `FakeChatModel`, `Gate` /
  `make_blocking_tool` and the verbatim bridge copy from `spikes/i3-1-approval/_common.py`
  (created in Step 2) — one shared harness, not a third hand-maintained copy. This file adds only
  the **pause-aware** consumer variant on top.

## WHAT — functions / signatures

```python
class PendingCounter:
    """Thread-safe pending-approval counter (Lock-guarded int)."""
    def incr(self) -> None: ...
    def decr(self) -> None: ...
    @property
    def value(self) -> int: ...

# small local constants stand in for the monkeypatched production values (#4):
INACTIVITY_TIMEOUT = 2.0      # models q.get(timeout=…), natural 300s not exercised
OVERALL_CAP = 3.0             # models _AGENT_OVERALL_TIMEOUT, natural 3600s not exercised

def run_bridge_paused(gen_factory, pending: PendingCounter) -> list:
    """Bridge copy with pause: Empty -> re-wait while pending>0; cap uses elapsed - paused."""

def scenario_pause_survives() -> None:    # tool pauses > both timeouts, turn still completes
def scenario_baseline_dies() -> None:     # NEGATIVE CONTROL: same pause, verbatim consumer, dies
```

## HOW — integration points

- Same real `run_agent_stream` + `FakeChatModel` + blocking tool as Step 2, imported from
  `_common.py`. Each scenario builds its **own** `Gate()` via `make_blocking_tool(gate)` — no
  module-level gate state shared across scenarios (Step 2's determinism rule applies here too).
- The tool (or the gate around it) calls `pending.incr()` when it begins awaiting the Future and
  `pending.decr()` immediately after it resolves — the counter is the observation channel
  #1045 already pinned; here it also *drives* the pause decision.
- Configure the resolver thread to sleep **5s** (> `INACTIVITY_TIMEOUT` and > `OVERALL_CAP`)
  before pushing `set_result`, so a non-pause consumer would raise `TimeoutError`.

## ALGORITHM — pause-aware consumer (run_bridge_paused, D1)

```
start = monotonic(); paused = 0.0
while True:
    try: event = q.get(timeout=INACTIVITY_TIMEOUT)
    except Empty:
        if pending.value > 0: paused += INACTIVITY_TIMEOUT; continue   # re-wait, don't die
        cancel.set(); raise TimeoutError(...)                          # genuine inactivity
    if event is None: break
    if (monotonic() - start) - paused > OVERALL_CAP:                   # cap excludes paused
        cancel.set(); raise TimeoutError(...)
    events.append(event)
```

## ALGORITHM — negative control (scenario_baseline_dies)

Without this, "pause survives" is equally compatible with "neither timeout would have fired
anyway" — both pause assertions would be vacuous. Driving the **verbatim (non-pause)** consumer
under identical conditions proves the timeouts are genuinely armed, and substantiates D1's
"keepalives *arm* the cap" rationale.

```
same setup: fresh Gate(), same 5s resolver think-time
drive the VERBATIM run_bridge from _common.py (no pause branch) instead of run_bridge_paused,
  passing inactivity_timeout=INACTIVITY_TIMEOUT and overall_cap=OVERALL_CAP
run.join()
assert isinstance(run.error, TimeoutError)   # the consumer runs on a worker thread, so the raise
                                             # reaches the main thread only via BridgeRun.error
                                             # (Step 2's error channel) — the timeout mechanic
                                             # really does kill the paused turn
```

## DATA

- `PendingCounter` exposes `.value`; `run_bridge_paused` returns `list[StreamEvent]`.
- Prints `PASS: pause-survives-inactivity`, `PASS: pause-survives-overall-cap`,
  `PASS: baseline-without-pause-dies`; exits 0.

## Rejected alternative — record, do NOT implement (D1)

Add a short module docstring / comment block stating why **keepalives** are rejected:
the `_AGENT_OVERALL_TIMEOUT` check sits *inside* the consumer loop (`:524`), so keepalive
events are what **arm** the cap rather than resetting it; keepalives also reach the session
`.jsonl` (`app_core.py:198`) and replay, and add interval-tuning surface. A counter is only
needed for pause. This text is lifted into `FINDINGS.md` in Step 6.

## Definition of done

- `python spikes/i3-1-approval/tier_b_pause.py` exits 0, all PASS lines, repeatable.
- Standard `src`/`tests` fast unit suite still green.
