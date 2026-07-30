# Step 4 — Turn-level integration in `RealLLMService`; remove I1.1 filter (D5)

**Reference:** read `pr_info/steps/summary.md` (KISS simplification #1, D5) first.

Wire the gateway's turn filter into `RealLLMService.stream()`, replacing I1.1's
`filter_tools_by_declaration` block. The gateway is optional (`None` until Step 5), so behaviour is
unchanged when absent. Enforcement is **config-driven, not gated on `enforce_skill_tools`**.

## WHERE
- `src/mcp_coder/icoder/services/llm_service.py` — `RealLLMService.__init__` / `.stream`.
- `src/mcp_coder/llm/providers/langchain/mcp_manager.py` — **delete** `filter_tools_by_declaration`.
- `tests/llm/test_skill_tool_filter.py` — **delete** (tests the removed helper).
- `tests/icoder/test_llm_service.py` — update for the gateway path.

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
- Remove the `permission_warning` event emission (subsumed; not an AC).
- Verify `filter_tools_by_declaration` has no remaining references (only `llm_service` +
  `test_skill_tool_filter.py`), then delete the function and its test file.

## ALGORITHM (`stream`)
```
tools = None
if self._mcp_manager is not None:
    tools = self._mcp_manager.tools()                 # cached list — read only
    if self._gateway is not None:
        frame = build_legacy_frame(allowed_tools, self._enforce_skill_tools)
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
- Patch `prompt_llm_stream` to a canned generator in these tests; use a fake mcp_manager exposing
  `tools()` + `canonical_name`.

## Checks
Full quality gate green. Confirm `test_skill_tool_filter.py` deletion leaves no dangling imports
(`lint-imports`, pytest collection).

## Commit
`I2.3 step 4: enforce never/always at turn level in RealLLMService; drop I1.1 filter`

## LLM prompt
> Implement Step 4 of the I2.3 plan. Read `pr_info/steps/summary.md` (KISS #1, D5) and
> `pr_info/steps/step_4.md`. Following TDD, first update `tests/icoder/test_llm_service.py`, then add a
> `gateway` parameter to `RealLLMService` and replace the `filter_tools_by_declaration` block in
> `stream()` with `build_legacy_frame` + `gateway.begin_turn` + `gateway.filter_tools` (translating the
> already-flowing `allowed_tools` into the frame inline — do NOT add a new `frame` parameter). Remove
> the `permission_warning` emission, delete `filter_tools_by_declaration` and its test file after
> confirming no other references. Enforcement must run regardless of `enforce_skill_tools`. Use MCP
> tools only; all checks pass; one commit.
