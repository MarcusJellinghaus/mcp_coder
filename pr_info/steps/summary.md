# Summary — Issue #949: full `~/.mcp_coder` cleanup via `get_user_app_data_dir`

## Goal
Adopt `mcp_coder_utils.user_app_data.get_user_app_data_dir` at every site in
`mcp_coder` that resolves a per-user data directory. Fix the Linux/macOS
asymmetry where `get_config_file_path()` and `get_sessions_file_path()`
resolve to `~/.config/mcp_coder/` while the rest of the codebase always uses
`~/.mcp_coder/`. After this work, every platform (Windows / Linux / macOS)
uses `~/.mcp_coder/`.

Root cause being fixed: that asymmetry breaks GitHub-token lookup downstream
in `mcp-workspace` (issue #184 there).

## Architectural / Design Change
Single design decision: a new local shim file
`src/mcp_coder/utils/user_app_data.py` that re-exports
`get_user_app_data_dir` from `mcp_coder_utils.user_app_data`. Matches the
existing 3-shim pattern (`subprocess_runner`, `subprocess_streaming`,
`log_utils`).

Why a shim and not a direct import? The `mcp_coder_utils_isolation`
import-linter contract forbids any `mcp_coder/` module from importing
`mcp_coder_utils` directly — only designated shim files may. The contract
must be updated in lock-step (added `ignore_imports` entry) when the new
shim is created.

After the shim lands, `get_config_file_path()` collapses to a one-line
delegation. Two platform-branching `if platform.system() == "Windows": ...`
blocks (in `user_config.py` and `vscodeclaude/sessions.py`) are removed
along with their associated platform-branching tests. `import platform` is
removed from `user_config.py`; kept in `vscodeclaude/sessions.py` (still
used for `VSCODE_PROCESS_NAMES`).

`tools/*.py` MLflow scripts also adopt the shim. The never-correct
hyphenated phantom path `~/.config/mcp-coder/config.toml` is dropped from
their config-discovery lists, including a redundant phantom-path line in a
`get_latest_mlflow_db_entries.py` error message.

No migration or fallback-read logic — `mcp_coder` has no Linux/macOS
users yet. Windows users see no change.

## Files Created / Modified

### Created
- `src/mcp_coder/utils/user_app_data.py` — new shim
- `pr_info/steps/summary.md` — this file
- `pr_info/steps/step_1.md` … `pr_info/steps/step_5.md` — per-step details

### Modified — Source
- `.importlinter` — add `mcp_coder.utils.user_app_data -> mcp_coder_utils` to `mcp_coder_utils_isolation` `ignore_imports`
- `src/mcp_coder/utils/user_config.py` — `get_config_file_path` → one-liner; drop `import platform`; update its own docstring
- `src/mcp_coder/llm/storage/session_storage.py` — replace `Path.home() / ".mcp_coder" / "sessions" / "langchain"`
- `src/mcp_coder/llm/storage/session_finder.py` — replace same path
- `src/mcp_coder/workflows/vscodeclaude/sessions.py` — `get_sessions_file_path` → single helper call; drop platform branch; update docstring

### Modified — Tools
- `tools/extract_mlflow_tool_calls.py` — single config path via shim, drop phantom fallback
- `tools/get_latest_mlflow_db_entries.py` — same; **delete line 352** (redundant phantom-path error line)
- `tools/get_mlflow_config.py` — single config path via shim
- `tools/get_recent_mlflow_runs.py` — single config path via shim
- `tools/inspect_mlflow_run.py` — same; drop phantom fallback
- `tools/search_mlflow_artifacts.py` — same; drop phantom fallback

### Modified — Tests
- `tests/utils/test_user_config.py` — delete `TestGetConfigFilePath`; add one thin assertion for the shim
- `tests/utils/test_user_config_integration.py` — delete `test_config_directory_creation_path_verification` and `test_path_consistency`
- `tests/workflows/vscodeclaude/test_sessions.py` — delete `test_get_sessions_file_path_linux`; rename `_windows` variant to drop the platform suffix
- `tests/cli/commands/test_verify_exit_codes.py` — fixture: `"/home/user/.config/mcp_coder/config.toml"` → `~/.mcp_coder/config.toml`

### Modified — Docs (mechanical sweep, replace `~/.config/mcp_coder` → `~/.mcp_coder`)
- `docs/cli-reference.md`
- `docs/coordinator-vscodeclaude.md`
- `docs/configuration/config.md` — also drop XDG framing in Linux/Containers subsection (~lines 920-930); keep Docker volume-mount example with updated path
- `docs/configuration/mlflow-integration.md` — also collapse Windows/Linux platform bullet list to a single "All platforms" line

(The other docs files — `docs/architecture/architecture.md`,
`docs/configuration/claude-code.md`, `docs/getting-started/label-setup.md`,
`docs/repository-setup/github.md`, `docs/repository-setup/README.md` — are
already clean of `.config/mcp_coder` patterns; verified by grep.)

### Sites NOT touched (already correct after the change)
- `src/mcp_coder/cli/commands/verify.py:330` — string literal already `"~/.mcp_coder/config.toml"`
- `src/mcp_coder/utils/jenkins_operations/client.py:7,76` — docstrings already say `~/.mcp_coder/config.toml`

## Step Plan (5 commits)

| Step | Commit theme | Touches |
|------|--------------|---------|
| 1 | Shim + importlinter + `get_config_file_path` one-liner + tests | new shim, `.importlinter`, `user_config.py`, `tests/utils/test_user_config*.py`, fixture in `tests/cli/commands/test_verify_exit_codes.py` |
| 2 | Langchain session storage adopts shim | `session_storage.py`, `session_finder.py`, related tests if any |
| 3 | vscodeclaude sessions adopts shim | `vscodeclaude/sessions.py`, `tests/workflows/vscodeclaude/test_sessions.py` |
| 4 | tools/*.py MLflow scripts adopt shim, drop phantom path | 6 files in `tools/`, including line 352 deletion |
| 5 | Docs sweep | 4 docs files |

Each step is self-contained: tests + implementation + all checks pass before
proceeding to the next.

## Acceptance (rolled up across all 5 steps)
- New shim re-exports `get_user_app_data_dir`.
- `.importlinter` updated; `lint-imports` passes.
- `get_config_file_path` body is a one-liner.
- All `Path.home() / ".mcp_coder"` and `Path.home() / ".config" / "mcp_coder"` patterns replaced in `src/` and `tools/`.
- Phantom `~/.config/mcp-coder/config.toml` removed; `get_latest_mlflow_db_entries.py:352` deleted.
- Platform-branching tests removed/updated.
- Docs use a single `~/.mcp_coder/` path.
- `mcp-coder verify` and `mcp-coder init` show `~/.mcp_coder/config.toml` on every platform.
- `pytest`, `pylint`, `mypy`, `lint-imports` all pass.
