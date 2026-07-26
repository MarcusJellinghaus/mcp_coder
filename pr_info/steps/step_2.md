# Step 2 — Layer 2: positive-list scoping from the supplied `--mcp-config`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step exactly as specified in `pr_info/steps/step_2.md`. TDD: extend the tests first, watch them fail, then implement. Run pylint, pytest (fast-unit exclusion markers, `-n auto`) and mypy via the MCP tools; all must pass. Format with `./tools/format_all.sh` and produce exactly one commit for this step.

## WHERE

- `src/mcp_coder/llm/providers/claude/claude_mcp_guard.py` (new helper)
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` (`ask_claude_code_cli_stream`)
- Tests: `tests/llm/providers/claude/test_claude_cli_stream_mcp_guard.py`

## WHAT

1. New pure helper in `claude_mcp_guard.py`:
   ```python
   def load_mcp_server_names(mcp_config: str, base_dir: str | None = None) -> set[str]:
       """Return the ``mcpServers`` keys of an mcp-config file.

       Relative paths resolve against ``base_dir`` (the subprocess cwd /
       execution_dir), NOT the caller's cwd. Raises ValueError naming the file
       when it is missing, unreadable, not valid JSON, or ``mcpServers`` is
       present but not a dict. A file without ``mcpServers`` yields an empty
       set (valid: a session deliberately configured with no servers).
       """
   ```
2. In `ask_claude_code_cli_stream`: compute the positive list **before** `stream_subprocess(...)` is called (operator errors must surface up front, not mid-stream):
   ```python
   configured_servers: set[str] | None = (
       load_mcp_server_names(mcp_config, cwd) if mcp_config else None
   )
   ```
3. At the abort site (currently `fatal_servers = find_fatal_mcp_servers(msg)`), scope fatality — guard API unchanged:
   ```python
   fatal_servers = find_fatal_mcp_servers(msg)
   if configured_servers is not None:
       ignored = {k: v for k, v in fatal_servers.items() if k not in configured_servers}
       fatal_servers = {k: v for k, v in fatal_servers.items() if k in configured_servers}
       if ignored:
           logger.info("Ignoring non-configured MCP server(s) outside --mcp-config: %s", ignored)
   ```
4. Update `ask_claude_code_cli_stream`'s docstring: add `ValueError` to Raises; note that with `mcp_config` set, only servers listed in it can abort the session.

## HOW

- Import `load_mcp_server_names` alongside the existing guard imports in `claude_code_cli_streaming.py`; re-export from `claude_code_cli.py` with the other guard names.
- `mcp_config=None` ⇒ `configured_servers=None` ⇒ current behavior (every listed server guarded; layer 1 from step 1 still applies).

## ALGORITHM (`load_mcp_server_names`)

```
path = Path(mcp_config); if relative and base_dir: path = base_dir / path
try: data = json.loads(path.read_text(utf-8))
except (OSError, JSONDecodeError) as e: raise ValueError(f"Cannot read MCP config {path}: {e}") from e
servers = data.get("mcpServers", {}) if isinstance(data, dict) else raise ValueError(...)
if not isinstance(servers, dict): raise ValueError(f"Invalid 'mcpServers' in {path}: expected object")
return set(servers.keys())
```

## DATA

- Returns `set[str]` of configured server names; empty set is valid.
- `configured_servers: set[str] | None` — `None` means "no config supplied, guard everything".

## TESTS (write first)

- `load_mcp_server_names`: happy path; relative path resolved against `base_dir` (use `tmp_path`); missing file → `ValueError` containing the path; malformed JSON → `ValueError`; top-level non-dict → `ValueError`; missing `mcpServers` key → empty set.
- Streaming with `mcp_config` supplied: a non-configured server with status `failed` (and one with `needs-auth`) does NOT raise; a **configured** server with `failed` still raises; the mixed case raises naming only the configured server.
- Streaming with a bad `mcp_config` path raises `ValueError` before any subprocess interaction (assert the subprocess mock was never called).
- Streaming with `mcp_config=None`: unchanged behavior (existing tests keep passing).

## Commit

`fix: scope MCP guard fatality to servers listed in --mcp-config (#1090)`
