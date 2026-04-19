# Step 1: Add `ImplementConfig` and `get_implement_config()` to pyproject_config.py

## Context
See `pr_info/steps/summary.md` for full design. This step adds the config reading layer.

## WHERE
- `src/mcp_coder/utils/pyproject_config.py` — add dataclass + function
- `tests/utils/test_pyproject_config.py` — add test class

## WHAT

### New dataclass
```python
@dataclass(frozen=True)
class ImplementConfig:
    """Configuration for the implement workflow."""
    format_code: bool
    check_type_hints: bool
```

### New function
```python
def get_implement_config(project_dir: Path) -> ImplementConfig:
    """Read [tool.mcp-coder.implement] from pyproject.toml."""
```

## HOW
Follow the exact same pattern as `get_github_install_config()`:
1. Check if `pyproject.toml` exists → return defaults if not
2. Parse with `tomllib` → return defaults on error
3. Navigate to `data["tool"]["mcp-coder"]["implement"]`
4. Read `format_code` and `check_type_hints` with `.get(key, False)`

## ALGORITHM
```
path = project_dir / "pyproject.toml"
if not path.exists(): return ImplementConfig(False, False)
data = tomllib.load(path)  # return defaults on error
section = data.get("tool", {}).get("mcp-coder", {}).get("implement", {})
return ImplementConfig(
    format_code=section.get("format_code", False),
    check_type_hints=section.get("check_type_hints", False),
)
```

## DATA
- Input: `project_dir: Path`
- Output: `ImplementConfig(format_code=bool, check_type_hints=bool)`
- Defaults: both `False`

## TESTS (write first)
Add `TestGetImplementConfig` class to `tests/utils/test_pyproject_config.py`:
1. `test_returns_both_true_when_configured` — both keys set to `true`
2. `test_defaults_to_false_when_section_missing` — `[tool.mcp-coder]` exists but no `[tool.mcp-coder.implement]`
3. `test_defaults_to_false_when_file_missing` — no `pyproject.toml`
4. `test_partial_keys_default_missing_to_false` — only `format_code` set, `check_type_hints` absent
5. `test_handles_invalid_toml` — malformed file returns defaults

## LLM PROMPT
```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_1.md.

Add ImplementConfig dataclass and get_implement_config() to pyproject_config.py,
following the exact pattern of get_github_install_config(). Write tests first in
tests/utils/test_pyproject_config.py, then implement the function.
```
