# Step 2 — Config accessors + single gate in `run_formatters`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` only.
> TDD: write the tests first, then the implementation. Run pylint, mypy, pytest (fast unit
> markers, `-n auto`) and lint-imports; all must pass. Format with `run_format_code`, then
> make exactly one commit.

## WHERE

- `src/mcp_coder/utils/pyproject_config.py`
- `src/mcp_coder/workflow_steps/commit.py`
- `tests/conftest.py` (autouse fixture)
- `tests/utils/test_pyproject_config.py`
- `tests/workflow_steps/test_commit.py`

`ImplementConfig.format_code` is **not** removed in this step (step 8 does that).

## WHAT

`pyproject_config.py`:

```python
@dataclass(frozen=True)
class FormatCodeSetting:
    """[tool.mcp-coder] format_code."""
    enabled: bool   # True when absent
    explicit: bool  # True when the key is present

def get_format_code(project_dir: Path) -> FormatCodeSetting:
    """Raises: ValueError if the value is not a bool (names key and file)."""

def has_legacy_format_code_key(project_dir: Path) -> bool:
    """True if [tool.mcp-coder.implement] format_code is present."""
```

`commit.py`:

```python
class FormatterConfigError(ValueError):
    """Formatter configuration is invalid; formatting cannot run."""

def check_formatter_config(project_dir: Path, warn_legacy_key: bool = False) -> str | None:
    """None when formatting is off or resolves cleanly, else the error message."""

def run_formatters(project_dir: Path) -> bool:
    """Run the project's configured formatter.

    Returns True when formatting is disabled or all steps succeeded, False if a step failed.
    Raises: FormatterConfigError if the formatter configuration is invalid.
    """
```

## HOW

- Both accessors use `_load_pyproject(project_dir)` (non-strict: missing/malformed → `{}`).
- `commit.py` imports `resolve_steps` from `mcp_coder.mcp_tools_py` (module-level, so the test
  fixture can patch `mcp_coder.workflow_steps.commit.resolve_steps`) and the two accessors from
  `mcp_coder.utils.pyproject_config`.
- Narrowing: add `except FormatterConfigError: raise` before the existing broad `except`.
- Docstrings: replace "(black, isort)" with "the project's configured formatter".

## ALGORITHM

```
check_formatter_config(p, warn_legacy_key):
    if warn_legacy_key and has_legacy_format_code_key(p):
        logger.warning("[tool.mcp-coder.implement] format_code is ignored; use [tool.mcp-coder] format_code")
    try:
        if not get_format_code(p).enabled: return None
        resolve_steps(p); return None
    except ValueError as e: return str(e)

run_formatters(p):
    msg = check_formatter_config(p)
    if msg: raise FormatterConfigError(msg)
    if not get_format_code(p).enabled: log "formatting disabled"; return True
    ... existing loop over run_format_code(p) results (unchanged) ...
```

## DATA

- `FormatCodeSetting(enabled=True, explicit=False)` when the key is absent.
- `check_formatter_config` → `None` | message string.
- `run_formatters` → `bool`; raises `FormatterConfigError`.

## Test fixture (`tests/conftest.py`)

```python
@pytest.fixture(autouse=True)
def _resolvable_formatter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Let formatter pre-flights pass in project dirs without pyproject.toml.

    Patches the single lookup site behind check_formatter_config. Real formatting
    is unaffected (the wrapper uses mcp-tools-py's own resolve_steps). Tests of the
    helper re-patch it.
    """
    monkeypatch.setattr(
        "mcp_coder.workflow_steps.commit.resolve_steps", lambda _p: ["isort", "black"]
    )
```

## Tests

`tests/utils/test_pyproject_config.py`:
- `get_format_code`: absent → `(True, False)`; `true` → `(True, True)`; `false` → `(False, True)`;
  `"false"` (string) → `ValueError`; missing / malformed `pyproject.toml` → `(True, False)`.
- `has_legacy_format_code_key`: present → True; absent / missing file → False.

`tests/workflow_steps/test_commit.py` (patch `run_format_code` as today):
- `format_code = false` → `run_format_code` not called, returns True.
- Key absent → `run_format_code` called.
- `resolve_steps` raising `ValueError` → `FormatterConfigError` with that message propagates.
- Non-bool `format_code` → `FormatterConfigError`.
- Step failure (`success=False`) → False (unchanged).
- Revisit `:50-55`: generic exception from `run_format_code` still → False.
- `check_formatter_config`: off → None even if `resolve_steps` would raise; error → message;
  legacy warning logged only with `warn_legacy_key=True` (use `caplog`), also when `format_code = false`.
