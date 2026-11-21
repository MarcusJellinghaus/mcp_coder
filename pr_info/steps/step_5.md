# Step 5 — icoder banner and event log show the required servers (Scope 3)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_5.md`).
> Implement Step 5 only: the start-up banner, `format_runtime_info` and the
> `session_start` event show `RuntimeInfo.required_mcp_servers` with their
> `claude mcp list` status; old logs without the new key fall back to
> `mcp_servers` inside `format_runtime_banner`. Tests first, then code. Run
> format, pylint, mypy and the fast pytest set (plus `textual_integration`
> snapshot tests if any banner snapshot changes). One commit.

## WHERE

- `src/mcp_coder/icoder/core/event_log.py` — `emit_session_start`
- `src/mcp_coder/icoder/ui/runtime_banner.py` — `format_runtime_banner`, `format_runtime_info`
- `src/mcp_coder/icoder/ui/replay.py` — unchanged (passes the raw event)
- Tests: existing banner / event-log tests under `tests/icoder/`; add cases there
  or in `tests/icoder/test_required_servers.py` (created in Step 4)

## WHAT

- `session_start` payload gains `"required_mcp_servers": list(runtime_info.required_mcp_servers)`.
  `mcp_servers` (name → version) and `mcp_connection_status` stay as they are.
- `format_runtime_info` passes `"required_mcp_servers": list(info.required_mcp_servers)`.
- `format_runtime_banner(data)` lists the required servers.

## ALGORITHM (`format_runtime_banner`, server lines)

```
versions = dict(_normalise_mcp_servers(data.get("mcp_servers")))
names = data.get("required_mcp_servers")
if not isinstance(names, (list, tuple)) or not names: names = list(versions)   # old log / no list
for name in names:
    head = f"{name} {versions[name]}" if versions.get(name) else str(name)
    lines.append(f"{head}  {_connection_status_suffix(name, statuses)}".rstrip())
```

Toolkit servers have no version (only `mcp-workspace` is binary-checked), so
their line is name + status.

## DATA

Banner line examples: `mcp-workspace 1.2.3  ✓ Connected`, `mcp-tools-py  ✗ not listed`.

## Tests (write first)

- live `RuntimeInfo` with `required_mcp_servers=("mcp-workspace", "mcp-tools-py")`,
  `mcp_servers=[mcp-workspace info]`, statuses with `mcp-tools-py` "not listed"
  → two lines, the second without a version.
- replayed event with `required_mcp_servers` key → same lines.
- replayed old event without the key → lines from `mcp_servers` (today's output).
- `emit_session_start` writes `required_mcp_servers`.
