# Step 2 — Banner: render `mcp-coder-utils` line in `on_mount`

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step (`pr_info/steps/step_2.md`) in full before making changes. Implement Step 2 only — add the `mcp-coder-utils` banner line to `ICoderApp.on_mount` and verify it renders correctly. Step 1 must already be merged (the `RuntimeInfo.mcp_coder_utils_version` field must exist). Follow TDD: add the new banner-output test in `tests/icoder/ui/test_app.py` first, then implementation. Run all three MCP quality checks until green. Produce **exactly one commit**. Do not touch `info.py` — that is Step 3.

## WHERE

- Source: `src/mcp_coder/icoder/ui/app.py` (around line 106, in `on_mount`)
- Test:   `tests/icoder/ui/test_app.py` (mirrors src structure per planning principle). No banner-output assertion exists there today — add a new focused test using the existing `make_icoder_app` fixture and `OutputLog.recorded_lines`.

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

Add a new focused test `test_banner_renders_mcp_coder_utils_version` in `tests/icoder/ui/test_app.py` (the file mirrors `src/mcp_coder/icoder/ui/app.py`). It uses the existing `make_icoder_app` fixture, runs the app via `app.run_test()`, and asserts that `OutputLog.recorded_lines` (joined with newlines) contains an `mcp-coder-utils <version>` line:

```python
async def test_banner_renders_mcp_coder_utils_version(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """on_mount banner includes the mcp-coder-utils version line."""
    app = make_icoder_app(responses=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        lines = app.query_one(OutputLog).recorded_lines
        joined = "\n".join(lines)
        assert any(line.startswith("mcp-coder-utils ") for line in lines), joined
```

If `make_icoder_app` does not already provide a `RuntimeInfo` with `mcp_coder_utils_version` populated, extend the factory (or pass a stub `AppCore`) so the banner can render the new line. No other test file needs to be touched.

## Acceptance

- `mcp__tools-py__run_pytest_check` passes (use markers/exclusions per CLAUDE.md).
- `mcp__tools-py__run_pylint_check` clean.
- `mcp__tools-py__run_mypy_check` clean.
- One commit, message e.g. `feat(icoder): show mcp-coder-utils version in startup banner`.
