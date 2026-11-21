# Step 4 — Required MCP servers: parsing, `verify`, icoder start-up and `/info` (Scope 3)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_4.md`).
> Implement Step 4 only: replace `MCP_SERVER_NAMES` with
> `required_mcp_servers(project_dir)`, give `parse_claude_mcp_list` a required
> list with a "not listed" status, restrict `verify_mcp_servers` to
> `mcp-workspace`, and make `verify`, icoder start-up and `/info` pass the
> required list and the resolved MCP config path. Banner/event-log display is
> Step 5. Tests first, then code. Run format, pylint, mypy, lint-imports, tach
> and the fast pytest set. One commit.

## WHERE

- `src/mcp_coder/utils/mcp_verification.py`
- `src/mcp_coder/cli/commands/verify.py` (MCP block around `parse_claude_mcp_list`)
- `src/mcp_coder/icoder/env_setup.py` (`RuntimeInfo`, `setup_icoder_environment`)
- `src/mcp_coder/icoder/core/commands/info.py`
- Tests:
  - `tests/utils/test_mcp_verification.py` (drop the `MCP_SERVER_NAMES` import)
  - **new** `tests/cli/commands/test_verify_required_servers.py`
  - **new** `tests/icoder/test_required_servers.py`
  - existing callers' tests that call `parse_claude_mcp_list` or build
    `RuntimeInfo` (add the new argument / rely on defaults)

## WHAT

```python
# utils/mcp_verification.py
_SHIPPED_SERVERS: tuple[str, ...] = (WORKSPACE_SERVER,)   # from toolkit_runner

def required_mcp_servers(project_dir: Path) -> list[str]:
    """mcp-workspace plus the servers the configured toolkit grants tools of."""
    return mcp_servers_of(llm_permissions(project_dir, "claude"))

def verify_mcp_servers(venv_root: str | Path) -> list[MCPServerInfo]:  # loops _SHIPPED_SERVERS

def parse_claude_mcp_list(
    env_vars: dict[str, str],
    required_servers: Sequence[str],
    mcp_config_path: str = ".mcp.json",
    timeout: int = 60,
    claude_executable: str | None = None,
) -> list[ClaudeMCPStatus] | None: ...

# icoder/env_setup.py — RuntimeInfo gains (with defaults, at the end)
    required_mcp_servers: tuple[str, ...] = ()
    mcp_config: str | None = None
```

## HOW

- `mcp_verification.py` imports `WORKSPACE_SERVER`, `llm_permissions`,
  `mcp_servers_of` from `.toolkit_runner` (both in `utils`; no layer change).
- `verify.py`: inside `if mcp_config_resolved and mcp_config_ok is not False:`
  ```python
  claude_mcp = parse_claude_mcp_list(
      env_vars, required_mcp_servers(project_dir),
      mcp_config_path=mcp_config_resolved, claude_executable=claude_exe)
  ```
  `claude_mcp_ok = all(s.ok for s in claude_mcp)` already turns "not listed"
  into exit 1 for provider `claude`; langchain stays informational. No change
  to the "Tools exposed" check or `find_fatal_mcp_servers`.
- `setup_icoder_environment`: compute `required = tuple(required_mcp_servers(project_dir))`
  once; call `parse_claude_mcp_list(effective, required, claude_executable=claude_exe,
  **({"mcp_config_path": mcp_config} if mcp_config else {}))`; store
  `required_mcp_servers=required`, `mcp_config=mcp_config` in `RuntimeInfo`.
- `info.py`: `parse_claude_mcp_list(runtime_info.env_vars,
  runtime_info.required_mcp_servers, claude_executable=claude_exe, **(same
  conditional mcp_config_path from runtime_info.mcp_config))`. It must not load
  the toolkit. Its loop over `claude_mcp` then prints the required list with status.
- Update the `ClaudeMCPStatus.name` docstring (no `MCP_SERVER_NAMES`).

## ALGORITHM (`parse_claude_mcp_list`, after the command ran)

```
found: dict[str, ClaudeMCPStatus] = {}
for line in stdout lines matching _MCP_LIST_LINE_RE:
    if name in required_servers: found[name] = ClaudeMCPStatus(name, text, text == "Connected")
return [found.get(n) or ClaudeMCPStatus(n, "not listed", False) for n in required_servers]
```

Failure paths (no executable, timeout, non-zero exit, exception) still return `None`.

## DATA

- `required_mcp_servers` → `list[str]`, `mcp-workspace` first; `["mcp-workspace"]`
  when the toolkit fails to load (`llm_permissions` returns `[]` with a warning).
- `parse_claude_mcp_list` → statuses in `required_servers` order, or `None`.

## Tests (write first)

- `parse_claude_mcp_list`: a required server missing from the output →
  `ClaudeMCPStatus(name, "not listed", ok=False)`; unrequired servers in the
  output are ignored; order follows `required_servers`; `--mcp-config` argv
  uses the passed path.
- `verify_mcp_servers`: only `mcp-workspace` is checked; a missing
  `mcp-tools-py` binary doesn't raise.
- `required_mcp_servers`: with a fake toolkit whose `llm_permissions` grant
  `mcp__x__tool` → `["mcp-workspace", "x"]`; load failure → `["mcp-workspace"]`.
- `verify` (provider `claude`): `claude mcp list` output lacks a required
  server → MCP row `[ERR] not listed`, exit 1; same under langchain → exit
  unaffected by it; `parse_claude_mcp_list` receives `mcp_config_resolved`.
- Done-when case: a `command` project (`_toolkit_class` → `CommandToolkit`,
  no Bash grants needed) with `.mcp.json` holding only `mcp-workspace`, the
  mcp-tools-py binary absent: required list is `["mcp-workspace"]`, the
  Claude MCP rows pass, and `setup_icoder_environment` succeeds
  (`execute_command` / `find_claude_executable` patched as in existing
  env_setup tests).
- icoder: `RuntimeInfo.required_mcp_servers` / `mcp_config` set; `/info`
  passes them and prints a "not listed" server.

Note: the autouse `_resolvable_formatter` fixture resolves config-less
projects to `PythonToolkit`, so `required_mcp_servers` returns
`["mcp-workspace", "mcp-tools-py"]` in existing tests. Existing `verify` /
icoder tests whose fake `claude mcp list` output lacks one of these now see a
"not listed" entry; patch `required_mcp_servers` at its use site
(`mcp_coder.cli.commands.verify.required_mcp_servers`,
`mcp_coder.icoder.env_setup.required_mcp_servers`) or extend the fake output.
