# Internal (mcp-coder repo only)

Files used in the mcp-coder repository itself but not relevant to downstream users.

## Design Documents

| File | Purpose |
|---|---|
| `project_idea.md` | Design notes for mcp-coder itself |
| `mlflow_implementation.md` | Implementation notes for mcp-coder's mlflow integration |

## icoder Launchers

| File | Purpose |
|---|---|
| `icoder.bat` | Launches the `mcp-coder icoder` interactive command (this repo) |
| `icoder_local.bat` | Same, using local venv for testing source changes |

## MLflow Tooling

Internal scripts for inspecting mcp-coder's own LLM call history during development:

| File | Purpose |
|---|---|
| `tools/start_mlflow.sh` / `.bat` | Start the local mlflow tracking server |
| `tools/get_mlflow_config.py` | Read mlflow config |
| `tools/get_latest_mlflow_db_entries.py` | Inspect recent mlflow DB entries |
| `tools/get_recent_mlflow_runs.py` | List recent mlflow runs |
| `tools/inspect_mlflow_run.py` | Inspect a specific mlflow run |
| `tools/search_mlflow_artifacts.py` | Search mlflow artifacts |

## Other Internal Scripts

| File | Purpose |
|---|---|
| `tools/reinstall_local.bat` | Reinstall mcp-coder from local source |
| `tools/read_github_deps.py` | Read GitHub dependency info |
| `tools/safe_delete_folder.py` | Safe folder deletion helper |
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
