# Step 4: `/info` Command

> **Ref:** [summary.md](summary.md) — "New Components → /info command"

## LLM Prompt

> Implement Step 4 from `pr_info/steps/step_4.md`. Read `pr_info/steps/summary.md` for full context.
> Create the `/info` slash command in `src/mcp_coder/icoder/core/commands/info.py` with tests in `tests/icoder/test_info_command.py`.
> Follow TDD: write tests first, then implement. Run all code quality checks after.

## WHERE

- **New:** `src/mcp_coder/icoder/core/commands/info.py`
- **New:** `tests/icoder/test_info_command.py`

## WHAT

### Public API

```python
def register_info(
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
    mcp_manager: MCPManager | None = None,
) -> None:
    """Register the /info command. Captures dependencies via closure."""
```

### Internal helpers

```python
def _redact_env_vars(env: dict[str, str]) -> dict[str, str]:
    """Redact env var values where key contains sensitive substrings.

    Matches case-insensitively: token, key, secret, password, credential.
    Redacted values replaced with '***'.
    """

def _format_info(
    runtime_info: RuntimeInfo,
    mcp_manager: MCPManager | None,
) -> str:
    """Build the /info output string. All values re-read live."""
```

## HOW

- Follows the same pattern as `register_help()`, `register_clear()`, `register_quit()`
- `register_info()` uses `@registry.register("/info", "Show runtime diagnostics")`
- Handler calls `_format_info()` and returns `Response(text=result)`
- `_format_info()` re-reads live values: `sys.version`, `sys.executable`, `importlib.metadata.version("mcp-coder")`, `os.environ`
- `RuntimeInfo` provides `tool_env_path`, `project_venv_path`, `project_dir` for the Environments section
- MCP section: if `mcp_manager` is not `None`, calls `mcp_manager.status()` for langchain info
- MCP section: always tries `parse_claude_mcp_list()` for Claude Code info (uses `runtime_info.env_vars`)
- Env vars section: filters `MCP_CODER_*` separately, then shows rest with redaction

## ALGORITHM — `_format_info()`

```
lines = ["=== iCoder /info ==="]
lines += [f"mcp-coder version: {importlib.metadata.version('mcp-coder')}"]
lines += [f"Python: {sys.version} ({sys.executable})"]
lines += [f"Environments: tool_env={runtime_info.tool_env_path}, ..."]
if mcp_manager:
    for s in mcp_manager.status():
        lines += [f"  {s.name}  {'✓' if s.connected else '✗'}  ({s.tool_count} tools)"]
lines += ["MCP_CODER_* env vars: ..."]  # filtered from os.environ
lines += ["Other env vars: ..."]  # redacted via _redact_env_vars
return "\n".join(lines)
```

## ALGORITHM — `_redact_env_vars()`

```
SENSITIVE = ("token", "key", "secret", "password", "credential")
result = {}
for k, v in env.items():
    if any(s in k.lower() for s in SENSITIVE):
        result[k] = "***"
    else:
        result[k] = v
return result
```

## DATA

- Input: `RuntimeInfo` (frozen dataclass), `MCPManager | None`
- Output: `Response(text=...)` — plain text, no Rich markup
- `_redact_env_vars` input/output: `dict[str, str]` → `dict[str, str]`
- Unicode symbols: `✓` for connected, `✗` for disconnected

### Output format (draft from issue)

```
=== iCoder /info ===
mcp-coder version: 0.x.y
Python:            3.11.x (C:\...\python.exe)

Environments:
  Tool env:    C:\...
  Project env: C:\...
  Project dir: C:\...

MCP servers (langchain):
  tools-py    ✓ Connected   (12 tools)
  workspace   ✓ Connected   (8 tools)

MCP servers (claude):
  tools-py: C:\...\mcp-tools-py.exe ... - ✓ Connected
  workspace: C:\...\mcp-workspace.exe ... - ✓ Connected

MCP_CODER_* env vars:
  MCP_CODER_PROJECT_DIR=...
  MCP_CODER_VENV_DIR=...

Other env vars (secrets redacted):
  PATH=C:\...
  GITHUB_TOKEN=***
  ANTHROPIC_API_KEY=***
```

## TEST PLAN (`tests/icoder/test_info_command.py`)

### `_redact_env_vars` tests

1. `test_redact_env_vars_redacts_token` — `{"GITHUB_TOKEN": "abc"}` → `{"GITHUB_TOKEN": "***"}`
2. `test_redact_env_vars_redacts_key` — `{"API_KEY": "abc"}` → `{"API_KEY": "***"}`
3. `test_redact_env_vars_redacts_secret` — `{"MY_SECRET": "abc"}` → `{"MY_SECRET": "***"}`
4. `test_redact_env_vars_redacts_password` — `{"DB_PASSWORD": "x"}` → `{"DB_PASSWORD": "***"}`
5. `test_redact_env_vars_redacts_credential` — `{"CREDENTIAL_FILE": "x"}` → `{"CREDENTIAL_FILE": "***"}`
6. `test_redact_env_vars_case_insensitive` — `{"github_token": "abc"}` → `{"github_token": "***"}`
7. `test_redact_env_vars_preserves_safe` — `{"PATH": "/usr/bin"}` stays unchanged
8. `test_redact_env_vars_empty` — `{}` → `{}`

### `/info` command integration tests

9. `test_info_command_registered` — registry has `/info` after `register_info()`
10. `test_info_shows_version` — output contains `mcp-coder version:`
11. `test_info_shows_python` — output contains `Python:` and `sys.executable`
12. `test_info_shows_environments` — output contains `Tool env:`, `Project env:`, `Project dir:`
13. `test_info_shows_mcp_status` — with mock `MCPManager`, output contains server status with `✓`/`✗`
14. `test_info_without_mcp_manager` — `mcp_manager=None`, no crash, MCP langchain section omitted or shows "not active"
15. `test_info_shows_mcp_coder_env_vars` — output contains `MCP_CODER_*` section
16. `test_info_redacts_secrets_in_env` — output contains `***` for sensitive vars
17. `test_info_in_help` — `/info` appears in `/help` output

## COMMIT

```
feat(icoder): add /info slash command with runtime diagnostics (#741)
```
