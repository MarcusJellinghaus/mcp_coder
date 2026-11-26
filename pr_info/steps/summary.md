# Summary: `mcp-coder init` gitignores `.mcp-coder/` and `logs/` (#1485)

## Problem

mcp-coder writes LLM session logs under `.mcp-coder/` and Claude session logs
under `logs/claude-sessions/` in the target repo, but `mcp-coder init` never
gitignores either folder. Every whole-tree commit in the workflows then sweeps
the session files in (prompts, absolute local paths), and task tracker
preparation sees changes the LLM did not make.

## Fix

Fix the cause in `init` only: add the two lines to the project `.gitignore`,
idempotently. Once the folders are ignored, git never offers the session files
to any commit, so no workflow, commit or task-tracker code changes.

## Architectural / design changes

- **One new, separate `.gitignore` writer in `cli/commands/init.py`**,
  next to `_write_gitignore_entries`. It does not touch `update_gitignore` /
  `GITIGNORE_ENTRY` (`workflows/vscodeclaude/`), because the VSCodeClaude
  session launch re-appends that block in every session folder. Same pattern as
  `ensure_scratch_gitignored` (`init_file_access.py`) for `.scratch/`.
- **Pure check, thin writer.** `_missing_session_log_lines(text)` holds all
  "already present" logic (no I/O); `_write_session_log_entries(project_dir)`
  reads, appends, logs and catches errors.
- **Accepted spellings are generated**, not listed: `_spellings(name)` yields
  `{"", "/"} x {"", "/", "/*", "/**"}` around the name (8 exact lines per
  name). A narrower line such as `logs/claude-sessions/` does not count.
- **Text check, not `git check-ignore`** — same approach as the other init
  writers. Read with `utf-8-sig`, append with `write_lf_text` (LF). An
  undecodable `.gitignore` is read before any write, so it stays byte-identical.
- **Block format:** blank line, `# mcp-coder session logs`, then only the
  missing lines among `/.mcp-coder/*` and `/logs/`.
- **Runs in both modes** (`--just-skills` and full init), independent of the
  `.mcp-file-access` skip reasons.
- **Reporting:** own line `Gitignore: <added lines> added` or
  `Gitignore: /.mcp-coder/*, /logs/ present`. The existing
  `Gitignore: N entries added` line is unchanged.
- **Exit code / hint:** a read/write failure makes `files_ok` false (exit 1);
  the "Commit .gitignore and .mcp-file-access…" hint also fires when only this
  block was added.
- No migration for repos initialised earlier; no workflow changes.

## Files

Modified:

- `src/mcp_coder/cli/commands/init.py` — constants, `_spellings`,
  `_missing_session_log_lines`, `_write_session_log_entries`, wiring in
  `execute_init`.
- `tests/cli/commands/test_init_gitignore.py` — new tests, extra assertions in
  existing tests.
- `docs/repository-setup/repo.md` — recommended lines, bullet rewritten.
- `docs/cli-reference.md` — `init` section and report line.
- `docs/repository-setup/README.md` — checklist item listing what `init` writes.

Created: none (besides these plan files).

## Steps

1. [step_1.md](step_1.md) — writer + tests (TDD), wired into `execute_init`.
2. [step_2.md](step_2.md) — documentation.
