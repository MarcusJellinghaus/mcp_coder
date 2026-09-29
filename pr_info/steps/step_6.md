# Step 6 — CLI wiring: load for every provider (D9), banner stays gated (D12)

Read [summary.md](./summary.md) §7 first. Last step: makes `@group`/`use:` actually reach skills, and
keeps the misleading startup banner where it belongs.

## WHERE

- `src/mcp_coder/cli/commands/icoder.py` (modify)
- `tests/icoder/test_icoder_permission_wiring.py` (modify)
- `tests/icoder/test_cli_icoder.py` (modify — docstring only)

## WHAT

No new functions. Three edits inside `execute_icoder`:

1. Hoist `config = load_permission_config(project_dir)` **above** the
   `if provider == "langchain" and mcp_config:` gate (currently `icoder.py:113`).
2. Keep `permission_degraded = config.degraded` **inside** that gate (D12).
3. Pass `groups=config.groups, scenarios=config.scenarios` to `build_frame` at `icoder.py:177`.

## HOW

- The `config` local already exists; it just moves out of the branch. The comment explaining that
  `permission_degraded` is hoisted "because `config` only exists inside the langchain gate" becomes
  wrong — replace it with the D12 reason: the load is provider-agnostic, but the banner
  (`icoder.py:116` → `app_core.py:341` → `ui/startup.py:42-47`) claims MCP calls are being denied,
  which is false under the Claude provider where nothing is enforced.
- Also correct the stale comment "Non-langchain keeps this False default (no permission config
  loaded)" — the config *is* loaded now; only the flag stays False.
- `emit_schema` now also runs under Claude. It is already gated on `.icoder/` existing **and** on
  content change, so there is no git churn — no work, just note it.
- `build_frame`'s new parameters have defaults (step 5), so this is an additive call-site change.
- Nothing else moves: `approval_engine`, `gateway` and `MCPManager` stay inside the langchain gate.

## ALGORITHM

```
config = load_permission_config(project_dir)          # D9: every provider
permission_degraded = False                            # D12: banner flag only
if provider == "langchain" and mcp_config:
    _assert_tool_interceptors_supported()
    permission_degraded = config.degraded              # stays gated
    approval_engine = ApprovalEngine()
    gateway = LangchainEnforcementGateway(config, approval_engine)
    ...unchanged...

frame_map = {s.name: build_frame(..., groups=config.groups, scenarios=config.scenarios) for s in skills}
```

## DATA

Unchanged shapes. `AppCore(..., permission_degraded=permission_degraded)` still receives `False` off
the langchain+mcp_config path, even when the loaded config is degraded.

## Tests (write first)

`tests/icoder/test_icoder_permission_wiring.py`:

1. **Rewrite** `test_icoder_no_gateway_without_langchain` (`:174-217`) from "config is never loaded"
   to "**loaded** but no gateway, no banner": `load_calls == [project_dir]`, `gateway is None`,
   `mcp_manager is None`.
2. New: under the Claude provider with a **degraded** config, `permission_degraded` reaches `AppCore`
   as `False` and no startup banner is raised (D12). Capture the `AppCore` kwargs the way the existing
   tests capture `RealLLMService` kwargs.
3. New: `build_frame` receives `config.groups` / `config.scenarios` — monkeypatch
   `mcp_coder.cli.commands.icoder.build_frame` and assert the kwargs, or assert a skill declaring
   `@group` is **not** blocked under the Claude provider (the AC's phrasing; prefer this one).
4. Existing langchain tests must still show `permission_degraded is True` for a degraded config.

`tests/icoder/test_cli_icoder.py`:

5. `test_execute_icoder_permission_degraded_defaults_false_off_langchain` (`:293-310`) — the
   **assertion still holds** under D12. Fix only the docstring's "no permission config is loaded",
   which is now false.

## LLM prompt

> Implement **step 6** of `pr_info/steps/summary.md` as described in `pr_info/steps/step_6.md`.
> Read the summary first (§7) for D9 and D12.
>
> Test-driven: rewrite/add the five test cases listed first, watch them fail, then make the three
> edits in `src/mcp_coder/cli/commands/icoder.py`.
>
> The one thing not to get wrong: `load_permission_config` moves out of the
> `provider == "langchain" and mcp_config` gate, but `permission_degraded = config.degraded` **stays
> inside it**. Loading everywhere is D9; keeping the flag gated is D12, because the startup banner
> claims MCP calls are being denied and that is false under the Claude provider. Also fix the two now-
> wrong comments around the old hoist.
>
> Then run the checks listed at the end of the summary, plus the full unit suite — this step touches
> the CLI entry point. One commit.
>
> After it is green, delete `pr_info/steps/` scratch artefacts only if the repo's workflow calls for
> it; otherwise leave the plan in place for the PR.
