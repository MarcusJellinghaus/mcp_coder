# Step 2 — Banner: render `mcp-coder-utils` line in `on_mount`

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step (`pr_info/steps/step_2.md`) in full before making changes. Implement Step 2 only — add the `mcp-coder-utils` banner line to `ICoderApp.on_mount` and verify it renders correctly. Step 1 must already be merged (the `RuntimeInfo.mcp_coder_utils_version` field must exist). Follow TDD: if any existing banner-output test exists, extend it first; otherwise add a focused unit-style assertion. Run all three MCP quality checks until green. Produce **exactly one commit**. Do not touch `info.py` — that is Step 3.

## WHERE

- Source: `src/mcp_coder/icoder/ui/app.py` (around line 106, in `on_mount`)
- Test:   reuse existing test infrastructure under `tests/icoder/` (e.g. `test_app_pilot.py` or a new minimal test). No new test file needed unless coverage gaps require it.

## WHAT

### `on_mount` — insert one new line into the `lines` list

Current shape (lines 105–118 of `app.py`):

```python
lines = [
    f"mcp-coder {info.mcp_coder_version}",
    *(... MCP server lines ...),
    f"Tool env:    {info.tool_env_path}",
    f"Project env: {info.project_venv_path}",
    f"Project dir: {info.project_dir}",
]
```

After change:

```python
lines = [
    f"mcp-coder {info.mcp_coder_version}",
    f"mcp-coder-utils {info.mcp_coder_utils_version}",   # ← NEW
    *(... MCP server lines ...),
    f"Tool env:    {info.tool_env_path}",
    f"Project env: {info.project_venv_path}",
    f"Project dir: {info.project_dir}",
]
```

That is the **only** code change in this step.

## HOW (integration)

- Reads `info.mcp_coder_utils_version` directly from `RuntimeInfo` (already present from Step 1).
- No new imports.
- No format helpers — bare f-string, identical pattern to the line above it.
- `"unknown"` fallback is rendered as the bare word (matches `_get_claude_code_version` precedent and issue spec).

## ALGORITHM

Trivial — a single list-literal insertion. No pseudocode required.

## DATA

The `OutputLog` receives `"\n".join(lines)` styled `dim`. The new line shape:
- Happy: `"mcp-coder-utils 0.1.8"` (or dev-version variant)
- Fallback: `"mcp-coder-utils unknown"`

## Tests

If a banner-rendering test already exists in `test_app_pilot.py` (or similar), extend it to assert:

```python
assert any(line.startswith("mcp-coder-utils ") for line in recorded_lines)
```

If no such test exists, add a small focused test in `tests/icoder/ui/test_app.py` or `tests/icoder/test_app_pilot.py` using the existing `make_icoder_app` fixture and `OutputLog.recorded_lines`. Construct an `AppCore` whose `runtime_info` is a `RuntimeInfo(...)` with `mcp_coder_utils_version="0.1.8"` and assert the banner output contains the line.

> **KISS note:** if extending an existing assertion is a one-liner, prefer that over a new test function.

## Acceptance

- `mcp__tools-py__run_pytest_check` passes (use markers/exclusions per CLAUDE.md).
- `mcp__tools-py__run_pylint_check` clean.
- `mcp__tools-py__run_mypy_check` clean.
- One commit, message e.g. `feat(icoder): show mcp-coder-utils version in startup banner`.
