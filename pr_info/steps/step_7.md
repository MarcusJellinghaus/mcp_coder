# Step 7 — Wiring: CLI → gateway / `RealLLMService` / `AppCore` (+ R16 gate)

**Depends on:** Steps 2, 4, 5.

One long-lived engine, constructed at startup and injected into all three holders, so the UI can
*reach* it (Step 8) from the modal callback and from cancel — and so a cancelled-while-pending turn
leaves no session record.

---

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/cli/commands/icoder.py` | **modify** — construct + inject |
| `src/mcp_coder/icoder/services/llm_service.py` | **modify** — `approval_bridge` param, forwarded |
| `src/mcp_coder/icoder/core/app_core.py` | **modify** — handles, delegators, R5 carve-out, R16 gate |
| `.importlinter` | **modify** — `layered_architecture` ignore entry |
| `tests/icoder/test_approval_wiring.py` | **create** |
| `tests/icoder/test_icoder_permission_wiring.py` | **modify** — assert the engine reaches all three |

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
  of `_ask_agent_stream`, and Step 5 already owns the single lifecycle site (summary §2.10).
* **`AppCore.stream_llm`** — two edits:
  1. the event-log carve-out becomes
     `if event.get("type") not in _TRANSIENT_EVENT_TYPES:` (imported from `llm.types`, the shared
     constant from Step 5);
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

## CHECKS

`run_pylint_check`, `run_pytest_check`, `run_mypy_check`, `run_lint_imports_check` — all green.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (§2.6, §2.7, §2.8, §2.10) and `pr_info/steps/step_7.md`, then
> implement Step 7 only.
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
> replace the `!= "raw_line"` event-log check with the shared `_TRANSIENT_EVENT_TYPES` constant
> from `llm/types.py`, and skip **both** `llm_request_end` **and** `store_session` when the
> injected engine reports `cancelled` — with a comment explaining that `ui/replay.py` keys its
> `— Cancelled —` marker off `in_flight`, so gating only `store_session` would leave this turn the
> single cancel that replays without a marker.
>
> Do **not** add an attach/detach `try/finally` in `RealLLMService.stream` — Step 5 owns the single
> lifecycle site. Do not import `textual` into `AppCore`.
>
> Write the seven test cases listed in the step first (assert engine **identity**, not equality).
>
> Use MCP tools only. Finish with `run_pylint_check`, `run_pytest_check`, `run_mypy_check` and
> `run_lint_imports_check` all green, then one commit.
