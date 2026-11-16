# feat(init): create .mcp-file-access; gitignore .scratch/

`mcp-coder init` creates (or completes) the `.mcp-file-access` rules file and gitignores `.scratch/` in every repo it runs in; `verify` respects the rules file, so its MCP edit smoke test keeps running with `.scratch/` gitignored.

**Human prerequisite first (task 0), then implementable by `mcp-coder implement`** — Python writes `.mcp-file-access` (MCP can't, by design); tests create it under `tmp_path`. Manual: task 0 and the live checks marked below.

## Dependencies / references

- **Hard prerequisite:** every env that runs the MCP server for these repos has mcp-workspace with `.mcp-file-access` support (since f626cf8 — unreleased, newer than tag 0.1.13, so no version floor can be pinned): the tool env, every Jenkins executor env, sibling-repo envs. A too-old server silently hides a gitignored `.scratch/` (no error) — breaking scratch probes, `issue_update`'s `.scratch/` body files, Jenkins log reads and the verify smoke test
- Soft: after issue 1 (this repo's `.mcp-file-access` already holds all five template rules)
- **Read first:** `docs/repository-setup/claude-permissions/implementation.md` §3.2 FU10, FU11; `tool-inventory.md` (`.mcp-file-access` facts)
- mcp-workspace (reference project): `docs/file-access.md`, `access_rules.py`; `directory_utils` re-exports (lazily) `FileAccess` (`IntEnum`: `HIDDEN`, `READ_ONLY`, `READ_WRITE`), `get_file_access(path: str, project_dir: Path) -> FileAccess`, `validate_access_rules(project_dir: Path) -> list[str]`. The loader reads `utf-8-sig` and folds case on win32
- Precedent: mcp-workspace already gitignores `.scratch/` with `read-write /.scratch/`
- Rollout to sibling repos: FU7 (each repo's next `init` changes `.gitignore` and `.mcp-file-access`; commit them; mcp-workspace gets three new rules)

## Decisions

- **Template = a constant in code** (like `templates.GITIGNORE_ENTRY`) — the root `.mcp-file-access` is not packaged (`setup.py` copies only `.claude/{skills,knowledge_base,agents}`). Rules: `read-only /.vscodeclaude_status.txt`, `read-only /.mcp.json`, `read-only /.claude/settings.json`, `read-only /.claude/settings.local.json`, `read-write /.scratch/`. Not `.mcp.linux.json` / `.mcp.macos.json`: target repos gitignore them (`repo.md`), where a `read-only` rule would *expose* them (this repo keeps them via issue 1)
- **Support flag:** the shim (`src/mcp_coder/mcp_workspace.py`) exports `FILE_ACCESS_SUPPORTED` plus `get_file_access`, `FileAccess`, `validate_access_rules` — imported from mcp-workspace when available, else mypy-safe stand-ins (no ImportError). The flag is the test seam. It describes the env `init` runs in, not the server — the hard prerequisite covers the server
- **Existing file:** first `validate_access_rules`; problems → leave the file byte-identical, warn, exit 0, and skip the `.scratch/` line. Otherwise append each template rule whose pattern doesn't occur yet (normalised: whitespace-insensitive, case-folded on win32). Appended rules come last and therefore win over earlier overlapping user rules (last match wins) — before appending, warn for each template path that an existing rule already matches with a different level (`get_file_access` before vs after)
- **Without support** (`FILE_ACCESS_SUPPORTED` false): still create / append the rules file (no validation possible → append only, warn), never write the `.scratch/` line
- **New file:** header comment, LF line endings (`utils.text_io.write_lf_text`, append mode for appends); existing CRLF files get LF appends, like `update_gitignore`; handle a missing trailing newline and a BOM
- **`.scratch/` gitignored in every repo by `init`** — through its own init-only writer, **not** `GITIGNORE_ENTRY` (shared with the vscodeclaude session launch, which must not gitignore `.scratch/`). Written only when: support flag true, rules file valid, and `get_file_access(".scratch/x")` is `READ_WRITE` after the rules step ("already present" counts). Tolerates an undecodable `.gitignore` (left byte-identical), like the existing gitignore step
- Runs in both `init` modes (incl. `--just-skills`); exit 1 if the rules file can't be written (like a gitignore failure; the run still finishes); report lines: `Gitignore: N entries added` (unchanged, `GITIGNORE_ENTRY` only), new `Gitignore: .scratch/ added|present|skipped (<reason>)` and `File access rules: created|N rules added|unchanged|invalid (<problem>)`; output tells the user to commit `.gitignore` and `.mcp-file-access`
- **vscodeclaude session folders: no change** — reversal of FU10's "same for session folders": they get the committed file via git; writing an untracked one would break checkouts of branches that track it
- After this issue, the `read-only /.claude/settings.local.json` rule exposes that file to MCP reads wherever it is gitignored — harmless

## Tasks

### 0. Prerequisite (by hand, before the implement run)
- [ ] Upgrade mcp-workspace (≥ f626cf8) in the tool env and every Jenkins executor env; check per env: with `.scratch/` listed in `.git/info/exclude` (not committed), MCP `list_directory` shows `(read-write, not committed)` for a `.scratch/` file; then remove the exclude line

### A — init (FU10)
- [x] Shim: `FILE_ACCESS_SUPPORTED`, `get_file_access`, `FileAccess`, `validate_access_rules` with fallback stand-ins
- [x] Template constant with the rules above
- [x] `cli/commands/init.py`: ensure `.mcp-file-access` per the Decisions (create / validate / append / warn), both modes
- [x] Init-only `.scratch/` gitignore writer, conditions as above
- [x] Tests:
  - [x] new file (also under `--just-skills`); existing file with/without the rules; second run = no change
  - [x] overlapping user rule → warning; same-pattern user rule kept
  - [x] invalid file byte-identical, exit 0, `.scratch/` line skipped
  - [x] rules file not writable → exit 1, run finishes
  - [x] `FILE_ACCESS_SUPPORTED` false → rules file appended, no `.scratch/` line
  - [x] `validate_access_rules(project) == []` after init; real `get_file_access` with `.scratch/` absent returns `READ_WRITE`
  - [x] drift test — every template rule is in this repo's `.mcp-file-access` (`REPO_ROOT` pattern)
  - [x] existing `test_init_gitignore.py` tests stay green: entry count unchanged (patch the flag where needed), `test_non_utf8_gitignore_does_not_abort_init` also covers the new writer, `test_gitignore_write_failure_exits_1_but_finishes_run`

### B — this repo + verify (FU11)
- [x] `cli/commands/verify.py::_run_mcp_edit_smoke_test`: `validate_access_rules` problems → skip "invalid rules file"; else run only when `get_file_access(_SMOKE_TEST_FILE)` is `READ_WRITE`; `HIDDEN` → skip "not exposed", `READ_ONLY` → skip "read-only rule"; without support → today's `is_path_gitignored` check
- [x] Update `tests/cli/commands/test_verify_mcp_edit_smoke.py` (patches of `is_path_gitignored`, the skip-text test)
- [x] This repo's `.gitignore`: `.scratch/` (via the new `init` step)
- [x] CLAUDE.md: `git_commit` note (keep the `all=True` ban; restate the reason — other untracked files), "Scratch probes" (no longer "not gitignored"), Jenkins log-download bullet ("`.scratch/` works" — via the rule)
- [x] Keep CI `check_forbidden_folder .scratch` as a backstop

### Docs
- [x] `docs/cli-reference.md` (init), `docs/repository-setup/repo.md` (`.gitignore` list; commit `.mcp-file-access`), `docs/repository-setup/README.md` (checklist, file table), `docs/repository-setup/claude-code.md`, `tools/jenkins_status_check.md` (`.scratch/` log wording)
- [x] `tool-inventory.md`: mcp-workspace version table (stale); `implementation.md`: FU10 (all template rules; session-folder part reversed), FU11 done
- [x] Issue 1 draft: "its `init` template is this repo's `.mcp-file-access`" → "issue 4's template is a subset (no `.mcp.linux/macos.json`)"

## Acceptance

- [x] Unit: the tests above; `verify` smoke test runs (`prompt_llm` called) when `.scratch/` is gitignored and the rule is present
- [x] Unit: the vscodeclaude session launch does not gitignore `.scratch/`
- [ ] Manual, interactive, after task 0 and the merge: in this repo, MCP `save_file` and `read_file` under `.scratch/`, `github_issue_view(body_file=".scratch/body.md")` (the write path `issue_update` uses), and `delete_directory(".scratch", recursive=True)` all work; `git status` doesn't show `.scratch/`
- [x] pylint, pytest, mypy pass
