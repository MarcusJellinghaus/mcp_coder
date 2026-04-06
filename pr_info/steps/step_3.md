# Step 3: Refactor `config_reader.py` to thin wrapper

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

Make `formatters/config_reader.py` delegate to `pyproject_config.py` instead of reading `pyproject.toml` directly. Existing tests must pass without changes.

## Changes

### MODIFY: `src/mcp_coder/formatters/config_reader.py`

**BEFORE:** Contains full `tomllib` reading logic and `check_line_length_conflicts` implementation.

**AFTER:** Thin wrapper that imports from `pyproject_config`.

```python
"""Configuration reading for formatters with line-length conflict detection."""

from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.pyproject_config import check_line_length_conflicts  # noqa: F401 — re-export
from ..utils.pyproject_config import get_formatter_config


def read_formatter_config(config_file: str = "pyproject.toml") -> Dict[str, Any]:
    """Read formatter configuration from pyproject.toml file.
    
    Args:
        config_file: Path to the configuration file (default: "pyproject.toml")
    
    Returns:
        Dictionary containing formatter configurations
    """
    config_path = Path(config_file)
    return get_formatter_config(config_path.parent)
```

**HOW — integration:**
- `check_line_length_conflicts` is re-exported (imported and available via this module's namespace)
- `read_formatter_config` delegates to `get_formatter_config`, translating the file path to a directory
- The `formatters/__init__.py` import `from .config_reader import check_line_length_conflicts, read_formatter_config` continues to work unchanged

**IMPORTANT NOTE on `read_formatter_config` signature:** The existing function takes a `config_file` path string (e.g. `"pyproject.toml"` or a full path). The new `get_formatter_config` takes a `project_dir` (directory). The wrapper must bridge this by using `Path(config_file).parent` — but when `config_file` is just `"pyproject.toml"` (relative, no directory), `Path("pyproject.toml").parent` returns `Path(".")` which is correct (CWD). The existing tests pass a temp file path, so `Path("/tmp/xxx.toml").parent` gives the temp dir — also correct.

However, `get_formatter_config` constructs `project_dir / "pyproject.toml"` internally, so the filename from the original path is lost. Check if any caller passes a non-standard filename. If the existing tests use `suffix=".toml"` with `NamedTemporaryFile`, the filename won't be `pyproject.toml`. In that case, `get_formatter_config` needs an optional `config_file` parameter, OR the wrapper needs to handle this case.

**Resolution:** Keep `get_formatter_config` accepting `project_dir: Path` only (KISS). The wrapper `read_formatter_config` handles the legacy interface: if the file exists at the given path, read it directly. This preserves backward compatibility for tests.

```python
def read_formatter_config(config_file: str = "pyproject.toml") -> Dict[str, Any]:
    config_path = Path(config_file)
    if config_path.name == "pyproject.toml":
        return get_formatter_config(config_path.parent)
    # Legacy: caller passed a non-standard filename (e.g. temp file in tests)
    return _read_formatter_config_from_file(config_path)
```

Where `_read_formatter_config_from_file` is a small private function preserving the original `tomllib` logic for backward compat with test temp files. Alternatively, make `get_formatter_config` accept an optional filename override.

**Simplest approach:** Add an optional `filename` parameter to `get_formatter_config`:

```python
def get_formatter_config(project_dir: Path, filename: str = "pyproject.toml") -> dict[str, Any]:
```

Then the wrapper becomes:
```python
def read_formatter_config(config_file: str = "pyproject.toml") -> Dict[str, Any]:
    config_path = Path(config_file)
    return get_formatter_config(config_path.parent, filename=config_path.name)
```

## Verification

- All existing `tests/formatters/test_config_reader.py` tests pass unchanged
- `formatters/__init__.py` imports still work
- pylint, mypy, pytest all clean

## Commit

```
refactor: delegate config_reader to pyproject_config (#640)
```

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Refactor src/mcp_coder/formatters/config_reader.py to be a thin wrapper that delegates 
to src/mcp_coder/utils/pyproject_config.py. The existing tests in 
tests/formatters/test_config_reader.py must pass without modification. Pay attention to 
the config_file parameter — existing tests pass temp file paths with non-standard names.
Run all quality checks.
```
