# Step 1 — Wrapper delegates to mcp-tools-py resolution

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` only.
> TDD: write the tests first, then the implementation. Run pylint, mypy, pytest (fast unit
> markers, `-n auto`) and lint-imports; all must pass. Format with `run_format_code`, then
> make exactly one commit.

## Precondition

`mcp_tools_py.formatter.runner` must export `run_format_code` with a `steps` parameter and
`resolve_steps`. If it does not (check with `get_library_source`), write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/mcp_tools_py.py`
- `tests/test_mcp_tools_py.py`

## WHAT

```python
from mcp_tools_py.formatter.runner import resolve_steps
from mcp_tools_py.formatter.runner import run_format_code as _run_format_code

__all__ = [..., "resolve_steps", ...]  # keep alphabetical

def run_format_code(project_dir: Union[str, Path]) -> dict[str, FormatterResult]:
    """Run the project's configured formatter.

    Raises:
        RuntimeError: If target directory resolution fails.
        ValueError: If no formatter can be resolved (from resolve_steps).
    """
```

## HOW

- Remove the lazy imports of `run_black` / `run_isort` and the step loop.
- Keep the lazy `resolve_target_directories` import and its `RuntimeError` behaviour.
- No other mcp_coder-side logic — this body is what #1195 replaces.
- Add `# noqa: DOC502` on the docstring if ruff flags the propagated `ValueError`
  (same style as mcp-tools-py's runner).

## ALGORITHM

```
root = Path(str(project_dir))
target_dirs = resolve_target_directories(str(root), None)
if isinstance(target_dirs, str): raise RuntimeError(target_dirs)
return _run_format_code(sys.executable, root, target_dirs, steps=None)
```

## DATA

`dict[str, FormatterResult]` keyed by step name in execution order
(e.g. `{"isort": ..., "black": ...}` or `{"ruff_imports": ..., "ruff_format": ...}`).

## Tests (`tests/test_mcp_tools_py.py`)

- Patch `mcp_coder.mcp_tools_py._run_format_code` and `resolve_target_directories`; assert called
  with `steps=None`, the resolved target dirs and the project root; return value passed through.
- `_run_format_code` raising `ValueError` propagates.
- `resolve_target_directories` returning a string → `RuntimeError` (keep/adjust existing test).
- `resolve_steps` importable from `mcp_coder.mcp_tools_py`.
- Remove/adjust existing tests that patch `run_isort` / `run_black`.
