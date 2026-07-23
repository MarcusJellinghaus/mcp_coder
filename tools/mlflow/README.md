# MLflow analysis tools

Helper scripts for inspecting and analysing the MLflow conversation artifacts
that mcp-coder logs for each Claude Code / LLM session. They run against the
**local** MLflow SQLite DB + on-disk artifacts (auto-detected from config) and
are **read-only**.

Run them from the repository root, e.g. `python tools/mlflow/inspect_mlflow_run.py <run_id>`.

## Server

| Script | Purpose |
|--------|---------|
| `start_mlflow.sh` / `start_mlflow.bat` | Start the local MLflow tracking server (uses `get_mlflow_config.py` for the tracking URI). |
| `get_mlflow_config.py` | Print the configured MLflow tracking URI. |

## Inspect / search

| Script | Purpose |
|--------|---------|
| `get_recent_mlflow_runs.py` | List recent runs (newest first). |
| `get_latest_mlflow_db_entries.py` | Dump the most recent raw DB entries for a run/experiment. |
| `inspect_mlflow_run.py` | Inspect one run's steps, tool calls and results (`--step`, `--filter`, `--show-content`). |
| `search_mlflow_artifacts.py` | Full-text search across artifacts by field (prompt / tools / ...). |

## Datasets

These build reusable datasets (JSONL + CSV) across *all* runs.

| Script | Purpose |
|--------|---------|
| `extract_mlflow_tool_calls.py` | Harvest tool-call samples (`--unique`, `--run`, `--limit`). |
| `extract_permission_events.py` | Harvest permission (approval/denial) events → `permission_events.jsonl` + `.csv`. |
| `analyze_permission_events.py` | Analyse that permission-events dataset (no DB needed). |

Default output dir for the dataset scripts is `.ml_flow_analysis/` (git-ignored).

### Permission-event workflow

```bash
# 1. Harvest denial events from every run into .ml_flow_analysis/
python tools/mlflow/extract_permission_events.py

# 2. Analyse the harvested dataset
python tools/mlflow/analyze_permission_events.py
python tools/mlflow/analyze_permission_events.py --group-by branch_name
```

`analyze_permission_events.py` classifies each denial by **cause**:

- `allowlist_gap` — the tool was connected/available (`was_available`) but not on
  `permissions.allow`; a genuine config gap.
- `naming_mismatch` — the model called a tool that wasn't connected, using a
  legacy `mcp__<server>__*` prefix (vs the current `mcp__mcp-<server>__*`).
- `not_connected` — unavailable and not a recognisable legacy name.

It also quantifies wasted retry loops (`retried_same`, `retry_count`) and the
step cost/turns spent on them, and clusters events by tool, mcp_server,
category, branch and day.

## Limitations

The actual allow-list passed to the CLI (`--settings` → `permissions.allow`) is
not logged in the artifacts, so a denial tells us a tool *was* denied but not
definitively which list it was missing from (tracked in #1057).
