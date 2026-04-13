# Step 5: Wire Everything in `execute_icoder()`

> **Ref:** [summary.md](summary.md) — "Modified Components → iCoder entry point"

## LLM Prompt

> Implement Step 5 from `pr_info/steps/step_5.md`. Read `pr_info/steps/summary.md` for full context.
> Wire up `MCPManager` creation, `/info` registration, and cleanup in `src/mcp_coder/cli/commands/icoder.py`.
> Follow TDD: write/update tests first, then implement. Run all code quality checks after.

## WHERE

- **Modified:** `src/mcp_coder/cli/commands/icoder.py`
- **Modified:** `tests/icoder/test_cli_icoder.py` (or new test file if needed)

## WHAT

Changes to `execute_icoder()` function:

1. After resolving `mcp_config` and `provider`, create `MCPManager` if applicable
2. After creating registry and registering skills, register `/info`
3. Pass `mcp_manager` to `RealLLMService`
4. Ensure `mcp_manager.close()` on exit

## HOW

### MCPManager creation (after mcp_config resolution, before LLM service)

```python
from ...llm.mcp_manager import MCPManager
from ...llm.providers.langchain.agent import _load_mcp_server_config

mcp_manager: MCPManager | None = None
if provider == "langchain" and mcp_config:
    server_config = _load_mcp_server_config(mcp_config, env_vars)
    mcp_manager = MCPManager(server_config)
```

### `/info` registration (after skill registration)

```python
from ...icoder.core.commands.info import register_info

register_info(registry, runtime_info, mcp_manager=mcp_manager)
```

### Pass to LLM service

```python
llm_service = RealLLMService(
    provider=provider,
    session_id=session_id,
    execution_dir=str(execution_dir),
    mcp_config=mcp_config,
    env_vars=env_vars,
    timeout=args.timeout,
    mcp_manager=mcp_manager,  # NEW
)
```

### Cleanup (try/finally around the EventLog context)

```python
try:
    with EventLog(logs_dir=project_dir / "logs") as event_log:
        # ... existing code ...
finally:
    if mcp_manager is not None:
        mcp_manager.close()
```

## ALGORITHM — changes to `execute_icoder()`

```
# After mcp_config resolution:
mcp_manager = None
if provider == "langchain" and mcp_config:
    server_config = _load_mcp_server_config(mcp_config, env_vars)
    mcp_manager = MCPManager(server_config)

# After skill registration:
register_info(registry, runtime_info, mcp_manager=mcp_manager)

# Pass to RealLLMService:
llm_service = RealLLMService(..., mcp_manager=mcp_manager)

# Wrap in try/finally for cleanup:
try:
    with EventLog(...) as event_log:
        ...
finally:
    if mcp_manager is not None:
        mcp_manager.close()
```

## DATA

- `mcp_manager`: `MCPManager | None` — `None` when provider is `claude` or no `mcp_config`
- No new return types or data structures

## TEST PLAN

1. `test_info_command_registered_in_icoder` — mock the TUI app, verify `/info` is in the registry after `execute_icoder` sets up
2. `test_mcp_manager_created_for_langchain` — mock dependencies, call `execute_icoder` with `provider="langchain"` and `mcp_config`, verify `MCPManager` is created
3. `test_mcp_manager_not_created_for_claude` — mock dependencies, call with `provider="claude"`, verify no `MCPManager` created
4. `test_mcp_manager_closed_on_exit` — mock `MCPManager.close()`, verify it's called after TUI exits
5. `test_mcp_manager_closed_on_error` — mock TUI to raise, verify `MCPManager.close()` still called (try/finally)

Note: These tests will heavily mock the TUI and LLM components. Focus on verifying the wiring, not the full integration.

## COMMIT

```
feat(icoder): wire MCPManager and /info into execute_icoder (#741)
```
