# Step 1 — Config reader `get_post_install_checks`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` only.
> TDD: write the tests first, then the reader. Run pylint, mypy and the fast unit
> pytest set (see CLAUDE.md). All must pass. Run the formatter, then make one commit.

## WHERE
- `src/mcp_coder/utils/pyproject_config.py`: add the function directly after `get_install_extras`.
- `tests/utils/test_pyproject_config.py`: add the class `TestGetPostInstallChecks` after `TestGetInstallExtras` and import the new function.

## WHAT
```python
def get_post_install_checks(
    project_dir: Path, *, strict: bool = False
) -> tuple[tuple[str, ...], ...]:
    """Read [tool.mcp-coder.install] post_install_checks from pyproject.toml."""
```

## HOW
- Same structure as `get_install_extras`: `_load_pyproject(project_dir, strict=strict)`, then
  `data.get("tool", {}).get("mcp-coder", {}).get("install", {})`.
- Error message format (same style as `get_install_extras`):
  `f"Invalid [tool.mcp-coder.install] post_install_checks in {path}\n"`
  `'Expected a list of argv lists such as [["mcp-coder", "--version"]], '`
  `f"got {type(value).__name__}: {value!r}"`
- Non-strict mode: `logger.warning("Ignoring invalid [tool.mcp-coder.install] post_install_checks in %s: %r", path, value)` and return `()`.

## ALGORITHM
```
value = section.get("post_install_checks")
if value is None: return ()
valid = isinstance(value, list) and all(
    isinstance(c, list) and c and all(isinstance(a, str) for a in c) for c in value)
if valid: return tuple(tuple(c) for c in value)
if strict: raise ValueError(msg)
logger.warning(...); return ()
```

## DATA
- Returns `tuple[tuple[str, ...], ...]`. `()` means no checks: the file, section or key is absent, the value is `[]`, or the value is invalid in non-strict mode.

## Tests (`TestGetPostInstallChecks`)
- valid list → tuple of tuples, order preserved
- key absent / section absent / no pyproject.toml → `()`
- `[]` → `()`
- strict: string value, list of strings, empty inner list, non-string element → `ValueError` whose message contains the file path, `post_install_checks` and the value repr
- non-strict, same malformed values → `()` plus a warning (`caplog`)
