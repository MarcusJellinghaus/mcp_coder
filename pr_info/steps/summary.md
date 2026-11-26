# Summary — #1419: Use mcp-coder-utils `fs` for repo text writes and the project-dir containment check

## Goal

mcp_coder and mcp-workspace should follow one line-ending rule and share one containment check. The mechanism comes from `mcp_coder_utils.fs` (mcp-coder-utils#69, merged as #88). The policy stays in mcp_coder.

**Aligned policy** (shared with mcp-workspace#400):
1. Existing file with line breaks → its dominant ending.
2. Tie, no line breaks, or new file → **LF**.

## Architectural / design changes

- **New shim `mcp_coder.utils.fs`**: re-exports only `write_text`, `dominant_newline` and `check_path_within` from `mcp_coder_utils.fs`, like `utils/user_app_data.py`. It is the only route to `mcp_coder_utils.fs`: the import-linter contract `mcp_coder_utils_isolation` gets one new `ignore_imports` entry for it. `read_file` and `normalize_path` are **not** re-exported, because their names clash with local functions that mean something else.
- **`write_lf_text` → `write_repo_text`** (`utils/text_io.py`; the module name stays). The function no longer writes LF only. It delegates to the shim: `write_text(path, text, newline=dominant_newline(existing or b"") or "\n", append=append)`. This applies to both appends and overwrites. The new name describes its purpose (text written into the target repo under the repo's line-ending policy), so it stays accurate if the policy changes.
- **One writer for user `.gitignore` appends**: `vscodeclaude/workspace.py` `update_gitignore` drops its own `open("a", newline="")` and calls `write_repo_text(..., append=True)`. Both `.gitignore` writers in `execute_init` (`update_gitignore`, `ensure_scratch_gitignored`) now follow the same rule, so a CRLF `.gitignore` stays CRLF.
- **`icoder/permissions/persist.py`**: the atomic write (temp file + replace) and the no-normalisation behaviour stay. Only the newline choice in `_read` moves to the shared rule: `dominant_newline(raw) or "\n"` replaces "CRLF if any `\r\n`".
- **`cli/utils.py` `is_outside_project_dir`**: delegates the mechanism to `check_path_within(path, Path(project_dir))`. The policy stays local:
  - `None` project dir → False
  - `ValueError` → True (outside)
  - `OSError` → False
- `tach.toml` needs no change: `utils/fs.py` falls under the existing `mcp_coder.utils` module.

## Files created / modified

| File | Change | Step |
|---|---|---|
| `src/mcp_coder/utils/fs.py` | **new** — shim | 1 |
| `tests/utils/test_fs_shim.py` | **new** — the shim exports exactly the three names | 1 |
| `.importlinter` | `ignore_imports` entry + comment without a count | 1 |
| `.claude/CLAUDE.md` | "Shared Libraries": intro without a count, widened topics, rows for `fs`, `toolkit`, `user_app_data` | 1 |
| `docs/architecture/architecture.md` | line 27: add line endings and path containment | 1 |
| `src/mcp_coder/utils/text_io.py` | rename (step 2); delegate to the shim + docstrings (step 3) | 2, 3 |
| `src/mcp_coder/cli/commands/define_labels_actions.py` | rename | 2 |
| `src/mcp_coder/cli/commands/init_file_access.py` | rename (3 calls) | 2 |
| `src/mcp_coder/cli/commands/verify.py` | rename | 2 |
| `src/mcp_coder/icoder/permissions/loader.py` | rename | 2 |
| `src/mcp_coder/workflows/create_plan/prerequisites.py` | rename | 2 |
| `src/mcp_coder/workflows/implement/task_tracker_prep.py` | rename | 2 |
| `src/mcp_coder/workflows/review/review_log.py` | rename | 2 |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | rename (step 2); `update_gitignore` via `write_repo_text` (step 4) | 2, 4 |
| `tests/utils/test_text_io.py` | rename (step 2); new tests, spy test deleted (step 3) | 2, 3 |
| `tests/cli/commands/test_init_file_access.py` | string patch target (step 2); `…_appends_lf` → `…_appends_crlf` (step 3) | 2, 3 |
| `tests/icoder/test_permissions_loader_schema.py` | string patch target | 2 |
| `tests/workflows/vscodeclaude/test_workspace.py` | parametrize the line-ending test (LF and CRLF seed) | 4 |
| `tests/cli/commands/test_init_gitignore.py` | `execute_init` on a CRLF `.gitignore` | 4 |
| `src/mcp_coder/icoder/permissions/persist.py` | `_read` newline choice + docstrings | 5 |
| `tests/icoder/test_permissions_persist.py` | mixed-file test | 5 |
| `src/mcp_coder/cli/utils.py` | `is_outside_project_dir` via `check_path_within` | 6 |
| `tests/cli/test_utils_context_root.py` | policy test (`ValueError` → True, `OSError` → False) | 6 |

## Steps

1. Shim `utils/fs.py` + import-linter, CLAUDE.md, architecture doc.
2. Rename `write_lf_text` → `write_repo_text` (pure refactor, incl. string patch targets).
3. `write_repo_text` follows the aligned policy via the shim.
4. `update_gitignore` writes via `write_repo_text`; end-to-end `execute_init` test.
5. `persist.py` newline choice via `dominant_newline`.
6. `is_outside_project_dir` via `check_path_within`.

Every step is one commit with its tests and implementation, and all checks pass at the end of each step.

## Behaviour changes (state them in the PR)

- **No longer "never writes `\r`"** (#1242's contract): an append to or overwrite of an existing CRLF file writes CRLF. New files stay LF. Overwrites of existing files keep the file's dominant ending: task-tracker reset, `tasks.json`, emitted schema, existing workflow YAML.
- **The `.gitignore` that `vscodeclaude` appends to** follows the file's dominant ending (it was always LF).
- **`persist.py` on a mixed file** follows the dominant ending (it was CRLF as soon as one `\r\n` was present).
- **A lone CR in the text is converted** to the chosen newline.
- **An encode error leaves the file intact**: an overwrite with unencodable text raises `UnicodeEncodeError` and the existing file is not emptied.
- **Requires mcp-coder-utils with `fs.write_text` / `fs.check_path_within` (#88 or later).** Nearly every command imports `cli/utils.py`, so an older install fails with `ImportError` at CLI start. There is no version pin.

## Out of scope (unchanged on purpose)

- `task_tracker_prep.py` restores `TASK_TRACKER.md` with `write_bytes(original)` (raw bytes; must not be normalised).
- `create_startup_script` writes `.vscodeclaude_start.bat` with text-mode `Path.write_text`.
- `emit_schema` already compares with universal newlines.
- `init._deploy_skills`, session JSON / logs, writes outside the repo, `tools/tach_docs.py`.
- `docs/architecture/architecture.md` shims table (line 96).
