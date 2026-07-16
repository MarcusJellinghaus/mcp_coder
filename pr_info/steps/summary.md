# I1.1 — Enforce a skill's declared tool set in the langchain provider (#1039)

## Goal

When a user invokes a skill that declares `allowed-tools` in its `SKILL.md`, the
langchain agent must run that turn with **only** the declared MCP tools (a
model-C whitelist). Enforcement is **host-side**: the tool list is narrowed by
code *before* `create_react_agent`, so no LLM output can widen it.

**Mechanism only.** This delivers the enforcement mechanism as an **opt-in**
(`enforce_skill_tools=False` by default). It does **not** edit any skill files —
completing the repo skills' declarations under enforcement is deferred to #1062.
All tests use **purpose-built fixtures**, never repo skills.

## The plumbing gap being closed

`ClaudeSkill.allowed_tools` is parsed today but silently dropped between the
skill handler and the agent:

```
_make_langchain_handler → SendToLLM(text only)        (skills.py)
handle_input → rebuilds SendToLLM(text only)          (app_core.py)
app.py SendToLLM case → _stream_llm(text only)        (ui/app.py)
AppCore.stream_llm(text) → LLMService.stream(text)    (app_core.py)
RealLLMService.stream → always MCPManager.tools()     (llm_service.py)   ← full list
                                     │
                     prompt_llm_stream(tools=…) → create_react_agent(...)  ← injection seam
```

The `tools=` seam already exists (`llm/interface.py:prompt_llm_stream`). We thread
the declared set from the handler to `RealLLMService.stream`, and narrow the tool
list there.

## Architectural / design changes

1. **Canonical tool identity is stamped at discovery.** The langchain adapter sets
   each tool's `.name` to the **bare** MCP name and stores `server_name` nowhere.
   `server_name` is only in scope inside `MCPManager._connect_and_discover`, so we
   stamp `mcp__{server}__{tool}` onto the tool's `metadata` there and expose a pure
   `MCPManager.canonical_name(tool)` accessor. This is the only place the
   server→tool association exists; it also disambiguates two servers exposing the
   same bare name.

2. **A pure, MCPManager-free filter function.**
   `filter_tools_by_declaration(tools, canonical_name_of, declared)` →
   `(filtered_tools, warnings)`. One string-prefix pass classifies each declared
   token: exact `mcp__server__tool` → allow-set; `mcp__…*` / `mcp__…(…)` / `@group`
   → unmatched **+ warning**; anything else (Bash-style / bare) → ignored. The live
   tools are filtered to exactly the allow-set (**even when empty** — fail-closed).
   Unit-testable with no live MCP connection.

3. **`SendToLLM` carries the declared set.** A new optional
   `allowed_tools: tuple[str, ...] | None` field threads the declaration from the
   handler, through `handle_input` (preserved via `dataclasses.replace`), through the
   UI worker, to the service. Minimal carrier; M2/I2.3 replaces it with the frame object.

4. **Enforcement toggle lives on `RealLLMService`.** New constructor arg
   `enforce_skill_tools: bool = False` (wired from the iCoder CLI). When enforcing
   **and** a declaration is present, `stream()` filters a **copy** of
   `MCPManager.tools()` (never mutating the shared cache) and passes it into the
   `tools=` seam. `FakeLLMService` takes the arg for signature parity only (no-op)
   and records the `allowed_tools` it received (terminal assertion point).

5. **Warnings surface visibly, gated on enforcement.** Un-parseable-token warnings
   are emitted from the enforcement path (only when narrowing actually happens) as a
   synthetic `{"type": "permission_warning", "message": …}` `StreamEvent`, yielded
   before the agent stream. `AppCore.stream_llm` already forwards non-`raw_line`
   events to the event log (event-log half free); `app.py` adds a small render guard
   for the TUI half. (The warning is *not* emitted from the handler — the handler
   doesn't know `enforce_skill_tools`, so it would warn falsely when enforcement is off.)

## Fail-closed rules (the only path to the full set is a falsy/absent declaration)

| Declaration | Result |
|---|---|
| Absent / empty (`[]`) | Full default tool set (unchanged behaviour) |
| Subset of exact `mcp__server__tool` tokens | Exactly those tools |
| All entries non-MCP (Bash-only) | **Zero** MCP tools |
| Contains wildcard / `@group` / arg-scoped token | Restricted to exact-matched tools (zero if none) **+ warning**; never unrestricted |

## Folders / modules / files

**Modified — source**
- `src/mcp_coder/llm/providers/langchain/mcp_manager.py` — stamp canonical name in
  `_connect_and_discover`; add `canonical_name()`; add module-level
  `filter_tools_by_declaration()`.
- `src/mcp_coder/icoder/core/types.py` — add `SendToLLM.allowed_tools`.
- `src/mcp_coder/icoder/skills.py` — `_make_langchain_handler` populates `allowed_tools`.
- `src/mcp_coder/icoder/services/llm_service.py` — widen `stream()` on Protocol /
  `RealLLMService` / `FakeLLMService`; `enforce_skill_tools` ctor arg; filtering + warning.
- `src/mcp_coder/icoder/core/app_core.py` — preserve field in `handle_input`
  (`replace`); `stream_llm(text, allowed_tools=None)`.
- `src/mcp_coder/icoder/ui/app.py` — pass `action.allowed_tools` through the worker;
  `permission_warning` render guard.
- `src/mcp_coder/cli/commands/icoder.py` — pass `enforce_skill_tools=False`.

**Modified / created — tests**
- `tests/llm/test_skill_tool_filter.py` *(new)* — pure-filter unit tests.
- `tests/llm/test_mcp_manager.py` — `canonical_name` accessor tests.
- `tests/icoder/test_types.py` — `SendToLLM.allowed_tools` default.
- `tests/icoder/test_skills.py` — handler populates `allowed_tools`.
- `tests/icoder/test_llm_service.py` — enforcement / warning / cache-safety / parity.
- `tests/icoder/test_app_core.py` — field survives `handle_input`; `stream_llm` forwards.
- `tests/icoder/test_app_pilot.py` — UI threading + `permission_warning` render.
- `tests/icoder/test_cli_icoder.py` — CLI passes `enforce_skill_tools`.

**Created — planning docs**
- `pr_info/steps/summary.md`, `pr_info/steps/step_1.md` … `step_5.md`.

## Steps (one commit each, TDD)

1. Pure filter function `filter_tools_by_declaration`.
2. `MCPManager` canonical-name stamping + `canonical_name()` accessor.
3. `SendToLLM.allowed_tools` field + skill handler populates it.
4. Service layer: `enforce_skill_tools`, `stream(allowed_tools=…)`, filtering + warning.
5. End-to-end threading: `AppCore`, `ui/app.py`, CLI wiring.

## Out of scope
Skill-file edits (#1062) · self-invocation guard (I1.2) · base-policy config /
`never`/`always`/`ask` / gateway / arg-level matching / `PermissionFrame` (M2+, I2.4) ·
wildcard/group/arg-scoped *matching* (I2.1/I4.1) · enforcing non-MCP/Bash tokens ·
Claude Code provider (native enforcement).
