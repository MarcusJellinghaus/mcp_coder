# I3.2 — Runtime approval engine + two-loop bridge (#1045)

Implementation summary for the M3 in-band approval engine on the **langchain provider only**.

**Read first:** epic #1038, design reference #1037 (§8.1 gotchas #1–#5, §8.3, §10.2 D-E/D-K,
§10.6.2 D-N), issue #1045 (all refinement passes: R1–R18), sibling #1046 (I3.3),
`spikes/i3-1-approval/FINDINGS.md` (deleted by Step 8 of this plan).

---

## 1. Goal

Replace I2.3's placeholder `AFTER_APPROVAL` → deny branch with a real in-band pause:

1. The call-level interceptor registers an `asyncio.Future` **on the agent loop**.
2. It emits an `approval_request` `StreamEvent` through the existing per-turn queue.
3. It `await`s the human decision, then **runs** (allow), returns a clean
   `ToolMessage(status="error")` (deny), or unwinds the turn (cancel).

The modal that *answers* is I3.3/#1046. This plan builds the engine, the seam, the two-loop
bridge, and everything the pause breaks: the two timeouts, the three inert cancel paths,
replay/persistence, session-record gating, and tool-unit pairing.

---

## 2. Architectural / design changes

### 2.1 Two new modules, split at the layer boundary (R6)

`layered_architecture` places `mcp_coder.icoder` **above** `mcp_coder.llm`, so
`_ask_agent_stream` cannot import a type from `icoder/permissions/`. Hence:

| Module | Layer | Contents | Hard constraint |
|---|---|---|---|
| `llm/providers/langchain/approval_bridge.py` | `llm` | `ApprovalBridge` Protocol: `attach(emit)` / `detach()` / `pending()` | **No langchain import at any scope** — grimp records function-level imports as edges |
| `icoder/permissions/approval.py` | `icoder` | `ApprovalDecision`, `ApprovalEngine` | Added to `permissions_leaf_isolation`; **never** imports `permission_bridge`, Textual, or `AppCore` |

The deny `ToolMessage` is constructed in `gateway.py` (which is excluded from the contract),
never in the engine. Keeping the engine inside `permissions/` makes "the engine never grows a
Textual handle" **machine-enforced on every CI run** — that is what protects R2.

### 2.2 The engine is one insertion-ordered dict (KISS simplification)

The registry is mutated from the **agent loop** in the normal case: interceptor coroutines run
there, and `resolve_pending` / `cancel_all` only ever hand their bodies over with
`call_soon_threadsafe`. Three members are touched **off** that loop, and the docstring must say
so rather than claim blanket single-threadedness:

* `attach()` / `detach()` mutate `_pending`, `_emit`, `_loop` (and `_cancelled`, on `attach`)
  from the **consumer thread** — `_ask_agent_stream`'s body and its `finally`. `detach()` is
  *not* guaranteed to run after the agent loop is dead: it follows `thread.join(timeout=5)`, and
  that join can expire with the loop still live (§2.3);
* `cancel_all()` sets `_cancelled = True` on the **Textual thread** before scheduling the future
  cancellations onto the loop;
* `pending()` is read cross-thread from the consumer thread.

Each of those is one attribute rebind or a `len(dict)` read — atomic under the GIL — so no lock
is needed. Two consequences must be *coded*, not assumed:

* the `finally: _emit_front()` in `request_approval` guards on `self._emit is None`: after a
  `detach()` that raced an expiring join, the sink is gone and promoting the next entry must be
  a no-op rather than an `AttributeError` on a dead turn;
* `detach()` **cancels** the futures it drops (§2.3) instead of merely clearing them.

Consequence: **no lock, no deque, no separate counter.** One `dict[approval_id → _PendingApproval]`
is simultaneously the registry, the FIFO arrival order (dicts are insertion-ordered), and the
pending count. Serialisation is achieved by emitting only for the front entry:

