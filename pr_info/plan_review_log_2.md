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
