# Step 9 — Wiring: CLI → gateway / `RealLLMService` / `AppCore` (+ R16 gate, + UI branch)

**Depends on:** Steps 4, 6, 7 (and Step 2, which moved `_handle_stream_event` into
`icoder/ui/stream_view.py`).

One long-lived engine, constructed at startup and injected into all three holders, so the UI can
*reach* it from the modal callback and from cancel — and so a cancelled-while-pending turn
leaves no session record.

**The UI `approval_request` branch ships in this same commit, not in Step 10.** Wiring the engine
is what makes the gateway's `AFTER_APPROVAL` branch actually emit and `await`. If the UI has no
branch yet, the first `ask`-gated tool call wedges the turn **permanently**: the pause suppresses
both the 300s inactivity timeout and `_AGENT_OVERALL_TIMEOUT` (Step 7), `_cancel_event` is inert
because `_stream_llm`'s `for` loop only tests it *after* an event arrives from the generator, and
the Textual thread worker is a non-daemon executor thread, so the app cannot even be quit cleanly.
There is no ordering of these two changes that leaves a usable app in between, so they are one
commit.

---

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/cli/commands/icoder.py` | **modify** — construct + inject |
| `src/mcp_coder/icoder/services/llm_service.py` | **modify** — `approval_bridge` param, forwarded |
| `src/mcp_coder/icoder/core/app_core.py` | **modify** — handles, delegators, R5 carve-out, R16 gate |
| `src/mcp_coder/icoder/ui/stream_view.py` | **modify** — `approval_request` branch (interim deny) |
| `src/mcp_coder/icoder/ui/app.py` | **modify** — cancel channel in `action_cancel_stream` |
| `.importlinter` | **modify** — `layered_architecture` ignore entry |
| `tests/icoder/test_approval_wiring.py` | **create** |
| `tests/icoder/test_icoder_permission_wiring.py` | **modify** — assert the engine reaches all three |
| `tests/icoder/test_app_pilot.py` | **modify** — UI branch + cancel cases |

## WHAT

```python
# services/llm_service.py — RealLLMService.__init__
approval_bridge: ApprovalBridge | None = None      # forwarded to prompt_llm_stream(...)

# core/app_core.py — AppCore.__init__
approval_engine: ApprovalEngine | None = None,
permission_gateway: LangchainEnforcementGateway | None = None,

# core/app_core.py — three thin delegators (the UI's only route to the engine/gateway)
def resolve_pending(self, approval_id: str, decision: ApprovalDecision) -> None: ...
def cancel_pending_approvals(self) -> None: ...
def add_runtime_rule(self, rule: Rule) -> None: ...     # I3.3 calls this on the UI thread

# icoder/ui/stream_view.py
def _handle_stream_event(self, event, *, replay_mode=False) -> None:
    if event.get("type") == "approval_request":
        ...                      # early return, mirroring the permission_warning precedent
        return

# icoder/ui/app.py
def action_cancel_stream(self) -> None:
    """Cancel the stream AND any pending approval (the direct UI→engine channel)."""
