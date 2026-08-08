# review-plan review log 2

Issue: #1044 — I3.1 Feasibility spike: interceptor ↔ cross-thread Future
Branch: `1044-i3-1-feasibility-spike-interceptor-cross-thread-future` (up to date with `origin/main` @ 988ed1a)

## Round 1 — 2026-08-08

**Findings**:
- `step_1.md:29-31,61-67` — **high** — D5 registry probe bypasses the registry: `resolve_from_thread` receives the `Future` object directly, so the reverse-order scenario only proves two independent Futures resolve independently. It would pass green against a completely cross-wired registry — the exact hazard D5 exists to catch.
- `step_5.md:66-70,90-92` — **medium** — the deny-path `tool_call_id` rebuttal is half-verified. `permission_bridge.py:28` does hardcode `tool_call_id=""` (round 1 of log 1 was factually wrong to demand derivation), but the "ToolNode overwrites it downstream" claim is an inherited docstring assumption nothing verifies, and `scenario_deny` cannot detect it being wrong because `FakeChatModel` never validates the id pairing a real provider API rejects. Adapter source is in the gitignored `.venv`, so it is not confirmable by reading.
- `step_2.md:37-41,91,105,121` — **medium** — module-level mutable `Gate` (class attributes) shared across three scenarios breaks the determinism AC. `scenario_inert` never resolves, so `Gate.fired` stays `True`; `scenario_direct` then passes its wait immediately and resolves against a stale loop/future.
- `step_3.md:12-14` vs `step_2.md:29-30` — **medium** — the shared harness is triplicated and the plan contradicts itself (Step 2 says reused, Step 3 forbids importing). Three hand-maintained copies of the verbatim `__init__.py:479-534` bridge, whose fidelity to production is load-bearing (§10.3).
- `step_3.md:47-56` — **low** — no negative control for the timeout mechanic: "pause survives" is compatible with "neither timeout would have fired anyway".
- `step_4.md:69-74`, `step_6.md:44-48` — **low** — the D7 recommendation omits two frictions: `prompt_llm_stream` is the provider-agnostic interface whose coupling to a langchain-permissions object #1043 D1 explicitly rejected, and `ask_langchain_stream` branches to `_ask_text_stream` when `mcp_config` is absent.
- `step_5.md:18-30` — **low** — an existing working FastMCP stdio server (`tests/llm/providers/claude/_mcp_stub_server.py`, with a `pyproject.toml:235` mypy override) is not referenced as the template.
- `step_2.md:92,124` — **low** — stale `agent.py` line refs (`:572`/`:568`; at HEAD `:569-570`/`:564`).

**Decisions**: all eight accepted as straightforward plan fixes — none changes scope or architecture, so none escalated. F2 accepted in the form "keep `tool_call_id=""`, but make Tier C *prove* the overwrite" rather than re-litigating the message shape. F6 accepted as FINDINGS content only; resolving the `prompt_llm_stream` coupling tension belongs to I3.2, not this spike.

**User decisions**: none required this round.

**Changes**: `step_1.md` registry-lookup resolver; `step_2.md` new `_common.py` split, per-scenario `Gate` dataclass, `FakeChatModel` records per-invoke messages, corrected line refs + "navigate by symbol"; `step_3.md` imports shared harness, per-scenario `Gate`, new `scenario_baseline_dies`; `step_4.md` two D7 frictions recorded; `step_5.md` stub-server template pointer, shared `FakeChatModel`, deny `tool_call_id` assertion + `PASS: deny-tool-call-id-filled`; `step_6.md` §5 frictions and new §10, DoD 9 → 10; `summary.md` `_common.py` in file list; `Decisions.md` created.

**Status**: committed

## Round 2 — 2026-08-08