* the dict entry is created **before** the emit → R10 is structural, not a rule to remember;
* only one `approval_request` is ever in flight → R3's *guarantee* holds by construction;
* FIFO is asserted against `pending_ids()`, which records **arrival** order (insertion precedes
  any `await`), so the assertion is not circular → R4 satisfied without relying on
  `asyncio.Lock` wake order;
* each caller waits on its **own** future, so cancel needs no special-casing.

> **Documented deviation from R3's mechanism (approved).** R3 says "the serial lock is held
> around the emit". There is no lock in this design; its *guarantee* ("exactly one
> `approval_request` outstanding, so I3.3 renders exactly one modal") is strictly preserved and
> is what the acceptance criterion tests. Record this in the `ApprovalEngine` docstring.

### 2.3 Loop handle, cancel channel, timeouts (carried from FINDINGS)

* **Loop handle** comes from `asyncio.get_running_loop()` *inside* `request_approval`
  (FINDINGS §2). A build-time handle would target the `MCPManager` daemon loop and the
  cross-thread resolve would silently never wake the coroutine. `asyncio.run` runs **per turn**,
  so the loop object differs every turn — this is why `detach()` must clear the registry.
* **Cancel-while-pending uses the direct UI→engine channel** (FINDINGS §4). The three generic
  paths (`cancel_event`, the TUI `_cancel_event`, `GeneratorExit`) are all gated on an event
  arriving from the generator, and a blocked interceptor emits none, so none of them can *trigger*
  a cancel while the consumer sits in `q.get`. They remain wired as a **post-resolution
  backstop** only.
* **`GeneratorExit` while an approval is pending is rare, not impossible — do not design as if it
  cannot happen.** It cannot be raised from the consumer's own `q.get` (CPython refuses
  `gen.close()` on an executing frame), but the consumer is **not** in `q.get` for the whole
  pending window: it yields the `approval_request` and is then suspended at that `yield` while
  the event is handled — `AppCore.stream_llm` passes it to `ui/app.py::_stream_llm`, which
  dispatches through `call_from_thread` and blocks until the UI handler returns. Under
  I3.3/#1046 that is the entire open-modal window. An exception in that handler (or any other
  consumer-side abort) leaves the `for` loop, closes the generator, and delivers `GeneratorExit`
  at the `yield` **with an approval still pending**; that path runs `cancel.set()` →
  `thread.join(timeout=5)` → `detach()`, and the join expires because the agent thread is parked
  on the future. **Required behaviour for that path:** `detach()` cancels every future it is
  about to drop (`call_soon_threadsafe(fut.cancel)`) before clearing `_pending`, so the parked
  interceptor unwinds and the daemon agent thread dies instead of leaking for the process
  lifetime with a future nothing can resolve.
* **Timeout suspension is pause, not keepalives** (FINDINGS §3, D1): the consumer treats
  `queue.Empty` as "re-wait" while `pending() > 0`, and the overall cap compares
  `elapsed − paused`. `paused` is measured from a **timestamped pending window** — the wall time
  between `pending()` going 0→n and back to 0 — **not** accumulated in `queue.Empty` units: with
  iCoder's 300s inactivity timeout and the 3600s cap, an `Empty`-only accumulation credits
  *nothing* for any pause shorter than 300s and charges it in full against the cap, so a turn
  with a few one-minute approvals still trips it. Keepalives *arm* the overall cap (it is checked
  inside the consumer loop after `q.get()` returns) and would reach the session `.jsonl` and replay.

### 2.4 Resolver: `runtime` becomes its own top-priority stage (R14)

`_resolve_config` sorts by `(specificity, policy.rank, _LAYER_ORDER[layer], -index)` — layer is
only the **third** key and `Policy.rank` puts `AFTER_APPROVAL` above `ALWAYS`, so a session grant
`Rule(Matcher("s","t"), ALWAYS, "runtime")` currently **loses** to an authored
`"ask": ["mcp__s__t"]`. Runtime rules now contest among themselves and win **as a group**.
`_LAYER_ORDER` keeps its meaning for the other three layers.

