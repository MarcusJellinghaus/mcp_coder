# Step 1: Add run_format_code shim + swap caller

**Commit message:** `refactor: add run_format_code shim + swap caller`

**Context:** See `pr_info/steps/summary.md` for full issue context (#737).

## Goal

Add a thin `run_format_code` wrapper to `mcp_tools_py.py` (same pattern as the
existing `run_mypy_check`), then swap `task_processing.py` to use it instead of
`mcp_coder.formatters.format_code`. Update the existing tests for the caller.

After this step, `mcp_coder.formatters` is still on disk but has zero production
callers — making step 2 (deletion) safe.

## WHERE — Files to modify

1. `src/mcp_coder/mcp_tools_py.py` — add shim
2. `src/mcp_coder/workflows/implement/task_processing.py` — swap import + call
3. `tests/workflows/implement/test_task_processing.py` — update mocks
4. `tach.toml` — add mcp_tools_py dependency to workflows module

## WHAT — Functions and signatures

### 1. New shim in `mcp_tools_py.py`

```python
from mcp_tools_py.formatter.models import FormatterResult
from mcp_tools_py.formatter.runner import run_format_code as _run_format_code
from mcp_tools_py.utils.project_config import resolve_target_directories

def run_format_code(
    project_dir: Union[str, Path],
) -> dict[str, FormatterResult]:
    """Run code formatters (isort, black) on the project.

    Args:
        project_dir: Path to the project directory.

    Returns:
        Dict mapping formatter step name to FormatterResult.
    """
```

### 2. Updated caller in `task_processing.py`

Change import from:
```python
from mcp_coder.formatters import format_code
```
to:
```python
from mcp_coder.mcp_tools_py import run_format_code
```

Change call site in `run_formatters()` from:
```python
results = format_code(project_dir, formatters=["black", "isort"])
```
to:
```python
results = run_format_code(project_dir)
```

Change error logging from `result.error_message` to `result.output`
(mcp-tools-py's `FormatterResult` uses `.output` not `.error_message`).

### 3. Updated tests in `test_task_processing.py`

In `TestRunFormatters`:
- Change `@patch` target from `...task_processing.format_code` to `...task_processing.run_format_code`
- In `test_run_formatters_success`: change assertion from
  `mock_format_code.assert_called_once_with(Path("/test/project"), formatters=["black", "isort"])`
  to `mock_run_format_code.assert_called_once_with(Path("/test/project"))`
- In `test_run_formatters_failure`: change `mock_failed_result.error_message` to
  `mock_failed_result.output` (the field the caller now logs)

In `TestIntegration`:
- `test_error_recovery_patterns`: Change `@patch` target from `...task_processing.format_code`
  to `...task_processing.run_format_code`

### 4. tach.toml dependency update

Add `{ path = "mcp_coder.mcp_tools_py" }` to the `depends_on` list of the
`mcp_coder.workflows` module. This is needed because `task_processing.py` now
has a top-level import from `mcp_coder.mcp_tools_py`.

## HOW — Integration points

- Import isolation enforced by `.importlinter`: only `mcp_coder.mcp_tools_py` may
  import from `mcp_tools_py` library — this is already configured
- The shim follows the exact same pattern as the existing `run_mypy_check` in the
  same file: resolve internals, delegate to library function

## ALGORITHM — Shim pseudocode (5 lines)

```
def run_format_code(project_dir):
    project_root = Path(str(project_dir))
    target_dirs = resolve_target_directories(str(project_root), None)
    if isinstance(target_dirs, str):  # error message
        raise RuntimeError(target_dirs)
    return _run_format_code(sys.executable, project_root, target_dirs)
```

## DATA — Return values

- `run_format_code()` returns `dict[str, FormatterResult]`
- `FormatterResult` from mcp-tools-py:
  - `output: str` — raw tool output
  - `success: bool` — True when return_code == 0
  - `files_changed: list[str]` — parsed file paths changed
- Caller (`run_formatters`) only checks `.success` and logs `.output` on failure

## Verification

```
mcp__tools-py__run_pytest_check   (unit tests, exclude integration)
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
mcp__tools-py__run_lint_imports_check
mcp__tools-py__run_vulture_check
```
