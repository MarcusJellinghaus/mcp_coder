# Step 4 — Turn-level integration in `RealLLMService`; remove I1.1 filter (D5)

**Reference:** read `pr_info/steps/summary.md` (KISS simplification #1, D5) first.

Wire the gateway's turn filter into `RealLLMService.stream()`, replacing I1.1's
`filter_tools_by_declaration` block. The gateway is optional (`None` until Step 5), so behaviour is
unchanged when absent. Enforcement is **config-driven, not gated on `enforce_skill_tools`**.

## WHERE
- `src/mcp_coder/icoder/services/llm_service.py` — `RealLLMService.__init__` / `.stream` (+ docstring).
- `src/mcp_coder/llm/providers/langchain/mcp_manager.py` — **delete** `filter_tools_by_declaration`.
- `src/mcp_coder/icoder/ui/app.py` — **KEEP** the `permission_warning` branch in `_handle_stream_event`
  (it now renders malformed-token warnings from `build_legacy_frame`; new producer, same event). No
  change unless the message text needs tweaking.
- `tests/llm/test_skill_tool_filter.py` — **delete** (tests the removed helper).
- `tests/icoder/test_llm_service.py` — update for the gateway path; keep/adjust a `permission_warning`
  assertion covering the malformed-token path (see TDD tests).
- `tests/icoder/test_app_core.py` — **KEEP** `test_stream_llm_passes_permission_warning_through`
  (the event path is preserved, now fed by malformed tokens).
- `tests/icoder/test_app_pilot.py` — **KEEP** `test_permission_warning_event_renders_message_text`
  (the event still renders).

## WHAT
```python
class RealLLMService:
    def __init__(self, ..., gateway: "LangchainEnforcementGateway | None" = None) -> None:
        ...
        self._gateway = gateway

    def stream(
        self, question: str, allowed_tools: tuple[str, ...] | None = None
    ) -> Iterator[StreamEvent]: ...
```

## HOW
- Import `LangchainEnforcementGateway` + `build_legacy_frame` from
  `mcp_coder.icoder.permissions.gateway` (top-level import is safe — the gateway pulls no
  `langchain_core`). Drop the `filter_tools_by_declaration` import.
- In `stream()`, replace the old `if self._enforce_skill_tools and allowed_tools:` block with the
  gateway path. The `LLMService` Protocol signature is **unchanged** (`allowed_tools` stays; no new
  `frame` param). `FakeLLMService` is untouched.
- **Repurpose (not remove) the `permission_warning` emission (USER DECISION).** `build_legacy_frame`
  now returns `(frame, warnings)`; emit one `permission_warning` event per malformed-token warning
  **before** setting the turn frame. The producer moves from I1.1's filter to the frame builder, but
  the event, the `ui/app.py` render branch, and the two rendering tests are **kept**. This preserves a
  user-visible signal for un-parseable skill tokens (which stay fail-closed — not silently elevated).
- **Docstring Boy-Scout (`stream()`):** update the docstring so it no longer says warnings come from
  "un-parseable tokens dropped by enforcement"; describe the new behaviour — a `permission_warning`
  event is yielded for each malformed declared token collected by `build_legacy_frame`, before the
  agent stream.
- Verify `filter_tools_by_declaration` has no remaining references (only `llm_service` +
  `test_skill_tool_filter.py`), then delete the function and its test file.

## ALGORITHM (`stream`)
```
tools = None
if self._mcp_manager is not None:
    tools = self._mcp_manager.tools()                 # cached list — read only
    if self._gateway is not None:
        frame, warnings = build_legacy_frame(allowed_tools, self._enforce_skill_tools)
        for msg in warnings:                          # surface malformed tokens (repurposed path)
            yield {"type": "permission_warning", "message": msg}
        self._gateway.begin_turn(frame)
        tools = self._gateway.filter_tools(tools, self._mcp_manager.canonical_name)
for event in prompt_llm_stream(question, ..., tools=tools, ...):
    update session_id on "done"; yield event
```

## DATA
- `tools` passed to `prompt_llm_stream` is either the manager's cached list (no gateway) or a filtered
  **copy** (gateway present). `MCPManager._cached_tools` is never mutated.

## TDD tests (write first)
- `test_stream_without_gateway_forwards_all_tools` — `gateway=None`, mcp_manager with 2 tools →
  `prompt_llm_stream` receives both (backward compat).
- `test_stream_with_gateway_drops_never_tools` — gateway with a config denying one tool → the filtered
  list excludes it; `prompt_llm_stream` receives the survivors.
- `test_stream_enforces_with_enforce_skill_tools_false` (D5) — `enforce_skill_tools=False`, config
  present with a `never` rule → the `never` tool is still dropped.
- `test_stream_does_not_mutate_manager_cache` — after `stream()`, `mcp_manager.tools()` still returns
  the full set.
- `test_stream_sets_per_turn_frame` — with `allowed_tools` set, `gateway.begin_turn` receives a
  `PermissionFrame`; with `allowed_tools=None`, it receives `None`.
- `test_stream_emits_permission_warning_for_malformed_token` (USER DECISION) — `allowed_tools`
  containing an un-parseable token → `stream()` yields a `permission_warning` event carrying the
  warning text, AND the malformed token is not elevated (the tool is not force-kept via the frame).
  Confirms the repurposed warning path surfaces the signal instead of dropping it silently.
- Patch `prompt_llm_stream` to a canned generator in these tests; use a fake mcp_manager exposing
  `tools()` + `canonical_name`.

## Checks
Full quality gate green. Confirm `test_skill_tool_filter.py` deletion leaves no dangling imports
(`lint-imports`, pytest collection). Confirm the `permission_warning` path still works end-to-end:
the `ui/app.py` render branch and the two rendering tests remain, now fed by malformed-token warnings
from `build_legacy_frame`.

## Commit
`I2.3 step 4: enforce never/always at turn level in RealLLMService; drop I1.1 filter`

## LLM prompt
> Implement Step 4 of the I2.3 plan. Read `pr_info/steps/summary.md` (KISS #1, D5) and
> `pr_info/steps/step_4.md`. Following TDD, first update `tests/icoder/test_llm_service.py`, then add a
> `gateway` parameter to `RealLLMService` and replace the `filter_tools_by_declaration` block in
> `stream()` with `build_legacy_frame` + `gateway.begin_turn` + `gateway.filter_tools` (translating the
> already-flowing `allowed_tools` into the frame inline — do NOT add a new `frame` parameter).
> `build_legacy_frame` now returns `(frame, warnings)`: **repurpose** (do NOT delete) the
> `permission_warning` emission to yield one event per malformed-token warning before setting the
> frame, keeping the `ui/app.py` branch and the two rendering tests. Update the `stream()` docstring to
> describe this new warning behaviour. Delete `filter_tools_by_declaration` and its test file after
> confirming no other references. Enforcement must run regardless of `enforce_skill_tools`. Use MCP
> tools only; all checks pass; one commit.
