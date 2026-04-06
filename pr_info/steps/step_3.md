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
    return get_formatter_config(config_path.parent, filename=config_path.name)
```

**HOW — integration:**
- `check_line_length_conflicts` is re-exported (imported and available via this module's namespace)
- `read_formatter_config` delegates to `get_formatter_config`, translating the file path to a directory and passing the filename
- The `formatters/__init__.py` import `from .config_reader import check_line_length_conflicts, read_formatter_config` continues to work unchanged

**Step 2 dependency:** `get_formatter_config` must have the `filename` parameter: `get_formatter_config(project_dir: Path, filename: str = "pyproject.toml")`.

### MODIFY: `src/mcp_coder/formatters/__init__.py`

The `_check_line_length_conflict` function (around line 65) independently reads `pyproject.toml` using `tomllib`, duplicating the logic now in `pyproject_config`. Refactor it to delegate:

```python
# Remove: import tomllib (no longer needed for this function)
# Replace _check_line_length_conflict body with:
from ..utils.pyproject_config import get_formatter_config

def _check_line_length_conflict() -> None:
    config = get_formatter_config(Path("."))
    black_len = config.get("black", {}).get("line-length")
    isort_len = config.get("isort", {}).get("line_length")
    if black_len is None and isort_len is None:
        return
    effective_black = black_len if black_len is not None else 88
    effective_isort = isort_len if isort_len is not None else 88
    if effective_black != effective_isort:
        logger.warning(
            "line-length mismatch: black=%s, isort=%s",
            effective_black,
            effective_isort,
        )
```

**Approach:** Use `get_formatter_config()` for reading the config (eliminating the direct `tomllib` import), but keep the existing default-to-88 comparison logic in this function. Do **not** delegate to `check_line_length_conflicts` — that utility has different behavior (it does not default missing values to 88). This function retains its own comparison semantics while using the shared I/O layer.

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
to src/mcp_coder/utils/pyproject_config.py. Also refactor 
src/mcp_coder/formatters/__init__.py to use get_formatter_config for reading config 
(removing the direct tomllib import), but keep its own default-to-88 comparison logic 
rather than delegating to check_line_length_conflicts (which has different behavior). The existing tests in 
tests/formatters/test_config_reader.py must pass without modification.
Run all quality checks.
```
