# Step 3 — `/info`: migrate to `runtime_info`, add `mcp-coder-utils` line, drop import

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step (`pr_info/steps/step_3.md`) in full before making changes. Implement Step 3 only — modify `_format_info` in `commands/info.py` to (a) read `mcp-coder` version from `runtime_info.mcp_coder_version`, (b) add a new `mcp-coder-utils version:` line right after, (c) drop the now-unused `import importlib.metadata`. Update `tests/icoder/test_info_command.py` accordingly. Steps 1 and 2 must already be merged. Follow TDD: update tests first, then implementation, then run all three MCP quality checks. Produce **exactly one commit**.

## WHERE

- Source: `src/mcp_coder/icoder/core/commands/info.py`
- Test:   `tests/icoder/test_info_command.py`

## WHAT

### `commands/info.py` — three changes

1. **Remove import** (line ~5):
   ```python
   import importlib.metadata   # ← DELETE
   ```

2. **Replace existing version line** in `_format_info` (line ~53):
   ```python
   lines.append(f"mcp-coder version: {importlib.metadata.version('mcp-coder')}")
   ```
   with:
   ```python
   lines.append(f"mcp-coder version: {runtime_info.mcp_coder_version}")
   lines.append(f"mcp-coder-utils version: {runtime_info.mcp_coder_utils_version}")
   ```

That's it. No other edits in this file.

## HOW (integration)

- `runtime_info` is already a parameter of `_format_info`.
- No new imports.
- DRY: both lines now read from a single `RuntimeInfo` source.

## ALGORITHM

Trivial — text formatting. No pseudocode required.

## DATA

Output adds one line to `/info`. Example:

```
mcp-coder version: 0.1.16.dev44+gbc165fb00
mcp-coder-utils version: 0.1.8
Python:            3.12.5 (...)
```

Fallback variant: `mcp-coder-utils version: unknown`.

## Tests (`tests/icoder/test_info_command.py`)

### Update `runtime_info` fixture

Add the new field:

```python
@pytest.fixture
def runtime_info() -> RuntimeInfo:
    return RuntimeInfo(
        mcp_coder_version="0.1.0",
        mcp_coder_utils_version="0.2.0",   # ← NEW
        python_version="3.11.0",
        ...
    )
```

### Replace `test_info_shows_version`

The current test mocks `importlib.metadata.version`. After this step that import no longer exists in `info.py`, so the patch target is gone. Rewrite the test to drive both lines through `runtime_info`:

```python
@patch("mcp_coder.icoder.core.commands.info.find_claude_executable", return_value=None)
def test_info_shows_versions(
    _mock_claude: object,
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
) -> None:
    register_info(registry, runtime_info)
    result = registry.dispatch("/info")
    assert result is not None
    assert "mcp-coder version: 0.1.0" in result.text
    assert "mcp-coder-utils version: 0.2.0" in result.text
```

Drop the `@patch("...info.importlib.metadata.version", ...)` decorator entirely — the import is gone.

## Acceptance

- `mcp__tools-py__run_pytest_check` passes for `tests/icoder/test_info_command.py` (use markers/exclusions per CLAUDE.md).
- `mcp__tools-py__run_pylint_check` clean (verifies the dropped import is genuinely unused).
- `mcp__tools-py__run_mypy_check` clean.
- One commit, message e.g. `refactor(icoder): /info reads versions from runtime_info, add mcp-coder-utils line`.
