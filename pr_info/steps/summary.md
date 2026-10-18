# Summary: LF-only writes for committed workflow files

## Problem

Four call sites write committed repo files via text-mode `open()`/`Path.write_text()`.
On Windows, text mode translates `\n` → `\r\n`. Combined with mcp-workspace's
`stage_specific_files` (uses GitPython `index.add`, which skips git's clean
filter), the CRLF lands directly in the commit blob — breaking the scoped
round-log commit used by every review round and causing history to alternate
CRLF/LF, which makes `/rebase` abort with "local changes would be overwritten".

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

Four callers switch to the helper — no change to their return values or
control flow, only how the final write happens:

| Caller | File | What it writes |
|---|---|---|
| `write_round_log` | `workflows/review/review_log.py` | per-round review log append |
| `create_pr_info_structure` | `workflows/create_plan/prerequisites.py` | `pr_info/TASK_TRACKER.md` template |
| `write_github_actions` | `cli/commands/define_labels_actions.py` | `.github/workflows/label-new-issues.yml`, `approve-command.yml` |
| `emit_schema` | `icoder/permissions/loader.py` | `.icoder/settings.schema.json` |

### Architectural impact

None. `workflows`, `cli.commands`, and `icoder` already depend on
`mcp_coder.utils` in both `tach.toml` (layer ordering: presentation/application
sit above infrastructure) and `.importlinter`'s `layered_architecture`
contract. Adding one more leaf import from an already-permitted package
requires no config changes — each step re-runs `tach check` and
`lint-imports` to confirm.

### Test strategy

The `\r\n`-normalization behavior is proven **once**, centrally, in the
helper's own unit tests — including a spy test on `pathlib.Path.open` that
asserts `newline="\n"` is passed (the one test that fails on every OS, not
just Windows). Each of the four call sites then only needs one trivial
`read_bytes()` regression assertion (`b"\r" not in content`) added to its
*existing* test file — a Windows-only guard against a caller silently
reverting to a text-mode write, not a re-proof of normalization.

### Out of scope (per issue)

- `icoder/permissions/persist.py:411` (`newline=""`, user `.icoder` settings,
  not committed).
- `workflows/vscodeclaude/helpers.py:158,177` (`.to_be_deleted`, workspace
  base, not a committed repo file).
- `tools/tach_docs.py:370,392` (dev-tool generator, outside `src`).
- Generated `.vscodeclaude_*` files (gitignored).
- Task-tracker updates made by external tools.
- The mcp-workspace staging-layer root cause — tracked separately as
  mcp-workspace#326.
- `tach.toml` / `.importlinter` config edits — not required (verified, not
  changed); the optional `icoder` `depends_on` hygiene line from the issue is
  skipped since `tach check` already passes without it.

## Files created

- `src/mcp_coder/utils/text_io.py`
- `tests/utils/test_text_io.py`

## Files modified

- `src/mcp_coder/workflows/review/review_log.py`
- `tests/workflows/review/test_review_log.py`
- `src/mcp_coder/workflows/create_plan/prerequisites.py`
- `tests/workflows/create_plan/test_prerequisites.py`
- `src/mcp_coder/cli/commands/define_labels_actions.py`
- `tests/cli/commands/test_define_labels_actions.py`
- `src/mcp_coder/icoder/permissions/loader.py`
- `tests/icoder/test_permissions_loader_schema.py`

## Steps

1. **Step 1** — add `write_lf_text` helper + its unit tests (TDD, no callers
   yet).
2. **Step 2** — switch `review_log.py`'s round-log append.
3. **Step 3** — switch `prerequisites.py`'s `TASK_TRACKER.md` write.
4. **Step 4** — switch `define_labels_actions.py`'s two workflow-file writes.
5. **Step 5** — switch `icoder/permissions/loader.py`'s `emit_schema` write.

Steps 2-5 are independent of each other and depend only on Step 1. Each step
is one commit: tests + implementation + all checks passing.
