# FINDINGS — I3.1 feasibility spike: interceptor ↔ cross-thread Future (#1044)

**Deliverable of a throwaway spike.** This file is the entire product of #1044. I3.2 (#1045) reads
it, carries the load-bearing rationale into its production code (docstrings/comments), then deletes
`spikes/i3-1-approval/` (D9). No production code shipped from this issue.

The spike answers one go/no-go question: *does the interceptor's `await future` run on the agent's
`asyncio.run(_run())` loop — distinct from the MCPManager daemon loop — and can a bare UI thread
resolve that Future cross-thread?* It also demonstrates each in-scope approval mechanic (#1–#5) has
a real outcome (works / documented-impossible-with-rationale), so I3.2 starts de-risked.

## Environment these outcomes were observed on

| Package | Version |
|---------|---------|
| langchain-mcp-adapters | 0.3.2 |
| langchain-core | 1.5.5 |
| langgraph | 1.2.11 |
| mcp | 1.29.0 |

Platform: Windows 10, CPython 3.11 venv (`.venv`). All five scripts are deterministic and exit 0 on
repeat; the loop-mechanics proofs require the **real** langchain/langgraph (never the repo test
conftest's stub classes).

### Aggregate outcomes (last re-run, all exit 0)

```
tier_a.py        PASS: loop-identity / cross-thread-resolve / deny / cancel / registry-no-cross-wiring
tier_b_cancel.py PASS: generic-paths-inert / direct-resolve-unblocks / thread-terminated / backstop-fires-after-resolve
tier_b_pause.py  PASS: pause-survives-inactivity / pause-survives-overall-cap / baseline-without-pause-dies
tier_d7_seam.py  PASS: attach-detach-lifecycle / stale-q-failure-reproduced / side-channel-emit-reachable
tier_c.py        PASS: interceptor-fired / loop-identity-real-path (agent≠daemon) / resume-past-gate / deny-shape
                 OBSERVED: deny-tool-call-id-empty (finding for I3.2 / latent I2.3 bug) [ToolNode did NOT fill it -> langgraph INVALID_CHAT_HISTORY]
                 OBSERVED: deny-path-wedges-agent (empty tool_call_id -> unpaired history -> invoke_count=1)
```

Per-gotcha demonstrated-outcome ("de-risked" = every mechanic has an outcome, not "all green"):

| # | Mechanic | Outcome |
|---|----------|---------|
| 1 | Cross-thread Future affinity + loop identity by object (D6) | **works** — Tier A + Tier C |
| 2 | Side-channel `approval_request` reachable off the `q` | **works** — Tier D7 |
| 3 | Cancel-while-pending via generic paths | **documented-impossible** (all three inert/unreachable) → direct channel **works** — Tier B cancel |
| 4 | Pause survives both timeouts (pause > keepalives, D1) | **works**, negative control confirms non-vacuous — Tier B pause |
| 5 | Deny `ToolMessage` shape + `tool_call_id` fill | shape **works**; empty-id fill **documented-impossible** (latent bug) — Tier C |

---

## 1. Go/no-go verdict — **POSITIVE (GO)**

Tier C (`tier_c.py::scenario_resume`) passed all three D6 identity conditions on the **real**
langchain-mcp-adapters call path, using an *independent* agent-loop reference:

- `gate.loop_id == model.loop_id` — the interceptor coroutine ran on the **agent loop**, proven
  against `FakeChatModel.loop_id` (an independent handle captured inside `_agenerate` on the agent's
  `asyncio.run` loop), not merely "the resolve worked" (D6: a working resolve only proves the guess
  was right; the identity comparison is what makes it a positive verdict).
- `gate.loop_id != daemon_loop_id` — that loop is **distinct** from the `MCPManager` daemon loop
  (`id(manager._loop)`). Observed distinct ids, e.g. `agent=…832 daemon=…768`.
- A **bare resolver thread** unblocked the awaiting Future via `loop.call_soon_threadsafe(...)`, and
  the agent then proceeded past the gate (real MCP `tool_result` echoing `text="spike"` + the fake's
  final `'done'` text; `invoke_count == 2`).

The interceptor also demonstrably **fired** with the model stubbed (`gate.fired is True`), so the
gating hook is real, not bypassed.

**Conclusion: the I3.2 in-band approval design is feasible as specified — proceed.**

### D10 fallbacks — **moot / not needed** (listed for completeness per the AC)

D10 requires a *negative* verdict to name and rank fallbacks. The verdict is positive, so these are
**not needed**; recorded only so the ranking exists if I3.2 hits an unforeseen blocker:

1. langgraph checkpointer + `interrupt()` (durable pause/resume via graph interrupts).
2. `HumanInTheLoopMiddleware` via the `langchain` meta-package (note: that meta-package is **not**
   currently installed in this venv — adopting it is a new dependency decision).
3. Out-of-band approval before turn start (pre-authorize tools; no mid-turn interception).

---

## 2. Loop-handle source (the whole point)

Always obtain the agent-loop handle with **`asyncio.get_running_loop()` inside the interceptor
coroutine**. **Never** reuse a build-time handle captured on the `MCPManager` daemon loop or at
gateway construction. Evidence: Tier A proves a Future is bound to its creating loop and a foreign
thread can only complete it through `call_soon_threadsafe`; Tier C proves the loop seen *inside* the
interceptor is the agent loop and is a different object from the daemon loop. A build-time handle
would target the wrong loop and the cross-thread resolve would silently never wake the coroutine.

---

## 3. Pause vs keepalives (D1) — pause **works**; keepalives **rejected**

Tier B pause (`tier_b_pause.py`) drives a pause-aware copy of the production consumer. A tool that
pauses 5s — longer than **both** the 2s inactivity `q.get(timeout=…)` **and** the 3s overall cap —
still completes, because a thread-safe **pending counter** re-waits on `queue.Empty` while
`pending.value > 0` and the cap is computed over `elapsed − paused`. A **negative control**
(`scenario_baseline_dies`) runs the *verbatim* (non-pause) consumer under identical conditions and
raises `TimeoutError`, so the pause is load-bearing, not vacuous.

**Keepalives are rejected** as the pause mechanism: the `_AGENT_OVERALL_TIMEOUT` check sits *inside*
the consumer loop (`llm/providers/langchain/__init__.py`, the `:524` region), so keepalive events
**arm** the cap rather than resetting it — the negative control substantiates exactly this (events
flowing through the loop trip the cap). Keepalives also pollute the session `.jsonl` / replay
(`app_core.py:198`) and add an interval-tuning surface. A counter is only needed for pause.

---

## 4. Direct cancel channel (D2) — the three generic paths are unusable while blocked

Tier B cancel (`tier_b_cancel.py::scenario_inert`) proves all three generic cancel paths are inert
or unreachable while the tool is blocked on the Future:

- **`cancel_event`** (`agent.py`, the `:569-570` region) is checked only *between* `astream_events`
  iterations; no events flow while blocked, so setting it does nothing.
- **TUI `_cancel_event`** (`ui/app.py:290` region) is checked only *after* an event arrives from the
  generator; none arrives while blocked, so it never wakes.
- **`GeneratorExit`** is **unreachable**, not merely inert (F11): the only thread that could close
  the consumer generator is the one stuck inside `next()`/`q.get(...)`, and CPython refuses
  `gen.close()` on an executing frame — `scenario_inert` asserts the exact
  `ValueError: generator already executing`.

The working unblock is the UI calling the engine **directly** to resolve/cancel the Future —
**pushed** via `call_soon_threadsafe`, never polled (`scenario_direct`). The generic paths still
work as a **backstop** *after* resolve (`scenario_backstop`: `cancel_event` set while blocked
becomes live on the first event after resume and breaks before the 2nd model invoke —
`invoke_count == 1`). Note the discriminator is *not* the absence of the `{"type":"done"}`
StreamEvent — `agent.py:698` yields that unconditionally even for a cancelled run (F15). After the
real 5s `thread.join`, the agent thread is genuinely dead (`is_alive() is False`) — but only once the
Future resolves.

---

## 5. D7 plumbing shape

Tier D7 (`tier_d7_seam.py`) models the seam standalone (D7 = "recorded as a recommendation; nothing
ships"). The recommendation for I3.2: thread an `ApprovalBridge` (wrapping the per-turn `queue.Queue`)
through `prompt_llm_stream → ask_langchain_stream → _ask_agent_stream`, **attached/detached per stream
in `try/finally`**. The parameter must stay **optional** — non-iCoder CLI paths call
`ask_langchain_stream` without it and must keep working.

**Stale-`q` failure mode to guard against** (demonstrated in `scenario_stale_q`): if a turn's bridge
is never detached, the next turn — beginning without attaching a fresh bridge — reads the gateway and
wrongly targets the *previous* turn's queue. The `try/finally` detach is what prevents this.

**Two frictions I3.2 will hit cold — named, not resolved here (resolution is I3.2's, F6):**

- **(a) Provider-agnostic-interface tension.** `prompt_llm_stream` (`src/mcp_coder/llm/interface.py`,
  `provider: str = "claude"` default) is the **provider-agnostic** interface, and I2.3 / #1043 D1
  **explicitly rejected** threading a langchain-permissions object through it — which is exactly what
  D7 prescribes. This coupling tension is real and unresolved.
- **(b) The no-MCP branch the parameter must cross.** `ask_langchain_stream`
  (`llm/providers/langchain/__init__.py`, the `:545` region) branches to `_ask_text_stream` when
  `mcp_config` is absent — the bridge parameter has to traverse that path as a **no-op**.

(Cite both by **symbol**; line numbers drift.)

---

## 6. Side-channel / replay consequence

The `approval_request` `StreamEvent` reaches the interceptor through the existing per-turn `q` — Tier
D7 `scenario_side_channel` puts a real `approval_request` event onto a real `queue.Queue` from inside
the interceptor and `get()`s it straight back, so the side channel is genuinely reachable (not just
asserted in prose). **Consequence for I3.2:** every non-`raw_line` StreamEvent is written to the
session `.jsonl` at `app_core.py:198` and re-rendered by `ui/replay.py`. An `approval_request` event
sent through `q` will therefore be **persisted and replayed** — I3.2 must decide whether approval
prompts belong in session history / replay and handle them accordingly.

---

## 7. Textual thread directions for I3.3

The modal approval callback runs on the **Textual UI thread**. The two marshalling primitives point in
**opposite directions** — do not reach for the wrong one:

- **`call_from_thread`** marshals *into* Textual (a worker/agent thread → the Textual event loop, e.g.
  to update the modal).
- **`call_soon_threadsafe`** marshals *out to the agent loop* (the Textual thread → the agent's
  `asyncio.run` loop, to resolve the pending Future).

So when the user clicks approve/deny on the Textual thread, I3.3 resolves the interceptor's Future
with **`agent_loop.call_soon_threadsafe(future.set_result, decision)`**, not `call_from_thread`.

---

## 8. D8 consequence — `spikes/` is outside CI

Confirmed by inspection (no config changed):

- `pyproject.toml` `[tool.pytest.ini_options] testpaths = ["tests"]` → `spikes/` is **never
  collected** by pytest.
- `.github/workflows/ci.yml` passes **`src tests` explicitly** to black, isort, pylint, ruff, and
  `mypy --strict`; import-linter / tach / pycycle / vulture run via `./tools/*.sh` scoped to the
  `mcp_coder` package / `src`/`tests`. None reach `spikes/`.

**Consequence carried into I3.2:** spike code is neither linted nor type-checked, so anything I3.2
lifts out of these fixtures (e.g. the verbatim bridge copy, `FakeChatModel`, the interceptor gate)
must be **rewritten to survive `mypy --strict`** and the project's ruff/pylint gates — the spike's
`# type: ignore` shims and untyped signatures will not pass as-is.

---

## 9. D9 handoff contract

I3.2 (#1045) **reads this file**, carries the load-bearing rationale into its production code
(docstrings/comments — especially the loop-handle rule §2, the direct-cancel rationale §4, the D7
seam shape §5, and the deny-path fix §10), then **deletes `spikes/i3-1-approval/`**. The spike is
consumed and removed; nothing in it ships.

---

## 10. Deny-path `tool_call_id` — **OBSERVED: empty (latent I2.3 bug)**

`build_deny_tool_message` (`permission_bridge.py:28`) constructs the deny `ToolMessage` with
`tool_call_id=""`, and its docstring (`:22-24`) claims *"langgraph's `ToolNode` overwrites it with the
real call id downstream."* Tier C's **recorded probe** (F13 — not a gating assert; Tier C exits 0
either way) turns that inherited assumption into an observed fact by comparing the post-`ToolNode`
`ToolMessage.tool_call_id` against the id the fake model emitted (`call_1`).

**Recorded outcome on this stack:**

```
OBSERVED: deny-tool-call-id-empty (finding for I3.2 / latent I2.3 bug)
          [ToolNode did NOT fill it -> langgraph INVALID_CHAT_HISTORY]
OBSERVED: deny-path-wedges-agent (empty tool_call_id -> unpaired history ->
          agent does NOT continue past deny; invoke_count=1)
```

The docstring claim is **FALSE**: `ToolNode` does **not** overwrite the empty id (consistent with
`langchain_core.BaseTool._format_output` returning `ToolOutputMixin` instances — and `ToolMessage`
*is* one — unchanged). The empty `tool_call_id` leaves the agent's `ping`/`call_1` tool_call
**unpaired**, so `create_react_agent` raises `INVALID_CHAT_HISTORY` on the next turn and the deny path
**wedges the agent** (`invoke_count` stays 1). This is simultaneously:

- a **finding for I3.2 (#1045)**: the fix is to set the **real `tool_call_id`** on the deny
  `ToolMessage` (from the intercepted request's tool_call id) instead of `""`; and
- a **latent bug in already-shipped I2.3 code (#1043)**: a real provider API rejects an unpaired
  `ToolMessage`, which `FakeChatModel` never validates — so nothing in the current test suite catches
  it.

**Gotcha — the bug hides in the stream but shows in state:** `run_agent_stream` cosmetically masks the
empty id in the *stream* event (the deny `tool_result` StreamEvent uses `run_id`), while the langgraph
*state* `ToolMessage` keeps `""`. The defect only surfaces in state/history validation, not in the
stream — so a stream-only test would miss it.

Per §10.3, a negative here is a valid "documented-impossible with rationale" outcome, **not** a
failed spike.

---

## Tier-C gotchas worth recording for I3.2

Small facts that cost time to rediscover:

1. **Stubbed `_agenerate`-only model emits no `text_delta`.** With `_agenerate` but no `_astream`,
   langchain falls back to a single non-streaming `ainvoke` and emits no `on_chat_model_stream`, so
   the driver yields no `text_delta`. The final assistant text only appears on the
   `on_chat_model_end` event, mirrored verbatim as a `raw_line` (`json.dumps(..., default=str)`) —
   assert `content='done'` there, not as a `text_delta`.
2. **Tool args must satisfy the tool schema or the interceptor never fires.** langgraph's `ToolNode`
   validates the tool_call against the tool schema **before** the tool coroutine (and therefore the
   interceptor) runs. Tier C's real `ping(text)` needs `args={"text": …}`; an empty `args` would fail
   validation and the interceptor would never fire. (Tier B's no-arg blocking tool uses `args={}`.)
3. **Model runs on `_agenerate`, not `_generate`.** `BaseChatModel`'s default `_agenerate` delegates
   to `run_in_executor(None, self._generate, …)` — a thread-pool thread with **no running loop**,
   where `asyncio.get_running_loop()` raises `RuntimeError` and the independent loop reference is
   destroyed. The fake must implement the async `_agenerate` to capture `loop_id` on the agent loop.
4. **`run_agent_stream` writes session history** to `~/.mcp_coder/sessions/langchain/` — the spike
   passes throwaway `session_id`s; I3.2's tests should expect (or isolate) these writes.
5. **Navigate production refs by symbol, not line** — every `__init__.py` / `agent.py` /
   `permission_bridge.py` / `app_core.py` reference above drifts; the symbol names are stable.