**Bound on the widening (security):** the group short-circuit is skipped when any *authored*
(non-runtime) matching rule is `never`. R14's canonical case is a runtime `always` beating an
authored `ask`; letting a **broad** runtime `always` also shadow a **specific** authored `never`
is a widening this issue does not need. With the bound, an authored `never` falls through to the
ordinary 4-key contest, where it loses only to a *strictly more specific* runtime rule — never to
a broader one. The bound is close to free: `filter_tools` hides `never` tools at turn start from
a snapshot, so a runtime grant cannot make such a tool callable in that turn anyway; without the
bound the resolver would merely disagree with the tool list.

*Ripple to mirror (not implemented here):* this is a semantic change to I2.1/#1041's resolver.
#1048's `/allow` quick commands carry no never-override confirm; with the bound above they do not
need one for the broad-grant case, but the specific-grant case still overrides an authored
`never` — record that in #1048 rather than solving it here.

### 2.5 Degraded config denies outright (R15)

`_resolve_config` short-circuits to `AFTER_APPROVAL` on `config.degraded` **before** consulting
rules. Making the branch real without R15 would mean a modal on *every* MCP call for the whole
session, with no `scope=session` grant able to stop it (the short-circuit precedes rule lookup).
The gateway therefore keeps the whole `Decision` and denies when
`isinstance(decision.source, Degraded)` — no emit. `_resolve_frame`'s "the one place degrade
loosens" docstring becomes false and is corrected in the same change.

*Known gap (accepted):* the user gets **no signal at deny time**. `permission_warning` is
emitted only from the skill-frame loop, and the startup banner is skipped on resume. Do not rely
on "the user is already told".

### 2.6 Runtime-rule store on the gateway; the write is I3.3's (R2/R8)

`PermissionConfig` is frozen, so `add_runtime_rule` is
`dataclasses.replace(config, rules=config.rules + (rule,))` rebound onto one attribute — atomic
under the GIL, no lock. It lives on `LangchainEnforcementGateway`, the only reader of the config.
`AppCore` gains two handles the UI reaches (`approval_engine`, `permission_gateway`) and three
thin delegating methods. The engine **never** writes the layer; I3.3's UI-thread modal callback
does, inline, before calling `resolve_pending`.

### 2.7 `approval_request` is transient (R5)

Every non-`raw_line` StreamEvent is persisted **twice** (session `.jsonl` + `raw_response["events"]`)
and `ui/replay.py` re-feeds it to `_handle_stream_event` — i.e. replay would pop an unanswerable
modal. A shared `_TRANSIENT_EVENT_TYPES` constant in `llm/types.py` replaces the two literal
`!= "raw_line"` checks so they cannot drift.

### 2.8 Cancel-while-pending writes no session record (R16)

Under hard cancel, `agent.py`'s `except Exception` misses `CancelledError`, so the `done` yield is
never reached, `_stream_llm`'s `_cancel_event` check never fires, the consumer loop simply ends,
and `store_session` runs — while an ordinary cancel breaks the loop and never gets there.
`AppCore.stream_llm` therefore consults a per-turn `cancelled` flag on the injected engine and
skips **both** `llm_request_end` **and** `store_session`. Gating only `store_session` is
insufficient: `ui/replay.py` clears `in_flight` on `llm_request_end` and appends the
`— Cancelled —` marker only when `in_flight` is still true at EOF.

> The flag is set by `cancel_all()` and reset by `attach()` — **not** by `detach()`, which runs
> inside `_ask_agent_stream`'s `finally`, i.e. *before* `AppCore.stream_llm` reads it.

### 2.9 Tool pairing gets a real correlation key (R18)

