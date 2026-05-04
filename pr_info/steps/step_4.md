# Step 4 — Adopt shim in `tools/*.py` MLflow scripts; drop phantom path

## LLM Prompt
> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_4.md`. Six standalone scripts in `tools/` each
> have a small `get_mlflow_db_path()` (or similar) function that
> hardcodes config-file locations. Replace those locations with a
> single shim call and drop the never-correct hyphenated phantom
> fallback. Also delete the redundant phantom-path line at
> `tools/get_latest_mlflow_db_entries.py:352`. Run all four checks
> before committing.

## Why this is one commit
All six tools share the same pattern; bundling them keeps the
"phantom-path removed" change atomic and reviewable.

## WHERE
- **Modify**: `tools/extract_mlflow_tool_calls.py`
- **Modify**: `tools/get_latest_mlflow_db_entries.py` *(includes line 352 deletion)*
- **Modify**: `tools/get_mlflow_config.py`
- **Modify**: `tools/get_recent_mlflow_runs.py`
- **Modify**: `tools/inspect_mlflow_run.py`
- **Modify**: `tools/search_mlflow_artifacts.py`

## WHAT

### Common pattern in all 6 files
Replace any of:
```python
config_paths = [
    Path.home() / ".mcp_coder" / "config.toml",
    Path.home() / ".config" / "mcp-coder" / "config.toml",   # phantom
]
for config_path in config_paths:
    if config_path.exists():
        ...
```
or
```python
config_path = Path.home() / ".mcp_coder" / "config.toml"
```
With a single discovery line:
```python
config_path = get_user_app_data_dir("mcp_coder") / "config.toml"
if config_path.exists():
    ...
```

### Special case — `tools/get_latest_mlflow_db_entries.py:352`
Inside the "Error: MLflow database not found" branch around line 348-353,
**delete the line**:
```python
print(f"  - Config: {Path.home() / '.config' / 'mcp-coder' / 'config.toml'}")
```
The line above already prints the resolved `db_path`. No replacement.

## HOW
At the top of each script, add:
```python
from mcp_coder.utils.user_app_data import get_user_app_data_dir
```
Tools sit outside the `mcp_coder/` package (and outside the import-linter
contract) so absolute imports are required.

## ALGORITHM
For each tool's `get_mlflow_db_path()` (or equivalent):
```
1. Compute config_path = get_user_app_data_dir("mcp_coder") / "config.toml"
2. If not config_path.exists(): return Path.home() / "mlflow_data" / "mlflow.db"
3. Read config, extract tracking_uri, parse sqlite:/// prefix
4. Return resolved Path
```
(Existing logic for steps 3-4 stays; only step 1 changes.)

## DATA
No new data structures. Resolved DB path is unchanged on Windows;
unchanged on Linux/macOS too because the only path the tools ever
*successfully* read on Linux/macOS today is `~/.mcp_coder/config.toml`
(the hyphenated alt path never matched).

## Test changes
None — `tools/` scripts have no unit tests. Manual smoke-test by
running one (e.g. `python tools/get_mlflow_config.py`) is optional but
recommended; no automated coverage exists or is being added.

## Verification
1. `mcp__tools-py__run_pytest_check` (fast unit tests — won't touch tools/ but must still be green)
2. `mcp__tools-py__run_pylint_check`
3. `mcp__tools-py__run_mypy_check`
4. `mcp__tools-py__run_lint_imports_check`
5. Commit message: `tools: route MLflow scripts through user_app_data shim, drop phantom config path`
