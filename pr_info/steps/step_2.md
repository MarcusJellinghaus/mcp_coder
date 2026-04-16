# Step 2 — `agent.py`: wrap MCP launch failures as LLMMCPLaunchError

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement
> Step 2 only: in `src/mcp_coder/llm/providers/langchain/agent.py`, wrap
> `FileNotFoundError` and `PermissionError` raised from
> `async with client.session(server_name)` as `LLMMCPLaunchError` in both
> `run_agent` and `run_agent_stream` (the `tools is None` branch in the
> latter). Add tests in
> `tests/llm/providers/langchain/test_langchain_agent.py`. Step 1 must
> already be merged (it introduced `LLMMCPLaunchError` and narrowed
> `CONNECTION_ERRORS`). Run the mandatory MCP tool quality checks.

## WHERE

- `src/mcp_coder/llm/providers/langchain/agent.py` — modify.
- `tests/llm/providers/langchain/test_langchain_agent.py` — modify
  (add new tests; no existing test changes expected).

## WHAT

### New import

```python
from ._exceptions import LLMMCPLaunchError
```

### Wrap site A — `run_agent`

Current block:

```python
client = MultiServerMCPClient(cast(Any, server_config))
all_tools = []
for server_name, connection in client.connections.items():
    async with client.session(server_name) as session:
        raw_tools = await session.list_tools()
        ...
```

Wrap the `async with client.session(server_name) as session:` line
together with the tool-loading body inside the same `try` block —
`FileNotFoundError` / `PermissionError` from `stdio_client.__aenter__`
are raised *on entering* the context manager, so the `try` must cover
the `async with` statement itself, not only its body. Re-raise as
`LLMMCPLaunchError`.

### Wrap site B — `run_agent_stream`

Inside the `if tools is None:` branch (subprocess-spawning path only),
apply the same wrap: wrap the
`async with client.session(server_name) as session:` line together with
the tool-loading body inside the same `try` block — `FileNotFoundError`
/ `PermissionError` from `stdio_client.__aenter__` are raised *on
entering* the context manager. The `tools is not None` early-return
path does **not** spawn subprocesses and does **not** need the wrap.

### Message format

```
MCP server '<name>' failed to launch: <resolved-command> (<ExceptionClassName>)
```

The resolved command is `server_config[server_name].get("command", "")`.

## HOW — integration points

- Signature of `run_agent` / `run_agent_stream` is unchanged.
- `LLMMCPLaunchError` propagates naturally: it is not in
  `CONNECTION_ERRORS`, so `_handle_provider_error` in
  `langchain/__init__.py` passes it through. `_ask_agent` and
  `_ask_agent_stream` then re-raise the original exception unchanged.
  The CLI's top-level handler prints `str(exc)`.

## ALGORITHM — per site

```
try:
    async with client.session(server_name) as session:
        raw_tools = await session.list_tools()
        for tool in raw_tools.tools: ...      # (existing body)
except (FileNotFoundError, PermissionError) as exc:
    cmd = server_config[server_name].get("command", "")
    raise LLMMCPLaunchError(
        f"MCP server '{server_name}' failed to launch: "
        f"{cmd} ({type(exc).__name__})"
    ) from exc
```

The `try/except` is **inside** the `for server_name, connection in
client.connections.items():` loop so that the server name and resolved
command are in scope.

## DATA

- `LLMMCPLaunchError` instance `.args[0]`: the formatted message string.
- `.__cause__`: the original `FileNotFoundError` or `PermissionError`.
- No changes to return values of `run_agent` or `run_agent_stream`.

## TDD — tests to add

In `tests/llm/providers/langchain/test_langchain_agent.py`:

1. **`test_run_agent_wraps_filenotfound_as_launch_error`**
   - Patch `MultiServerMCPClient` so `client.connections` yields one
     server `{"broken": ...}` and `client.session("broken").__aenter__`
     raises `FileNotFoundError("no such file")`.
   - Call `asyncio.run(run_agent(...))`.
   - Assert raised exception is `LLMMCPLaunchError`.
   - Assert message contains the resolved command path and
     `"FileNotFoundError"`.
   - Assert `exc.__cause__` is the original `FileNotFoundError`.

2. **`test_run_agent_wraps_permissionerror_as_launch_error`**
   - Same harness, raise `PermissionError("denied")` instead.
   - Assert message contains `"PermissionError"`.

3. **`test_run_agent_stream_wraps_filenotfound`**
   - Same harness but call `run_agent_stream` in the `tools=None` branch.
   - Use `async for ... in run_agent_stream(...):` inside an
     `asyncio.run` wrapper; assert the generator raises
     `LLMMCPLaunchError` on first iteration.

4. **`test_run_agent_stream_skips_wrap_when_tools_provided`**
   - Call `run_agent_stream(..., tools=[<mock tool>])`.
   - Ensure `MultiServerMCPClient` is not constructed
     (`patch(...).assert_not_called()`).

Mock `create_react_agent` to return an object whose `astream_events` (or
`ainvoke`) never gets called — these tests only exercise the
pre-agent-setup path, so the wrap exception is raised before agent
invocation.

- Existing test
  `tests/llm/providers/langchain/test_langchain_agent.py::test_hard_fails_on_mcp_server_error`
  (approx. line 510) asserts `ConnectionError` (not `FileNotFoundError`
  / `PermissionError`); it is unchanged by this step and must remain
  green.

## Done-when

- `mcp__tools-py__run_pylint_check` clean.
- `mcp__tools-py__run_pytest_check` (fast-unit exclusions) green.
- `mcp__tools-py__run_mypy_check` clean.
- Single commit: "Step 2: wrap MCP launch failures as LLMMCPLaunchError
  in agent (#830)".