**Findings**:
- `step_2.md:45` (with `:39-42`) — **high** — the shared `FakeChatModel` specifies only sync `_generate`. `BaseChatModel`'s default `_agenerate` delegates to `run_in_executor(None, self._generate, ...)`, so it runs on a thread-pool thread with **no running loop**, where `asyncio.get_running_loop()` raises `RuntimeError`. That destroys `model.loop_id` — the independent agent-loop reference `step_5.md:94-96` compares `gate.loop_id` against, and on which `step_6.md:14-20` gates the entire positive go/no-go verdict.
- `step_3.md:73-75` vs `step_2.md:68-90` — **medium** — `scenario_baseline_dies` (F5) is unwritable as specified: `run_bridge` has no timeout parameters (and Step 2's `scenario_inert` needs a *long* one, so a hardcoded short value breaks it), and `BridgeRun` has no error channel, so the `TimeoutError` raised on the worker thread never reaches the main thread.
- `step_2.md:80,124` — **medium** — `BridgeRun.close()` while the consumer is blocked raises `ValueError: generator already executing`; CPython refuses `gen.close()` while the frame is executing, and the worker thread in `q.get(...)` *is* executing it. `GeneratorExit` is not merely inert — it is unrequestable.
- `step_2.md:31,148-150` — **medium** — `scenario_backstop` needs tool_call(blocking) → tool_call(instant) → `'done'`, contradicting `_common.FakeChatModel`'s documented 2-invoke script; "Configure `FakeChatModel` to …" assumes a knob the signature block does not have. Loose end from the F4 extraction.
- `step_5.md:112` vs `:132` and `step_6.md:53-59` — **medium** — the deny-`tool_call_id` probe is a gating `assert`, but Step 6 §10 calls its failure a valid recorded finding; the run cannot both fail and be the deliverable. Not hypothetical: `BaseTool._format_output` returns `ToolOutputMixin` instances unchanged and `ToolMessage` is one, so the empty id may survive `ToolNode`.
- `step_5.md:37-45` — **low** — `_common.Gate` and `tier_c.Gate` collide, defended only by a "never import `*`" comment; and `tier_c.Gate` declares only `fired`/`loop_id` while `:95` requires a resolver thread to approve "the pending Future".

**Decisions**: all six accepted as straightforward fixes inside the existing structure — none changes scope, tiering, or a settled decision, none needs a dependency/config change, none escalated. F13 accepted in the reviewer's form (recorded probe, exit 0 either way) because it matches §10.3's "demonstrated working **or** documented-impossible with rationale"; every other Step 5 assertion stays gating. F14 accepted as a rename rather than a documented hazard (KISS).

**User decisions**: none required this round.

**Changes**: `step_2.md` async `_agenerate` + `responses` script + `run_bridge` timeout params + `BridgeRun.error` + `ValueError` assertion; `step_3.md` baseline control passes timeouts and asserts via the error channel; `step_5.md` `InterceptorGate` rename with `loop`/`future` fields + deny probe demoted to recorded observation with explicit DoD exception; `step_6.md` §4 "unreachable while blocked", §10 records whichever outcome occurred; `Decisions.md` F9–F14 appended. `summary.md` needed no change.

**Note**: the apply agent was interrupted by an API error after F9–F12 and was resumed from its transcript to complete F13–F14; the resumed run verified F9–F12 had landed coherently and appended `Decisions.md` once, without duplicates.

**Status**: committed

## Round 3 — 2026-08-08

**Findings**:
- `step_2.md:195-199` (`scenario_backstop`) — **high** — the D2 part-(c) backstop proof is non-deterministic *and* asserts a factually wrong discriminator. (a) "stream ended before the final 'done' event" is false: `cancel_event` breaks the loop at `agent.py:569-570`, the `break` exits the `try` normally and falls through to history reconstruction, and `agent.py:698` yields `{"type": "done", …}` **unconditionally** — a cancelled run still emits it. (b) `cancel_event` is set only after the main thread observes the first `tool_result`, by which time the agent thread has already run invoke 2 → instant tool → invoke 3 → stream end with no waits, so the flag lands after the run is over. Predictably red, not merely flaky. Risk: the implementer weakens the assertion to something equally true of `scenario_direct`, voiding the AC.
- `step_2.md:112-122` with `:149-167` — **low** — `run_bridge`'s spike-invented worker thread is never stated to be a daemon. `scenario_inert` deliberately abandons its run, leaving the worker in the copied `q.get(timeout=300.0)` (F10's long default must stay long); a non-daemon worker is joined at interpreter shutdown, hanging `python tier_b_cancel.py` ~300s and contradicting the "exits 0, repeatable" DoD.
- `summary.md:116` — **low, consistency** — still phrases the deny probe as a single expected outcome rather than F13's two-valid-outcomes recorded probe.
- `summary.md:75` — **low, consistency** — the documented fast-suite marker exclusion list omits `jenkins_integration`, `copilot_cli_integration`, `llm_integration`, `textual_integration`.

