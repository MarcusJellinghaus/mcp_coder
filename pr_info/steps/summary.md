# I2.3 — Langchain Enforcement Gateway (`never`/`always`) — Implementation Summary

## Goal

Introduce a deterministic, host-side **enforcement layer** between MCP tool discovery
(`MCPManager`) and the langchain agent. In milestone M2 it enforces exactly two policies:

- **`never`** → tool is hidden from the model (turn level) **and** denied if ever called (call level).
- **`always`** → tool passes through untouched.
- **`after-approval` (`ask`)** → tool stays **visible** at turn level but is **denied at call level**
  with a distinct "requires approval — not yet available" message (M3 swaps deny→prompt).

The gateway consumes the already-landed I2.1 resolver (`resolve()` → `Decision`) and the I2.2
loader (`load_permission_config()` → `PermissionConfig`). This issue is the **first real consumer of
I2.2** (the loader has zero non-test call sites today). `MCPManager` stays policy-free; the gateway
is the single, unit-testable enforcement site and cannot be widened by LLM output.

## Architectural / design changes

### New enforcement seam
```
                 build time (icoder.py startup)
  load_permission_config(project_dir) ──► PermissionConfig
                                            │
                                            ▼
                         LangchainEnforcementGateway(config)
                          │                         │
      tool_interceptors=[gate.interceptor]          │ gateway=gate
                          ▼                         ▼
                    MCPManager                RealLLMService
             (call-level enforcement)     (turn-level enforcement)
```

- **Call level** rides on `langchain-mcp-adapters` native `tool_interceptors` (an
  `async (request, handler)` hook passed to `convert_mcp_tool_to_langchain_tool`). The gateway's
  interceptor reconstructs the canonical name from `request.server_name` + `request.name`, calls
  `resolve()`, and either `await handler(request)` (`always`) or returns a deny `ToolMessage`.
- **Turn level** runs in `RealLLMService.stream()`: the gateway filters the manager's tool list by
  calling `resolve()` per tool and dropping `NEVER`. It operates on a **filtered copy** — never
  mutating `MCPManager._cached_tools`.
- **Per-turn holder = mutable field on the gateway** (`_frame`), not a separate object. `begin_turn(frame)`
  sets it; both the turn filter and the interceptor read it. Valid under the sequential-turn assumption
  (documented; M3 reuses this holder for the cross-thread approval Future).

### Decisions honoured
- **D1** — the three near-duplicate `convert_mcp_tool_to_langchain_tool` build loops
  (`mcp_manager._connect_and_discover`, `agent.run_agent`, `agent.run_agent_stream` else-branch) are
  **unified into one shared helper** accepting `tool_interceptors`. The real gateway is injected
  **only at the `MCPManager` site**; the two inline `agent.py` loaders pass `None`. A **bypass-guard
  test** asserts iCoder only ever reaches the instrumented `MCPManager` path.
- **D2** — `icoder.py` startup calls `load_permission_config(project_dir)` once and hands the config
  to the gateway.
- **D3** — `langchain-mcp-adapters` floor raised `>=0.1.0` → `>=0.3.0`; a runtime capability check
  gives a clear error if `tool_interceptors` is unsupported. The check is a reusable helper
  (`_assert_tool_interceptors_supported`) invoked **early at iCoder startup** — before `MCPManager`
  builds tools — so the clear `ImportError` beats the raw `TypeError` a `<0.3.0` adapter would raise
  at the first `convert_...(tool_interceptors=...)` call.
