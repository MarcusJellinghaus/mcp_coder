# Step 2 — Banner: render `mcp-coder-utils` line in `on_mount`

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step (`pr_info/steps/step_2.md`) in full before making changes. Implement Step 2 only — add the `mcp-coder-utils` banner line to `ICoderApp.on_mount` and verify it renders correctly. Step 1 must already be merged (the `RuntimeInfo.mcp_coder_utils_version` field must exist). Follow TDD: add the new banner-output test in `tests/icoder/ui/test_app.py` first, then implementation. Run all three MCP quality checks until green. Produce **exactly one commit**. Do not touch `info.py` — that is Step 3.

## WHERE

- Source: `src/mcp_coder/icoder/ui/app.py` (around line 106, in `on_mount`)
- Test:   `tests/icoder/ui/test_app.py` (mirrors src structure per planning principle). No banner-output assertion exists there today. **Two changes** to this file: extend the `make_icoder_app` factory to accept an optional `runtime_info` kwarg (so the banner branch in `on_mount` can render), and add a new focused test using that kwarg plus `OutputLog.recorded_lines`.

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

Two changes to `tests/icoder/ui/test_app.py` (the file mirrors `src/mcp_coder/icoder/ui/app.py`):

### 1. Extend `make_icoder_app` to accept an optional `runtime_info`

The current factory builds `AppCore(llm_service=llm, event_log=event_log)` with no `runtime_info`, so `on_mount`'s `if self._core.runtime_info:` gate skips the banner block entirely. Extend the factory to forward an optional `runtime_info` kwarg through to `AppCore`. The default (kwarg omitted / `None`) **must remain unchanged** so all existing tests in this file continue to pass without edits:

```python
@pytest.fixture
def make_icoder_app(
    event_log: EventLog,
) -> Callable[..., ICoderApp]:
    """Factory to create ICoderApp with custom FakeLLM responses."""

    def _factory(
        *,
        responses: list[list[StreamEvent]] | None = None,
        runtime_info: RuntimeInfo | None = None,   # ← NEW
    ) -> ICoderApp:
        llm = FakeLLMService(responses=responses or [])
        return ICoderApp(
            AppCore(
                llm_service=llm,
                event_log=event_log,
                runtime_info=runtime_info,         # ← NEW (None preserves old behavior)
            ),
        )

    return _factory
```

Add `from mcp_coder.icoder.env_setup import RuntimeInfo` (and `MCPServerInfo` if needed) to the imports at the top of the file.

### 2. Add the new banner-output test

It uses the extended factory to inject a `RuntimeInfo` with `mcp_coder_utils_version` populated, runs the app via `app.run_test()`, and asserts that `OutputLog.recorded_lines` contains an `mcp-coder-utils <version>` line:

```python
async def test_banner_renders_mcp_coder_utils_version(
    make_icoder_app: Callable[..., ICoderApp],
) -> None:
    """on_mount banner includes the mcp-coder-utils version line."""
    runtime_info = RuntimeInfo(
        mcp_coder_version="9.9.9",
        mcp_coder_utils_version="1.2.3",
        python_version="3.12.0",
        claude_code_version="unknown",
        tool_env_path="/tmp/tool-env",
        project_venv_path="/tmp/proj-venv",
        project_dir="/tmp/proj",
        env_vars={},
        mcp_servers=[],
    )
    app = make_icoder_app(responses=[], runtime_info=runtime_info)
    async with app.run_test() as pilot:
        await pilot.pause()
        lines = app.query_one(OutputLog).recorded_lines
        joined = "\n".join(lines)
        assert any(line.startswith("mcp-coder-utils 1.2.3") for line in lines), joined
```

> Field set matches `RuntimeInfo` after Step 1 lands (new `mcp_coder_utils_version` placed right after `mcp_coder_version`; `mcp_connection_status` left at its `None` default).

No other test file needs to be touched.

## Files modified

- `src/mcp_coder/icoder/ui/app.py` — one new line in the `on_mount` `lines` list.
- `tests/icoder/ui/test_app.py` — extend `make_icoder_app` factory with optional `runtime_info` kwarg AND add the new `test_banner_renders_mcp_coder_utils_version` test (plus the `RuntimeInfo` import).

## Acceptance

- `mcp__tools-py__run_pytest_check` passes (use markers/exclusions per CLAUDE.md).
- `mcp__tools-py__run_pylint_check` clean.
- `mcp__tools-py__run_mypy_check` clean.
- One commit, message e.g. `feat(icoder): show mcp-coder-utils version in startup banner`.
