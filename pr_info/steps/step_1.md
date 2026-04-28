# Step 1 — `env_setup.py`: helper + `RuntimeInfo` field

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step (`pr_info/steps/step_1.md`) in full before making changes. Implement Step 1 only — extend `RuntimeInfo` with the new field, add the `_get_package_version` helper, and update tests in `tests/icoder/test_env_setup.py`. Follow TDD: update/add tests first, then implementation, then run all three MCP quality checks (pylint, pytest, mypy) until green. Produce **exactly one commit** for this step. Do not touch `app.py` or `info.py` — those are later steps.

## WHERE

- Source: `src/mcp_coder/icoder/env_setup.py`
- Test:   `tests/icoder/test_env_setup.py`

## WHAT

### New helper in `env_setup.py`

```python
def _get_package_version(name: str) -> str:
    """Return installed version of `name`, or "unknown" if not found."""
```

### `RuntimeInfo` dataclass — add one field

```python
@dataclass(frozen=True)
class RuntimeInfo:
    mcp_coder_version: str
    mcp_coder_utils_version: str   # ← NEW (placed right after mcp_coder_version)
    python_version: str
    claude_code_version: str
    tool_env_path: str
    project_venv_path: str
    project_dir: str
    env_vars: dict[str, str]
    mcp_servers: list[MCPServerInfo]
    mcp_connection_status: list[ClaudeMCPStatus] | None = None
```

### `setup_icoder_environment` — route both lookups through the helper

Replace the existing line:
```python
version = importlib.metadata.version("mcp-coder")
```
with:
```python
mcp_coder_version = _get_package_version("mcp-coder")
mcp_coder_utils_version = _get_package_version("mcp-coder-utils")
```
…and pass `mcp_coder_utils_version=mcp_coder_utils_version` into the `RuntimeInfo(...)` constructor (positionally, immediately after `mcp_coder_version`).

## HOW (integration)

- `importlib.metadata` is already imported at the top of the module — no import changes.
- `_get_package_version` references `importlib.metadata.version` and `importlib.metadata.PackageNotFoundError`.
- Helper is module-private (leading underscore), like `_get_claude_code_version`.

## ALGORITHM (helper, ~5 lines)

```
def _get_package_version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"
```

## DATA

- Helper return type: `str` — either a PEP 440 version string (e.g. `"0.1.16.dev44+gbc165fb00"`) or the literal `"unknown"`.
- `RuntimeInfo.mcp_coder_utils_version` — same shape as `mcp_coder_version`.

## Tests (`tests/icoder/test_env_setup.py`)

### Add at top of file (new imports if needed)

Import `_get_package_version` from `mcp_coder.icoder.env_setup`.

### Add two focused tests for the helper

```python
def test_get_package_version_known() -> None:
    """Real installed package returns a non-empty, non-"unknown" version."""
    result = _get_package_version("mcp-coder")
    assert result != "unknown"
    assert result  # non-empty

def test_get_package_version_missing_returns_unknown() -> None:
    """Non-existent package falls back to "unknown"."""
    assert _get_package_version("definitely-not-a-real-pkg-xyz-926") == "unknown"
```

> **Important:** these tests must NOT be inside `TestSetupIcoderEnvironment` (which uses the `_mock_externals` fixture that patches `importlib.metadata.version` module-wide and would bypass the `try/except`). Place them as top-level functions or in their own class without that fixture.

### Update `TestSetupIcoderEnvironment.test_setup_returns_runtime_info`

Add one assertion (the `_mock_externals` mock returns `"0.42.0"` for any package name, so this works automatically):

```python
assert info.mcp_coder_utils_version == "0.42.0"
```

### Update `TestRuntimeInfoDefaults.test_mcp_connection_status_default_none`

Add the new field to the `RuntimeInfo(...)` direct instantiation:

```python
info = RuntimeInfo(
    mcp_coder_version="1.0",
    mcp_coder_utils_version="1.0",   # ← NEW
    python_version="3.12.0",
    ...
)
```

## Acceptance

- `mcp__tools-py__run_pytest_check` (with the standard `-m "not …integration"` exclusion pattern from CLAUDE.md) passes for `tests/icoder/test_env_setup.py`.
- `mcp__tools-py__run_pylint_check` clean.
- `mcp__tools-py__run_mypy_check` clean.
- One commit, message e.g. `feat(icoder): add mcp_coder_utils_version to RuntimeInfo`.