```

## HOW

* **`cli/commands/icoder.py`** — inside the existing
  `if provider == "langchain" and mcp_config:` block, next to the gateway:
  `approval_engine = ApprovalEngine()`, passed to `LangchainEnforcementGateway(config,
  approval_engine)`. Keep the `ApprovalEngine | None` variable hoisted to outer scope like
  `gateway` and `permission_degraded` already are, then pass it to `RealLLMService(...)` and
  `AppCore(...)`. One instance, three references.
* **`.importlinter`** — add
  `mcp_coder.cli.commands.icoder -> mcp_coder.icoder.permissions.approval` to
  `layered_architecture`'s `ignore_imports` (`cli` and `icoder` share one layer line, so every such
  import is whitelisted individually). Add it in **this** step, where the import first exists.
* **`RealLLMService.stream`** — pass `approval_bridge=self._approval_bridge` to
  `prompt_llm_stream`. **Do not** add an attach/detach `try/finally` here: the sink is `q`, a local
  of `_ask_agent_stream`, and Step 7 already owns the single lifecycle site (summary §2.10).
* **`AppCore.stream_llm`** — two edits:
  1. the event-log carve-out becomes
     `if event.get("type") not in TRANSIENT_EVENT_TYPES:` (imported from `llm.types`, the shared
     constant from Step 7);
  2. gate the tail on the engine's per-turn flag:
     ```python
     if self._approval_engine is not None and self._approval_engine.cancelled:
         return                       # no llm_request_end, no store_session (R16)
     self._event_log.emit("llm_request_end")
     store_session(...)
     ```
     Comment **why both**: `ui/replay.py` clears `in_flight` on `llm_request_end` and appends the
     `— Cancelled —` marker only when `in_flight` is still true at EOF, so gating only
     `store_session` would make this turn the one cancel that replays without a marker.
* All three `AppCore` delegators are no-ops when their handle is `None` (non-langchain providers
  construct neither engine nor gateway).
* `AppCore` must **not** import `textual`; it does not today and must not start.
* **`ui/stream_view.py` — `approval_request` branch** (kept in this commit so none ships a
  wedgeable app). Copy the shape of the existing `permission_warning` early return at the top of
  `_handle_stream_event`. Until I3.3/#1046 lands, resolve immediately and fail-closed:

  ```python
  _DENY_NO_UI = (
      "This tool requires approval, but the approval prompt is not available yet, "
      "so the call was refused without asking the user. Choose a different approach "
      "or ask the user how to proceed."
  )

  approval_id = str(event.get("approval_id", ""))
  # I3.3/#1046 replaces this with the modal (ModalScreen[ApprovalDecision]).
  # Until then, fail closed: a live `ask` rule would otherwise wedge the turn.
  # Its own `reason` — never the gateway's R11 user-deny wording, because no user
  # was asked and the model must not be told one refused (summary §2.11).
  self._core.resolve_pending(
      approval_id, ApprovalDecision("deny", "once", reason=_DENY_NO_UI)
  )
  return
  ```

  Mark it with a `TODO(#1046)`. Importing `ApprovalDecision` from `icoder.permissions.approval`
  into `icoder.ui` is legal (the leaf contract forbids the *reverse* direction).
* **`ui/app.py` — cancel channel.** `action_cancel_stream` keeps `self._cancel_event.set()` **and**
  adds `self._core.cancel_pending_approvals()`. Comment why (FINDINGS §4): all three generic paths
  are gated on an event arriving from the generator, and a blocked interceptor emits none, so none
  of them can *trigger* a cancel while the consumer is waiting in `q.get`. They stay wired as the
  post-resolution backstop. Do **not** write that `GeneratorExit` is unreachable while an approval
  is pending (summary §2.3) — it is reachable at the `yield` that delivered the event, and
  `detach()`'s cancel-then-clear covers it.
* **Do not** add a modal, scopes, or any persist write-back — that is #1046. The `on_unmount`
  shutdown hook stays in Step 10; with the interim auto-deny above, no approval is ever left
  pending across a quit in this commit. Consequence for Step 10: its R9 pilot test must suppress
  this auto-deny (monkeypatching `AppCore.resolve_pending` to a no-op) to reach the pending state
  at all — see `step_10.md` test 1.

## ALGORITHM

```python
# cli/commands/icoder.py (inside the existing langchain+mcp_config gate)
config = load_permission_config(project_dir)
approval_engine = ApprovalEngine()
gateway = LangchainEnforcementGateway(config, approval_engine)
mcp_manager = MCPManager(server_config, tool_interceptors=[gateway.interceptor])
...
llm_service = RealLLMService(..., gateway=gateway, approval_bridge=approval_engine)
app_core   = AppCore(..., approval_engine=approval_engine, permission_gateway=gateway)
```

## DATA

* `AppCore.resolve_pending` / `cancel_pending_approvals` / `add_runtime_rule` all return `None`.
* The engine instance is shared by reference across gateway, service and core — assert **identity**
  (`is`) in the wiring test, not equality.
* `cancelled` survives `detach()` and is reset by the next `attach()` — that ordering is exactly
  what makes the R16 gate readable after the generator has finished (summary §2.8).

## TESTS (write first)

1. **Identity wiring:** the CLI builds **one** `ApprovalEngine`, and gateway / service / core all
   hold the same object (`is`).
2. **Non-langchain / no-mcp_config:** engine and gateway stay `None`; `AppCore` delegators are
   safe no-ops; `RealLLMService` passes `approval_bridge=None`.
3. **`RealLLMService.stream` forwards** `approval_bridge` to `prompt_llm_stream` (monkeypatch and
   assert on the kwarg).
4. **R16 — cancelled turn stores nothing:** with a fake engine reporting `cancelled=True`,
   `AppCore.stream_llm` emits **no** `llm_request_end` and calls **no** `store_session`.
5. **R16 — normal turn unchanged:** `cancelled=False` (and engine `None`) both store as today.
6. **R5 — event-log carve-out:** an `approval_request` in the stream is **absent** from the session
   `.jsonl`; `raw_line` exclusion still holds; every other event type is still logged.
7. **`scope=session` end to end (engine-free):** `AppCore.add_runtime_rule(...)` →
   `gateway.interceptor` resolves `ALWAYS` for that tool on a **subsequent** turn.

UI (`tests/icoder/test_app_pilot.py`, `textual_integration`):

8. An `approval_request` event routes to `resolve_pending` with a deny carrying `_DENY_NO_UI` and
   renders nothing; `ResponseAssembler` and the event log are unaffected.
9. `action_cancel_stream` calls `cancel_pending_approvals()` **and** sets `_cancel_event`.

## CHECKS

`run_pylint_check`, `run_mypy_check`, `run_pytest_check` (fast selection) **plus**
`run_pytest_check(markers=["textual_integration"], extra_args=["-n","auto"])` for the pilot tests,
**plus** `run_lint_imports_check` **plus the file-size gate**
(`check_file_size(max_lines=750)` must not list `icoder/ui/app.py` or `icoder/ui/stream_view.py`)
— all green.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (§2.6, §2.7, §2.8, §2.10) and `pr_info/steps/step_9.md`, then
> implement Step 9 only.
>
> Construct **one** `ApprovalEngine` in `src/mcp_coder/cli/commands/icoder.py` beside the gateway
> (inside the existing `provider == "langchain" and mcp_config` gate) and inject the same instance
> into `LangchainEnforcementGateway`, `RealLLMService` (as `approval_bridge`, forwarded to
> `prompt_llm_stream`) and `AppCore` (as `approval_engine`, alongside a `permission_gateway`
> handle). Add `mcp_coder.cli.commands.icoder -> mcp_coder.icoder.permissions.approval` to
> `layered_architecture`'s `ignore_imports` in `.importlinter`.
>
> Give `AppCore` three thin delegating methods — `resolve_pending`, `cancel_pending_approvals`,
> `add_runtime_rule` — each a safe no-op when its handle is `None`. In `AppCore.stream_llm`,
> replace the `!= "raw_line"` event-log check with the shared `TRANSIENT_EVENT_TYPES` constant
> from `llm/types.py`, and skip **both** `llm_request_end` **and** `store_session` when the
> injected engine reports `cancelled` — with a comment explaining that `ui/replay.py` keys its
> `— Cancelled —` marker off `in_flight`, so gating only `store_session` would leave this turn the
> single cancel that replays without a marker.
>
> In the **same commit**, add the UI side: an `approval_request` early-return branch in
> `ui/stream_view.py::_handle_stream_event`
> (mirroring the existing `permission_warning` precedent) that resolves the
> approval immediately with `ApprovalDecision("deny", "once", reason=_DENY_NO_UI)` via
> `self._core.resolve_pending` — a module-level reason string of its own, **never** the gateway's
> `_DENY_USER` R11 wording, because no user was asked — marked `TODO(#1046)`; and make
> `action_cancel_stream` also call `self._core.cancel_pending_approvals()`. Without both, this
> commit ships an app where the first `ask`-gated call wedges the turn permanently (both timeouts
> suppressed by the pause, `_cancel_event` inert, non-daemon worker thread). Do not add a modal,
> scopes, or any persist write-back — that is #1046.
>
> Do **not** add an attach/detach `try/finally` in `RealLLMService.stream` — Step 7 owns the single
> lifecycle site. Do not import `textual` into `AppCore`.
>
> Write the nine test cases listed in the step first (assert engine **identity**, not equality).
>
> Use MCP tools only. Run the fast suite **and** the `textual_integration` marker. Finish with
> `run_pylint_check`, `run_pytest_check`, `run_mypy_check`, `run_lint_imports_check` and
> `check_file_size(max_lines=750)` all green, then one commit.

---

## Implementation note (post-implementation)

Implemented exactly as the step specifies — no shape deviations. One engine is built inside the
existing `provider == "langchain" and mcp_config` gate and injected into
`LangchainEnforcementGateway`, `RealLLMService(approval_bridge=…)` and
`AppCore(approval_engine=…, permission_gateway=…)`; `AppCore` gained the three no-op-safe
delegators, the `TRANSIENT_EVENT_TYPES` carve-out and the R16 gate; `ui/stream_view.py` gained the
`approval_request` early return (module-level `_DENY_NO_UI`, `TODO(#1046)`) and `ui/app.py`'s
`action_cancel_stream` now also calls `self._core.cancel_pending_approvals()`. No attach/detach was
added to `RealLLMService.stream`; `AppCore` still imports no `textual`.

### Patch-site survey (incomplete in the step)

The step's WHERE table lists `test_icoder_permission_wiring.py` but not the *second* stub of
`LangchainEnforcementGateway`. Adding the constructor's second argument breaks any one-parameter
stand-in, so two test doubles had to be re-pointed:

* `tests/icoder/test_icoder_permission_wiring.py` — `_FakeGateway.__init__(self, config)` →
  `(self, config, approval_engine=None)`; the test now also asserts
  `llm_calls[0]["approval_bridge"] is gateway.approval_engine` (identity, per the step).
* `tests/icoder/test_cli_icoder.py::test_execute_icoder_passes_permission_degraded_when_config_degraded`
  — `lambda _config: MagicMock()` → `lambda _config, _engine=None: MagicMock()`. This was the only
  **failing** test before the fix (`assert 1 == 0`: the `TypeError` was swallowed by the CLI's
  top-level error boundary, so it surfaced as a nonzero exit code rather than a traceback).

### Tests

`tests/icoder/test_approval_wiring.py` (new, 9 cases) covers step tests 1–7: identity wiring,
the non-langchain no-op path, both `approval_bridge` forwarding directions, R16 cancelled vs.
normal (parametrized over engine present/absent), the R5 carve-out (asserted against the session
`.jsonl` on disk, and asserting the live consumer still *sees* every event), and the engine-free
`scope=session` grant through the real gateway interceptor. Step tests 8–9 are in
`tests/icoder/test_app_pilot.py` (`textual_integration`), driven through a `_RecordingEngine`
subclass of the real `ApprovalEngine` so the `AppCore` parameter type holds without a cast; test 9
presses `escape` rather than calling the action directly, so the binding is exercised too.

### Checks

`run_pylint_check` clean on `src/mcp_coder/icoder` + `tests/icoder` (the `src`-wide run reports
only the pre-existing stale-`mcp_workspace` / absent-langchain E-codes, none in a touched file);
`run_mypy_check` (strict) on `src` + `tests/icoder` reports only the 6 pre-existing
stale-`mcp_workspace` errors; `run_lint_imports_check` 21/21 kept with the new
`cli.commands.icoder -> icoder.permissions.approval` entry; `run_format_code` reformatted
`tests/icoder/test_approval_wiring.py` (applied, re-verified green afterwards);
`check_file_size(max_lines=750)` clean — neither `ui/app.py` nor `ui/stream_view.py` is listed.

Pytest: `tests/icoder` minus the two files below (850 passed); `test_app_pilot.py` +
`test_cli_icoder.py` + `test_approval_wiring.py` unfiltered (92 passed, `textual_integration`
included); `tests/cli` + `tests/llm/providers/langchain` (one pre-existing failure, see below).

**Local environment caveats (all pre-existing, unchanged from Steps 1–8):** the stale installed
`mcp_workspace` still breaks pytest collection repo-wide, so every run used
`PYTHONPATH=C:\Users\Marcus\Documents\GitHub\mcp-workspace\src`; `pytest-textual-snapshot` is still
absent, so `tests/icoder/test_snapshots.py` errors at fixture setup here and was excluded from the
runs; `tests/llm/providers/langchain/test_langchain_exceptions.py::test_connection_errors_contains_httpx_connect_error`
still fails with `httpx` absent. None of them touches anything this step changed.
