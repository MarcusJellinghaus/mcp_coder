# Step 6 — Extract `format_runtime_banner()` helper

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step
> (`pr_info/steps/step_6.md`) with strict TDD. Tests first, then code.
> Run pylint, pytest, mypy via the mandatory MCP tools. Single commit.

## WHERE

- Modify: `src/mcp_coder/icoder/ui/app.py` — extract banner-line
  building from `on_mount()` into a module-level helper.
- Add tests to: `tests/icoder/ui/test_app.py` (or a new
  `tests/icoder/test_banner.py` if simpler — pure function, no Textual
  needed).

## WHAT

```python
# in src/mcp_coder/icoder/ui/app.py (module level)
def format_runtime_banner(data: Mapping[str, object]) -> list[str]:
    """Build the dim banner lines shown at startup and during replay.

    Accepts either a RuntimeInfo-shaped mapping (live) or a session_start
    event payload (replay). Both contain: mcp_coder_version, tool_env (or
    tool_env_path), project_venv (or project_venv_path), project_dir,
    mcp_servers, mcp_connection_status. Missing keys are handled
    gracefully.
    """
```

`on_mount()` becomes:

```python
if self._core.runtime_info:
    info = self._core.runtime_info
    output = self.query_one(OutputLog)
    lines = format_runtime_banner({
        "mcp_coder_version": info.mcp_coder_version,
        "mcp_coder_utils_version": info.mcp_coder_utils_version,
        "tool_env_path": info.tool_env_path,
        "project_venv_path": info.project_venv_path,
        "project_dir": info.project_dir,
        "mcp_servers": [{"name": s.name, "version": s.version} for s in info.mcp_servers],
        "mcp_connection_status": [...],
    })
    output.append_text("\n".join(lines), style="dim")
```

(The exact field names match those written into `session_start` payloads
so a replay can pass the parsed dict directly.)

## HOW

- The helper is **pure** (no Textual / no I/O). Returns the list of lines
  exactly as the existing code currently joins them.
- Accept both `tool_env_path` and `tool_env` keys for compatibility
  (CLI emits `tool_env`, RuntimeInfo has `tool_env_path` — pick one
  canonical name and write to the `session_start` payload using that
  same name in **Step 11** if needed; for this step, the helper handles
  both via a two-key fallback).
- `mcp_servers` accepts either:
  - a list of `MCPServerInfo` objects (live), or
  - a list of `{"name": ..., "version": ...}` dicts (replay), or
  - the dict-of-name→version shape currently in `session_start`.
  Normalise to `(name, version)` tuples internally.

## ALGORITHM

```
format_runtime_banner(d):
    lines = [f"mcp-coder {d.get('mcp_coder_version', 'unknown')}"]
    if utils_ver := d.get("mcp_coder_utils_version"):
        lines.append(f"mcp-coder-utils {utils_ver}")
    for name, version in _normalise_mcp_servers(d.get("mcp_servers")):
        suffix = _connection_status_suffix(name, d.get("mcp_connection_status"))
        lines.append(f"{name} {version}  {suffix}".rstrip())
    tool_env = d.get("tool_env_path") or d.get("tool_env")
    if tool_env: lines.append(f"Tool env:    {tool_env}")
    venv = d.get("project_venv_path") or d.get("project_venv")
    if venv: lines.append(f"Project env: {venv}")
    if pd := d.get("project_dir"): lines.append(f"Project dir: {pd}")
    return lines
```

## DATA

- Input: `Mapping[str, object]` with the keys listed above.
- Output: `list[str]`.

## Test Cases

1. Pass a live-shaped dict (matching `RuntimeInfo`'s field names) →
   returns the existing line set.
2. Pass a `session_start`-shaped dict (matching the JSONL payload) →
   returns the same content, possibly minus the connection-status
   suffix when status data is absent.
3. Missing `mcp_servers` key → no server lines, no exception.
4. Connection status with one ok and one error server → suffixes
   `"✓ Connected"` and `"✗ <text>"` are correct.
5. Snapshot test of `on_mount` continues to pass (no visual change).

## Out of Scope

- Replay calling this helper — Step 8.
- Banner-on-resume ordering — Step 11.
