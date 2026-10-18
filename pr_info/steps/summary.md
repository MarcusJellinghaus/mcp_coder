# Summary: LF-only writes for committed files

## Problem

Several call sites write files that can end up in a commit via text-mode
`open()` / `Path.write_text()`. On Windows, text mode translates `\n` →
`\r\n`. Combined with mcp-workspace's `stage_specific_files` (uses GitPython
`index.add`, which skips git's clean filter), the CRLF lands directly in the
commit blob — breaking the scoped round-log commit used by every review round
and causing history to alternate CRLF/LF, which makes `/rebase` abort with
"local changes would be overwritten".

Only the round log is an observed failure; the other sites are the same risk
class (defence in depth). The call-site list comes from a repo-wide search of
`src/` and `tools/` (issue #1242, "Fix" section).

## Design

One new pure helper, `mcp_coder.utils.text_io.write_lf_text(path, text, *,
append=False)`:

1. Normalizes any embedded `\r\n` in `text` to `\n` (the round-log text comes
   from LLM output, so `newline="\n"` alone would not guarantee no `\r` —
   an already-CRLF chunk would pass through unchanged).
2. Writes via `Path.open(mode, encoding="utf-8", newline="\n")`, which
   disables Python's universal-newline translation on write. This mirrors
   the existing `.gitignore`-writer precedent in
   `workflows/vscodeclaude/workspace.py:435-437` (`newline=""`); `"\n"` is
   used here because it states the intent explicitly.

No equivalent exists in the shared `mcp-coder-utils` package (checked), so a
local module is justified. The helper uses `Path.open` (not a module-level
`open()`) because on Python 3.11 `Path.open` passes `newline` through to
`io.open`, while a spy on `builtins.open` would not observe it.

Six `src/` callers switch to the helper — no change to their return values or
control flow, only how the final write happens:

| Caller | File | What it writes |
|---|---|---|
| `write_round_log` | `workflows/review/review_log.py` | per-round review log append (the observed failure) |
| `create_pr_info_structure` | `workflows/create_plan/prerequisites.py` | `pr_info/TASK_TRACKER.md` template |
| `write_github_actions` | `cli/commands/define_labels_actions.py` | `.github/workflows/label-new-issues.yml`, `approve-command.yml` |
| `emit_schema` | `icoder/permissions/loader.py` | `.icoder/settings.schema.json` |
| `create_vscode_task` | `workflows/vscodeclaude/workspace.py` | `.vscode/tasks.json` in the cloned target repo |
| `_run_mcp_edit_smoke_test` | `cli/commands/verify.py` | transient `.mcp_coder_verify.md` probe |

One non-`src` caller gets an **inline** fix instead: `tools/tach_docs.py`
(`docs/architecture/*.html`, committed) uses a small local `_write_lf`
(`write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")`).
`tools/` is a stand-alone dev script and must not depend on `src/`.
`Path.write_text(newline=...)` needs Python 3.10+ (`requires-python =
">=3.11"`); `newline="\n"` alone does not strip an embedded `\r\n`, hence the
explicit `replace`.

### Architectural impact

None expected. `workflows`, `cli.commands`, and `icoder` already depend on
`mcp_coder.utils` in both `tach.toml` (layer ordering: presentation/application
sit above infrastructure) and `.importlinter`'s `layered_architecture`
contract. Adding one more leaf import from an already-permitted package
requires no config changes — each step re-runs `tach check` and
`lint-imports` to confirm (including `workflows.vscodeclaude`, Step 6).

### Test strategy

The `\r\n`-normalization behavior is proven **once**, centrally, in the
helper's own unit tests — including a spy test on `pathlib.Path.open` that
asserts `newline="\n"` is passed (the one test that fails on every OS, not
just Windows) and tests asserting that LF-only input is written
byte-identical in both write and append modes. Each `src/` call site with a
committed output then only needs one trivial `read_bytes()` regression
assertion (`b"\r" not in content`) added to its *existing* test file — a
Windows-only guard against a caller silently reverting to a text-mode write,
not a re-proof of normalization. The `tasks.json` and `tach_docs` tests
inject `\r\n` through their template / generator output so they do not pass
trivially on Linux. The `verify.py` probe has no new test (fixed literal
content, removed after use); its existing tests stay green. `tach_docs` has
no existing tests, so Step 8 adds `tests/tools/test_tach_docs.py`.

### Out of scope (per issue)

- `.vscodeclaude_start.bat` / `.vscodeclaude_start.sh` and other gitignored
  `.vscodeclaude_*` files. **The `.bat` launcher must keep its line endings**:
  `.gitattributes` sets `*.bat text eol=crlf`.
- Writes outside any repo: `.code-workspace` (`workspace.py:482`),
  vscodeclaude audit/sessions files, `user_config.py:348`, the temp settings
  file in `rebase.py:53`.
- Logs and session data: `event_log`, `crash_logging`, streaming logs,
  `copilot_cli.py:356`, `mlflow_logger.py:343`, `session_storage`,
  `serialization`.
- `cli/commands/init.py:98` (`shutil.copy2` is a byte copy).
- Other `tools/` writers (`ci_coverage_summary`, `safe_delete_folder`,
  `tools/mlflow/*`, `tools/test_profiler_plugin/*`).
- `icoder/permissions/persist.py:411` (`newline=""`, user `.icoder` settings,
  not committed).
- `workflows/vscodeclaude/helpers.py:158,177` (`.to_be_deleted`, workspace
  base, not a committed repo file).
- Task-tracker updates made by external tools.
- The mcp-workspace staging-layer root cause — tracked separately as
  mcp-workspace#326. It covers repos that normalize line endings; this change
  fixes the source independent of git config. Neither makes the other
  redundant.
- `tach.toml` / `.importlinter` config edits — not expected (verify, do not
  change unless a check fails); the optional `icoder` `depends_on` hygiene
  line from the issue is skipped since `tach check` already passes without it.

## Files created

- `src/mcp_coder/utils/text_io.py`
- `tests/utils/test_text_io.py`
- `tests/tools/test_tach_docs.py`

## Files modified

- `src/mcp_coder/workflows/review/review_log.py`
- `tests/workflows/review/test_review_log.py`
- `src/mcp_coder/workflows/create_plan/prerequisites.py`
- `tests/workflows/create_plan/test_prerequisites.py`
- `src/mcp_coder/cli/commands/define_labels_actions.py`
- `tests/cli/commands/test_define_labels_actions.py`
- `src/mcp_coder/icoder/permissions/loader.py`
- `tests/icoder/test_permissions_loader_schema.py`
- `src/mcp_coder/workflows/vscodeclaude/workspace.py`
- `tests/workflows/vscodeclaude/test_workspace.py`
- `src/mcp_coder/cli/commands/verify.py`
- `tools/tach_docs.py`

## Steps

1. **Step 1** — add `write_lf_text` helper + its unit tests (TDD, no callers
   yet).
2. **Step 2** — switch `review_log.py`'s round-log append.
3. **Step 3** — switch `prerequisites.py`'s `TASK_TRACKER.md` write.
4. **Step 4** — switch `define_labels_actions.py`'s two workflow-file writes.
5. **Step 5** — switch `icoder/permissions/loader.py`'s `emit_schema` write.
6. **Step 6** — switch `workspace.py`'s `create_vscode_task` (`tasks.json`)
   write.
7. **Step 7** — switch `verify.py`'s `.mcp_coder_verify.md` probe write.
8. **Step 8** — inline `newline="\n"` fix in `tools/tach_docs.py` + new
   `tests/tools/test_tach_docs.py`.

Steps 2-8 are independent of each other; Steps 2-7 depend on Step 1, Step 8
does not. Each step is one commit: tests + implementation + all checks
passing.