**Decisions**: all four accepted; none escalated. For F15 the reviewer offered two restructurings — took the **simpler** one (single `Gate`: set `cancel_event` while blocked, then resolve, break on the first event after resume) over the two-gate variant, per the "default to simpler plans" rule. It is also a tighter mirror-image of `scenario_inert`: same flag, inert while blocked, live once resolved. Mandated that the new discriminator must not be the absence of the `done` StreamEvent. Consequence: `scenario_backstop` reverts to the default 2-entry `responses` script (the `FakeChatModel(responses=…)` constructor from F12 stays — Step 5 still uses it).

**User decisions**: none required this round.

**Changes**: `step_2.md` single-gate `scenario_backstop` with `invoke_count`-based discriminator + explicit "do not assert absence of `done`" note + `AIMessage("done")` vs `{"type": "done"}` disambiguation + `run_bridge` worker documented `daemon=True`; `step_5.md` resume assertion no longer keys on the "final 'done' event"; `summary.md` deny-probe wording and marker list; `Decisions.md` F15–F18 appended and F12's row amended so no live "3-entry script" claim remains.

**Note**: the round-3 reviewer misreported HEAD as `423a17f`; actual HEAD was `e227755`. Its file-content verification was against the correct (current) files, so the findings stand.

**Status**: committed

## Round 4 — 2026-08-08

**Findings**: none.

**Decisions**: n/a.

**User decisions**: none required.

**Changes**: none — F15–F18 verified landed correctly and coherently. `scenario_backstop`'s single-`Gate` restructuring is consistent with `scenario_inert`, `scenario_direct`, the default 2-entry `FakeChatModel` script and Step 6 §4; no live "3-entry script" claim survives; the `daemon=True` worker, the two-outcome deny-probe wording and the marker list all check out. Load-bearing code references re-verified at HEAD (`agent.py:564/569-570/698`, `__init__.py:479/481/506/515/524/530/534/545`, `mcp_manager.py:52-59`, `permission_bridge.py:28`, `gateway.py:106`).

**Status**: no changes needed

## Final Status

**Rounds run**: 4 (this log) — plus 2 in `plan_review_log_1.md`, six review rounds total on this plan.

**Findings applied this log**: 18 (F1–F18) across three apply rounds, in commits `369b2c1`, `e227755`, `de777b8`. Round 4 produced zero findings, terminating the loop.

**Escalations to the user**: none. Every finding was an implementation-detail correction inside the settled structure — no finding changed scope, tiering, or any decision in D1–D10.

**Requirement changes**: none. Four independent rounds confirmed `langchain-mcp-adapters>=0.3.0`, `langgraph>=1.2.9` and (transitively) `mcp`/FastMCP are already pinned in `pyproject.toml`, and that D8's confirm-only stance holds — `testpaths = ["tests"]` and CI passing `src tests` explicitly mean `spikes/` needs no configuration work. No `pyproject.toml` or CI edit should be pulled forward into planning.

**Substantive corrections made** (the ones that would otherwise have shipped a vacuous proof):
- **F1** — the D5 registry probe resolved Futures by object, so it would have passed green against a completely cross-wired registry. Now resolves by `approval_id` lookup inside the thread.
- **F9** — the shared `FakeChatModel` implemented only sync `_generate`; `BaseChatModel`'s default `_agenerate` would have run it on a thread-pool thread with no running loop, destroying `model.loop_id` and with it the D6 identity comparison the entire positive go/no-go verdict is gated on.
- **F15** — the D2 part-(c) backstop scenario was racy *and* keyed on the absence of a `done` StreamEvent that `agent.py:698` emits unconditionally even after a cancel break. Restructured to a single `Gate` mirroring `scenario_inert`.
- **F13** — the deny-`tool_call_id` probe was a gating assert whose failure Step 6 itself called a valid recorded finding; now a recorded probe (exit 0 either way), matching §10.3.

**Known residual uncertainty** (by design, not a defect): the "langgraph `ToolNode` overwrites `tool_call_id`" claim inherited from I2.3's docstring cannot be verified by reading — the adapter source is in the gitignored `.venv`. F2/F13 turn it into an empirical probe with two valid outcomes; a negative is simultaneously a finding for I3.2 and a latent bug in shipped I2.3 code.

**Verdict**: the plan is converged and **ready for approval**.
