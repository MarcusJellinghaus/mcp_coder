# Internal (mcp-coder repo only)

Files used in the mcp-coder repository itself but not relevant to target repos.

## icoder Launchers

| File | Purpose |
|---|---|
| `icoder_local.bat` | Launches iCoder using local venv for testing source changes |

## MLflow Tooling

Internal scripts for inspecting mcp-coder's own LLM call history during development:

| File | Purpose |
|---|---|
| `tools/mlflow/start_mlflow.sh` / `.bat` | Start the local mlflow tracking server |
| `tools/mlflow/get_mlflow_config.py` | Read mlflow config |
| `tools/mlflow/get_latest_mlflow_db_entries.py` | Inspect recent mlflow DB entries |
| `tools/mlflow/get_recent_mlflow_runs.py` | List recent mlflow runs |
| `tools/mlflow/inspect_mlflow_run.py` | Inspect a specific mlflow run |
| `tools/mlflow/search_mlflow_artifacts.py` | Search mlflow artifacts |
| `tools/mlflow/extract_permission_events.py` / `analyze_permission_events.py` | Harvest & analyse permission (denial) events |

See [`tools/mlflow/README.md`](../../tools/mlflow/README.md) for the full list.

## Other Internal Scripts

| File | Purpose |
|---|---|
| `tools/reinstall_local.bat`, `tools/reinstall_local.sh` | Editable dev reinstall via `mcp-coder install` |
| `tools/read_github_deps.py` | Read GitHub dependency info (still used by CI workflows) |
| `tools/safe_delete_folder.py` | Safe folder deletion helper |
| `tools/jenkins_builds.py` (+ `.bat` / `.sh`) | List recent Jenkins builds with time, status, folder, job, build number and display name; defaults to the configured `executor_job_path` |
| `tools/jenkins_download_logs.py` (+ `.bat` / `.sh`) | Download console logs of recent Jenkins builds (default: failure, aborted, unstable), named by display name, plus an `index.csv` |
| `tools/jenkins_classify_logs.py` (+ `.bat` / `.sh`) | Tag downloaded logs with issue ids from `tools/jenkins_issue_patterns.toml` and add target repo and package versions to `index.csv`; workflow in `tools/jenkins_issue_analysis.md` |
| `tools/__init__.py` | Makes `tools/` an importable Python package |

## Internal CI Workflows

| File | Purpose |
|---|---|
| `.github/workflows/langchain-integration.yml` | Tests mcp-coder's own langchain integration |
| `.github/workflows/publish.yml` | Publishes the mcp-coder package to PyPI |

## IDE Configuration

| File | Purpose |
|---|---|
| `.run/` | IntelliJ/PyCharm run configurations (IDE-specific local convenience) |
