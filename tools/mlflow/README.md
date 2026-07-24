# MLflow analysis tools

Helper scripts for inspecting and analysing the MLflow conversation artifacts
that mcp-coder logs for each Claude Code / LLM session. They run against the
**local** MLflow SQLite DB + on-disk artifacts (auto-detected from config) and
are **read-only**.

Run them from the repository root, e.g. `python tools/mlflow/inspect_mlflow_run.py <run_id>`.

## Scope: headless runs vs interactive sessions

mcp-coder drives Claude Code in two very different ways, and **these tools only
see the first one:**

| | Headless workflow runs | Interactive sessions |
|---|---|---|
| Example | `mcp-coder` implement/review workflows | iCoder TUI, `claude` in a terminal |
| Tools exposed | **MCP toolset only** (+ ToolSearch), via `--mcp-config --strict-mcp-config`; native **`Bash` is never exposed** | full tool set incl. **`Bash`**, native file tools, etc. |
| Permission model | `permissionMode: default`, no human → non-allow-listed calls are **auto-denied** | human present → non-allow-listed calls **prompt for approval** |
| Logged to | **MLflow** artifacts (`conversation_data/`) | Claude Code transcripts: `~/.claude/projects/<project>/*.jsonl` |
| Analysed by | **these tools** | not yet — see below |

**Consequence:** every permission event these tools report is an **MCP allow-list
gap**. There are **zero Bash approvals** in the data — not because Bash is always
approved, but because Bash is never offered to headless runs. Any question about
bash-approval behaviour must come from the interactive transcripts instead.

## Analysing interactive sessions

`extract_interactive_events.py` covers the interactive half. It reads Claude
Code's own transcripts under `~/.claude/projects/<sanitised-project>/*.jsonl`
(one file per session; *not* MLflow), emits every `tool_use` call as an event
(same schema as the headless extractor, so `analyze_permission_events.py` can
consume it), and prints an interactive-specific summary.

```bash
python tools/mlflow/extract_interactive_events.py            # auto-detects the current repo
python tools/mlflow/extract_interactive_events.py --project-dir /path/to/repo
```

Each event carries a few interactive-only fields:

- `outcome` — `executed` / `denied_by_user` / `interrupted` / `error`. A user
  rejection is detected by the marker
  `"The user doesn't want to proceed with this tool use"` in the result.
- `was_allowlisted` — is the call pre-authorised by `.claude/settings*.json`
  `permissions.allow`? `True`/`False` for `mcp__*` tools and `Bash` (matched
  against `Bash(prefix:*)` / `Bash(exact)` rules); `None` for other native tools.
- `bash_verb` — first token of a Bash command, for grouping (`gh`, `git`, ...).

The summary's **"executed but NOT allow-listed"** list ≈ *what a human had to
approve* — the interactive counterpart of the headless `permission_denials`.

Caveats: **approvals are implicit** (an executed call was permitted, but the
transcript doesn't say whether it was auto-allowed or manually clicked); Bash
matching is approximate (it doesn't split `&&`/`|` the way Claude Code does).
For an exact record, a `PreToolUse` hook logging `{tool, input, decision}` per
call would be the clean prospective source.

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
| `extract_interactive_events.py` | Harvest tool/permission events from **interactive** transcripts (see below) → `interactive_events.jsonl` + `.csv`. |

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