- **D4** — a throwaway inline **model-C frame** is built from the tokens already flowing as
  `allowed_tools` (legacy `allow` list → `base`, `allow=[...]`). I2.4 (#1061) later replaces this with
  `build_frame(skill)`.
- **D5** — base `never`/`always` enforcement runs **whenever a config is present**, independent of the
  `enforce_skill_tools` flag. The flag only controls skill-frame *narrowing* of undeclared tools,
  encoded purely as the frame's `base` (`"none"` when narrowing, `"inherit"` otherwise) — no branching
  in the gateway.

### KISS simplifications adopted (vs. the issue's literal prose)
1. **No new `frame` parameter is threaded through `stream()`/`AppCore`/`SendToLLM`.** The declared-tool
   tokens already flow end-to-end as `allowed_tools: tuple[str, ...]`. `RealLLMService.stream()`
   translates them into the throwaway model-C frame inline. This preserves every acceptance criterion
   while leaving `core/app_core.py`, `core/types.py`, the `LLMService` Protocol, and `FakeLLMService`
   untouched. Constructing an `AppCore`-owned frame is deferred to **I2.4 (#1061)**, which is the issue
   that owns `build_frame` — consistent with D4's minimal-then-refactor stance.
2. **The langchain-specific deny `ToolMessage` is built by a tiny provider-package helper**
   (`build_deny_tool_message`) that the gateway calls. The gateway itself imports **no** `langchain_core`
   / `langchain_mcp_adapters` symbols (adapter types are annotated `Any`). This keeps `langchain_core`
   confined to the provider package (respecting the existing "only the langchain provider imports
   langchain_core" boundary) and needs **no new import-linter exceptions** beyond narrowing the
   permissions-leaf contract to exclude the gateway.
3. **The per-turn holder is a plain mutable field**, and the turn filter mirrors the existing
   `filter_tools_by_declaration` signature so the `RealLLMService.stream()` change is a near one-line swap.
4. **The runtime capability check is a small reusable helper** (`_assert_tool_interceptors_supported`)
   called both from the existing `_check_agent_dependencies()` and **early at iCoder startup** (before
   `MCPManager` builds tools). Its `inspect.signature` call is guarded so the langchain conftest's
   `MagicMock` stand-in (present when the real adapter is absent) is skipped rather than misread.

### USER DECISION — malformed skill tokens keep a warning
`build_legacy_frame` returns `(frame, warnings)`: an un-parseable declared token contributes **no**
matcher (fail-closed — never silently elevated) and its parse error is **collected**. `RealLLMService.stream()`
surfaces each as a `permission_warning` event (the existing UI render path is **kept**, not deleted —
its producer simply moves from I1.1's filter to the frame builder). This preserves a user-visible signal
for malformed tokens instead of dropping them silently.

### Subsumed / replaced
- I1.1's `filter_tools_by_declaration` (skill narrowing) is **removed**; its role is subsumed by the
  gateway's resolver-based turn filter (frame-first semantics keep a skill-elevated `never` tool visible
  automatically). Its dedicated test file is removed too.

## Files created / modified

**Created**
- `src/mcp_coder/icoder/permissions/gateway.py` — `LangchainEnforcementGateway`, `build_legacy_frame`.
- `src/mcp_coder/llm/providers/langchain/permission_bridge.py` — `build_deny_tool_message` (langchain deny shape).
- `tests/icoder/test_permissions_gateway.py` — gateway + frame-builder unit tests.
- `tests/llm/providers/langchain/test_permission_bridge.py` — deny-shape unit test.
- `tests/llm/providers/langchain/test_tool_build_helper.py` — unified-helper + interceptor-passthrough tests.
- `tests/icoder/test_icoder_permission_wiring.py` — startup wiring, bypass-guard, and real-agent integration test.

**Modified**
- `pyproject.toml` — `langchain-mcp-adapters>=0.1.0` → `>=0.3.0` (in `langchain-base`).
- `src/mcp_coder/llm/providers/langchain/agent.py` — reusable `_assert_tool_interceptors_supported`
  helper (called from `_check_agent_dependencies` and, early, from iCoder startup); new
  `_convert_server_tools` helper; rewire `run_agent` and `run_agent_stream` onto it.
- `src/mcp_coder/llm/providers/langchain/mcp_manager.py` — `tool_interceptors` constructor param
  (pass-through); rewire `_connect_and_discover` onto the shared helper; **remove**
  `filter_tools_by_declaration`.
- `src/mcp_coder/icoder/services/llm_service.py` — `gateway` param on `RealLLMService`; replace the
  I1.1 filter block with the gateway turn filter; drop the `filter_tools_by_declaration` import;
  **repurpose** the `permission_warning` emission to surface malformed-token warnings from
  `build_legacy_frame`; update the `stream()` docstring to the new warning behaviour.
- `src/mcp_coder/cli/commands/icoder.py` — call `_assert_tool_interceptors_supported()` early (before
  `MCPManager`); `load_permission_config(project_dir)`; construct the gateway; inject
  `tool_interceptors=[gate.interceptor]` into `MCPManager`; pass `gateway` to `RealLLMService`.
- `.importlinter` — narrow `permissions_leaf_isolation` `source_modules` to the pure modules
  (`model`, `matcher`, `resolver`, `loader`) so the gateway may import the resolver + langchain provider.
- `tests/llm/test_skill_tool_filter.py` — **removed** (tests the deleted I1.1 helper).
- `tests/icoder/test_llm_service.py` — updated for the gateway path; `permission_warning` assertion
  retargeted to the malformed-token case.
- `tests/icoder/test_app_core.py`, `tests/icoder/test_app_pilot.py` — **kept** (the two
  `permission_warning` render tests stay; the event path is preserved, now fed by malformed tokens).

## Step plan (each step = one commit: tests + implementation + all checks green)

1. **Adapter floor + capability check** — pin `>=0.3.0`; fail fast if `tool_interceptors` unsupported.
2. **Unify the three build loops** — one `_convert_server_tools` helper accepting `tool_interceptors`;
   `MCPManager` gains a pass-through `tool_interceptors` param.
3. **Gateway core** — `LangchainEnforcementGateway` (turn filter + interceptor), `build_legacy_frame`,
   provider deny-bridge, and the import-linter narrowing. Fully unit-tested in isolation.
4. **Turn-level integration** — wire the gateway into `RealLLMService.stream()`; remove I1.1's filter.
5. **Startup wiring + guards** — early `_assert_tool_interceptors_supported()` + `load_permission_config`
   + gateway construction + interceptor injection in `icoder.py`; bypass-guard tests (site 2 stream-only
   + site 3 inline-loader); real-agent integration test.

## Requirements traceability
- AC "fully-`never` hidden / `always` unprompted" → Steps 3, 4.
- AC "denied call → clean `ToolMessage(status="error")`, no raise" → Steps 3 (shape), 5 (integration).
- AC "`always` passes through unchanged" → Steps 3, 5.
- AC "`after-approval` denies at call level; resolver still reports it" → Step 3.
- AC D5 "config-driven, not flag-gated" → Steps 3 (frame base), 4.
- AC D2 "config loaded + wired; no-config → ALWAYS default" → Step 5.
- AC D1 "single injection point + bypass guard (no un-instrumented convert site reachable from
  iCoder)" → Steps 2 (helper), 5 (guard — **both** site 2 stream-only + site 3 inline-loader).
- AC "same canonical identity turn vs call; two servers same bare name" → Step 3, Step 5
  (end-to-end assertion: real turn-level stamp equals interceptor `f"mcp__{server}__{request.name}"`).
- AC "`_cached_tools` never mutated" → Step 4.
- AC "skill-elevated `never` stays callable (synthetic frame)" → Step 3 (turn-level visibility +
  **call-level interceptor** callable test).
- AC "per-turn holder scopes frame+config" → Steps 3, 4.
- AC "adapter floor `>=0.3.0` + **clear** runtime error if unsupported (before the raw TypeError)" →
  Step 1 (reusable guarded helper), Step 5 (early startup call + ordering test).
- USER DECISION "malformed skill token → warning surfaced, tool not silently elevated" → Step 3
  (`build_legacy_frame` collects warnings), Step 4 (`permission_warning` emission + test).
- Regression "canonical-name stamp stays raw-MCP-name-based after unification (not `lc_tool.name`)" →
  Step 2 (non-tautological test: mock `convert_...` returns a renamed lc_tool; expected pinned to the
  raw-name literal).
- AC "unit + integration tests; pylint/mypy/ruff/import-linter green" → all steps.