Both tool events already carry `tool_call_id`, but from different sources: `on_tool_start` emits
the langgraph `run_id`, `on_tool_end` emits the **model's `call_N` id** whenever `output` is a
`ToolMessage` (the normal `ToolNode` case). Id-keyed pairing on that field would therefore never
match and would silently degrade to name-FIFO — reproducing the exact defect R1 exists to fix.
A new `tool_run_id` field carries the `run_id` on both events; `tool_call_id` semantics are
untouched (#1118 depends on them, and two existing assertions stay green).

Pairing is id-keyed with a name-FIFO fallback **only when the result carries no `tool_run_id`** —
`claude_code_cli_streaming.py` and `copilot_cli_streaming.py` emit neither field, and replayed
pre-change logs carry neither. When an id *is* supplied and matches nothing pending, the lookup
returns `None` (unpaired: `duration_ms is None`, or the existing "no open tool unit" WARN) rather
than falling through to name-FIFO — falling through there would silently attach the result to
some other call of the same tool, which is precisely the defect R1/R18 exist to fix.
One short module-level function `pop_pending_tool()` serves both sites; `ui/app.py`'s
`_open_tool_units` collapses from `dict[str, deque[str]]` to a single `deque`.

*Not fixed (R17, recorded):* there is **no** correlation key between `approval_request` and the
on-screen tool unit — the interceptor has only the model's `call_N` id. I3.3 must identify the
call by tool name + args, as its own criteria already describe.

### 2.10 Attach/detach: one lifecycle site

The emit sink is `q`, a **local of `_ask_agent_stream`**, so `RealLLMService.stream` cannot reach
it. Attach/detach therefore happens in `_ask_agent_stream`'s existing `try/finally` — the one
already holding `thread.join(timeout=5)`, which runs on both normal completion **and**
`GeneratorExit` (the cancel path). One site, one test. This is the observable requirement of the
`detach()`-clears-the-registry criterion; a second defensive detach in `RealLLMService.stream`
is deliberately **not** added (two lifecycle sites rot).

Because that `finally` is also the `GeneratorExit` path, and `GeneratorExit` *is* reachable with
an approval pending (§2.3), `detach()` must **cancel then clear**: schedule
`fut.cancel` for every remaining entry onto `_loop` with `call_soon_threadsafe`, then drop
`_pending`, `_emit`, `_loop`. Clearing alone would strand the parked interceptor on a future no
longer reachable from any registry, keeping the daemon agent thread alive for the process lifetime.

### 2.11 Interim behaviour until I3.3 lands

Nothing answers an `approval_request` until the modal exists. The `ui/app.py` branch therefore
resolves immediately with a deny — fail-closed, a few lines, replaced by the modal in #1046.
Without it, a live `ask` rule would wedge a turn until the user cancels.

That deny must **not** reach the model as the gateway's R11 user-deny wording ("Tool call denied
by the user…"): no user was asked. `ApprovalDecision` therefore carries an optional `reason`, the
UI passes its own `_DENY_NO_UI` string, and the gateway prefers `decision.reason` over
`_DENY_USER`. #1046 drops the `reason` when a real user answers, and the R11 wording applies again.

---

## 3. Files created / modified

### Created

| Path | Purpose |
|---|---|
| `src/mcp_coder/llm/providers/langchain/approval_bridge.py` | `ApprovalBridge` Protocol (the seam). No langchain import. |
| `src/mcp_coder/icoder/permissions/approval.py` | `ApprovalDecision`, `ApprovalEngine`. |
| `tests/icoder/test_permissions_approval.py` | Engine unit tests (pure asyncio, no langchain). |
| `tests/llm/providers/langchain/approval_harness.py` | Typed fixture: `FakeChatModel` + blocking tool + bridge driver. |
| `tests/llm/providers/langchain/test_approval_cancel_path.py` | R7 probe + real-path cancel regression test. |
| `tests/llm/providers/langchain/test_approval_stream_bridge.py` | Pause / attach-detach / transient-event tests. |
| `tests/llm/providers/langchain/test_approval_integration.py` | End-to-end allow/deny through the real agent path. |
| `tests/icoder/test_approval_wiring.py` | `AppCore` / `RealLLMService` / CLI wiring + R16 gating. |

### Modified

| Path | Change |
|---|---|
| `src/mcp_coder/icoder/permissions/resolver.py` | R14 runtime stage; R15 docstring correction. |
| `src/mcp_coder/icoder/permissions/gateway.py` | Keep the whole `Decision`; real `AFTER_APPROVAL` branch; degraded deny; fail-closed fallback; `add_runtime_rule`. |
| `src/mcp_coder/icoder/core/app_core.py` | `approval_engine` / `permission_gateway` params + 3 delegating methods; `_TRANSIENT_EVENT_TYPES`; R16 gate. |
| `src/mcp_coder/icoder/services/llm_service.py` | `approval_bridge` ctor param, forwarded to `prompt_llm_stream`. |
| `src/mcp_coder/icoder/ui/app.py` | `approval_request` branch; cancel channel; `on_unmount` hook; pairing deque. |
| `src/mcp_coder/cli/commands/icoder.py` | Construct the engine; inject into gateway / service / core. |
| `src/mcp_coder/llm/types.py` | `_TRANSIENT_EVENT_TYPES`; `ResponseAssembler` carve-out; StreamEvent docs. |
| `src/mcp_coder/llm/interface.py` | Optional `approval_bridge` param (langchain only). |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Bridge param + attach/detach; pause-based timeout suspension; `CancelledError` catch. |
| `src/mcp_coder/llm/providers/langchain/agent.py` | Emit `tool_run_id` on both tool events. |
| `src/mcp_coder/llm/formatting/render_actions.py` | Trailing optional `tool_run_id` on `ToolStart` / `ToolResult`. |
| `src/mcp_coder/llm/formatting/stream_renderer.py` | `pop_pending_tool()`; id-keyed pairing; `tool_run_id` on cleanup results. |
| `.importlinter` | `permissions_leaf_isolation` + `layered_architecture` entries. |
| existing test files | `test_permissions_resolver.py`, `test_permissions_gateway.py`, `test_stream_renderer_tool_format.py`, `tests/icoder/test_app_pilot.py`. |

### Deleted

| Path | Reason |
|---|---|
| `spikes/i3-1-approval/` (8 files) | D9 consume-and-delete handoff, after its rationale is carried into code. |

### Explicitly **not** touched

* `src/mcp_coder/icoder/ui/widgets/output_log.py` — `tool_run_id` is declared **last with a
  default**, so its `ToolStart(display_name=…, raw_name="", args=…)` call site still compiles.
* `src/mcp_coder/icoder/ui/replay.py` — it calls `_cleanup_orphan_tools()`, whose signature is
  unchanged.

---

## 4. Step sequence

| Step | Title | Depends on |
|---|---|---|
| 1 | Real-path `CancelledError` probe (**decision gate**) | — |
| 2 | `ApprovalBridge` Protocol + `ApprovalEngine` | 1 |
| 3 | Resolver: `runtime` stage (R14) + degraded docstring | — |
| 4 | Gateway: real `AFTER_APPROVAL` branch + `add_runtime_rule` | 2, 3 |
| 5 | Provider plumbing: bridge param, pause, cancel catch, transient events | 2 |
| 6 | Tool-unit pairing on `tool_run_id` (R18/R1) | — |
| 7 | Wiring: CLI → gateway / service / `AppCore` (+ R16 gate) | 2, 4, 5 |
| 8 | UI branch, cancel channel, shutdown hook, integration test, spike deletion | 7 |

Each step is one commit: tests + implementation + **all** checks green
(`run_pylint_check`, `run_pytest_check`, `run_mypy_check`, plus `lint-imports` where noted).

---

## 5. Standing constraints for every step

* **MCP tools only** for file operations and checks (see `CLAUDE.md`). Git via Bash is allowed.
* Fast test invocation:
  `run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])`
* `mypy --strict` must pass. Anything lifted from `spikes/` was never linted or type-checked —
  rewrite it, do not copy it.
* Navigate production code **by symbol, not by line number**; every line anchor in #1045 has drifted.
* Docstrings on every public symbol (ruff `D`/`DOC` rules are active).
* Carry the load-bearing FINDINGS rationale into code comments where the step says so — that is
  an acceptance criterion (D9), not decoration.
