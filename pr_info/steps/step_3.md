# Step 3 — icoder startup banner surfaces tool status + count

**Commit:** `feat: show MCP tools exposed in icoder startup banner`

Implements acceptance item 3. Depends on Step 1's `find_exposed_mcp_tools`.
See `summary.md` (incl. the startup-latency tradeoff).

## WHERE
- **Impl:** `src/mcp_coder/icoder/env_setup.py` (RuntimeInfo + probe)
- **Wiring:** `src/mcp_coder/cli/commands/icoder.py` (pass provider + mcp_config)
- **Banner:** `src/mcp_coder/icoder/ui/runtime_banner.py`
- **Replay:** `src/mcp_coder/icoder/core/event_log.py` (`emit_session_start`)
- **Tests:** `tests/icoder/test_env_setup.py`, `tests/icoder/test_runtime_banner.py`
  (match the actual existing filenames in `tests/icoder/`).

## WHAT
`RuntimeInfo` (frozen dataclass) gains two optional fields:
```python
mcp_tools_exposed: int | None = None     # count of mcp__* tools at init
mcp_tools_status: str | None = None      # "connected" | "pending" | "fatal" | None
```
`setup_icoder_environment` signature gains two params (back-compat defaults):
```python
def setup_icoder_environment(
    project_dir: Path,
    provider: str = "claude",
    mcp_config: str | None = None,
) -> RuntimeInfo:
```
New guarded private helper:
```python
def _probe_exposed_mcp_tools(
    provider: str, mcp_config: str | None, env_vars: dict[str, str], execution_dir: str,
) -> tuple[str | None, int | None]:
    """Return (status, count) via one short 'Reply with OK' prompt; (None, None) on any failure."""
```

## HOW
- `_probe_exposed_mcp_tools` (Claude only; returns `(None, None)` otherwise):
  ```python
  from mcp_coder.llm.interface import prompt_llm
  from mcp_coder.llm.providers.claude.claude_mcp_guard import (
      find_exposed_mcp_tools, find_fatal_mcp_servers, find_unavailable_mcp_servers,
  )
  ```
  Call `prompt_llm("Reply with OK", provider="claude", timeout=30,
  mcp_config=mcp_config, env_vars=env_vars, execution_dir=execution_dir)`,
  read `resp["raw_response"]["system"]`, derive status (fatal→"fatal",
  else pending→"pending", else "connected") and `len(find_exposed_mcp_tools(sm))`.
  Wrap the whole body in `try/except Exception` → return `(None, None)` and log
  at debug. Never raise (must not block launch).
- In `setup_icoder_environment`, after computing `effective`/servers, call the
  probe and store both values on the returned `RuntimeInfo`.
- In `icoder.py`, move provider + mcp_config resolution **above** the
  `setup_icoder_environment(...)` call and pass them:
  `setup_icoder_environment(project_dir, provider=provider, mcp_config=mcp_config)`.
  (`resolve_llm_method` / `parse_llm_method_from_args` / `resolve_mcp_config_path`
  already have no dependency on `runtime_info`, so the reorder is safe.)
- `runtime_banner.format_runtime_banner`: after the per-server lines, add:
  ```python
  count = data.get("mcp_tools_exposed")
  if count is not None:
      status = data.get("mcp_tools_status") or ""
      suffix = f" ({status})" if status else ""
      lines.append(f"MCP tools:   {count} exposed{suffix}")
  ```
  `format_runtime_info` passes the two new fields into the mapping.
- `emit_session_start`: inside the `if runtime_info is not None:` block add
  `payload["mcp_tools_exposed"] = runtime_info.mcp_tools_exposed` and
  `payload["mcp_tools_status"] = runtime_info.mcp_tools_status`, so replay
  banners show the same line (keys already flow through `format_runtime_banner`).

## ALGORITHM (status derivation)
```
sm = resp["raw_response"]["system"]
if find_fatal_mcp_servers(sm):                      status = "fatal"
elif find_unavailable_mcp_servers(sm):              status = "pending"   # non-fatal remainder
else:                                               status = "connected"
count = len(find_exposed_mcp_tools(sm))
```

## DATA
- Banner line: `MCP tools:   37 exposed (connected)` (omitted entirely when count is None).
- `RuntimeInfo.mcp_tools_exposed: int | None`, `RuntimeInfo.mcp_tools_status: str | None`.

## TESTS (write first)
`test_env_setup.py` (mock `prompt_llm`):
- provider `"langchain"` → fields stay `None` (probe not run).
- provider `"claude"`, mocked response with connected init + 3 `mcp__*` tools →
  `mcp_tools_exposed == 3`, `mcp_tools_status == "connected"`.
- `prompt_llm` raises → fields `None`, no exception propagates.
`test_runtime_banner.py`:
- mapping with `mcp_tools_exposed=37, mcp_tools_status="connected"` → a
  `MCP tools:` line is present; with `None` → no such line.

## LLM PROMPT
> Implement Step 3 from `pr_info/steps/step_3.md` (context + the startup-latency
> tradeoff in `pr_info/steps/summary.md`). TDD first: add tests to
> `tests/icoder/test_env_setup.py` (mock `prompt_llm`: langchain→None,
> claude→count/status, exception→None) and `tests/icoder/test_runtime_banner.py`
> (line present when count set, absent when None). Then add the two optional
> `RuntimeInfo` fields and the guarded `_probe_exposed_mcp_tools` helper in
> `env_setup.py`; give `setup_icoder_environment` `provider`/`mcp_config`
> params; reorder `icoder.py` to resolve and pass them; render the line in
> `runtime_banner.py`; include the fields in `emit_session_start`. The probe
> must never raise. Run pylint/pytest (`-n auto`, integration-excluded)/mypy,
> fix all, format, single commit.
