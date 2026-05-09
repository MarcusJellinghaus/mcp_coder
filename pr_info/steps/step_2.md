# Step 2 — Platform-aware `validate_mcp_json` + author `.mcp.linux.json`

**Reference:** [summary.md](./summary.md) — issue #963.

## Goal

1. Author `.mcp.linux.json` at the repo root so this repo can itself be cloned and validated on Linux.
2. Introduce a single source of truth `_MCP_CONFIG_FILES` mapping `platform.system()` → required filename.
3. Make `validate_mcp_json` use that mapping, with a clear error message naming the missing file.

## WHERE

- **Create:** `.mcp.linux.json` (repo root) — literal copy of `.mcp.macos.json`.
- **Modify:** `src/mcp_coder/workflows/vscodeclaude/workspace.py`
- **Modify:** `tests/workflows/vscodeclaude/test_workspace.py`

## WHAT

### `.mcp.linux.json` (new)

Create as a literal copy of `.mcp.macos.json`. Same `${MCP_CODER_VENV_PATH}/<binary>` shape, no `.exe`, no backslashes, reference-project paths use `${HOME}/Documents/GitHub/...`. The two files are byte-identical for now (Linux and macOS POSIX env-var conventions match closely enough that a single file shape works).

### `workspace.py` — module-level constant

Add near the top:

```python
_MCP_CONFIG_FILES: dict[str, str] = {
    "Windows": ".mcp.json",
    "Darwin": ".mcp.macos.json",
    "Linux": ".mcp.linux.json",
}
```

### `workspace.py` — `validate_mcp_json(folder_path: Path) -> None`

Replace the hardcoded `.mcp.json` lookup with a platform-aware lookup using `_MCP_CONFIG_FILES`. On unrecognized `platform.system()` (shouldn't happen on the supported targets) fall back to `.mcp.json`.

Signature unchanged. Raises `FileNotFoundError` with a message that names both the expected file and the platform.

## HOW

- Use `platform.system()` (already imported in `workspace.py`).
- Keep the existing function signature and exception type. Only the lookup and the error message change.
- Tests use `monkeypatch.setattr("mcp_coder.workflows.vscodeclaude.workspace.platform.system", lambda: "Darwin")` (same idiom already used in existing tests).

## ALGORITHM

```
required_filename = _MCP_CONFIG_FILES.get(platform.system(), ".mcp.json")
mcp_path = folder_path / required_filename
if not mcp_path.exists():
    raise FileNotFoundError(
        f"{required_filename} not found in {folder_path}. "
        f"This file is required for Claude Code integration on {platform.system()}."
    )
```

## DATA

- `_MCP_CONFIG_FILES`: `dict[str, str]` keyed by `platform.system()` return values.
- `validate_mcp_json` return type unchanged (`None`).

## Tests (write first)

In `tests/workflows/vscodeclaude/test_workspace.py`, add a parametrized class:

```python
@pytest.mark.parametrize("system,expected_file", [
    ("Windows", ".mcp.json"),
    ("Darwin",  ".mcp.macos.json"),
    ("Linux",   ".mcp.linux.json"),
])
class TestValidateMcpJsonPerPlatform:
    def test_passes_when_required_file_present(...)
    def test_raises_when_required_file_missing(...)
    def test_does_not_accept_wrong_platform_file(...)
```

The `test_does_not_accept_wrong_platform_file` case verifies strictness for each parametrized platform: only files for *other* platforms are present in the folder, and validation must still raise. Concretely, the fixture must populate the folder as follows per parametrized run:

- **Windows run**: write `.mcp.macos.json` and `.mcp.linux.json` (NOT `.mcp.json`) → must raise.
- **Darwin run**: write `.mcp.json` and `.mcp.linux.json` (NOT `.mcp.macos.json`) → must raise.
- **Linux run**: write `.mcp.json` and `.mcp.macos.json` (NOT `.mcp.linux.json`) → must raise.

This proves the validator does not accept any file other than the one mandated for the current platform.

Assert that the `FileNotFoundError` message contains the expected filename.

## Acceptance

- `.mcp.linux.json` exists at repo root and is valid JSON.
- New parametrized tests pass on all three simulated platforms.
- Existing `validate_mcp_json` tests are updated to either use the new parametrization or remain Windows-pinned via `monkeypatch`.
- pylint, mypy, pytest clean.

## LLM prompt

> Implement Step 2 from `pr_info/steps/step_2.md`, using `pr_info/steps/summary.md` for context.
>
> Create `.mcp.linux.json` at the repo root as a byte-for-byte copy of `.mcp.macos.json`. Add a module-level `_MCP_CONFIG_FILES` constant in `src/mcp_coder/workflows/vscodeclaude/workspace.py`. Update `validate_mcp_json` to look up the platform's required filename from that mapping; raise `FileNotFoundError` with a message naming both the file and the platform.
>
> Write the parametrized tests in `tests/workflows/vscodeclaude/test_workspace.py` **first**, then implement until they pass. Include a test asserting that on Darwin, having only `.mcp.json` does NOT satisfy the check.
>
> Run the three required quality checks per `.claude/CLAUDE.md`. One commit, message: `Make validate_mcp_json platform-aware; add .mcp.linux.json (#963)`.
