# Step 10: Documentation

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_10.md`) only. Steps 1–9 must be done: if `mcp_coder.install.project_setup` does not exist, write one line to `pr_info/.blocked.txt` and stop.
Docs only. Run pytest (unit filter, `-n auto`, includes `tests/docs`) and `check_file_size`; both must pass. One commit.

## WHERE

- Create `docs/configuration/setup.md`
- Modify `docs/configuration/config.md` — "Test Command Script" and "Dependency Architecture" sections; link to `setup.md`
- Modify `docs/repository-setup/README.md` — `uv.lock` must be tracked or ignored (today it says not required); link `setup.md`
- Modify `README.md`, `docs/architecture/architecture.md`, `docs/migration/multi-language.md` — remove "project setup is Python-only / uses `uv sync --extra dev`"; describe `mcp-coder setup`; architecture names `install/project_setup.py`, `utils/setup_config.py`, `utils/executable.py`
- Check `docs/environments/environments.md` and `docs/coordinator-vscodeclaude.md` (updated in step 7) for remaining stale statements
- Modify `docs/README.md` if it indexes configuration pages
- Modify `docs/cli-reference.md` — the `### setup` section links `docs/configuration/setup.md`

## WHAT (`docs/configuration/setup.md`)

1. Purpose and the one command: `mcp-coder setup --project-dir <dir> [--refresh] [--skip-overrides]`; callers (session launcher, Linux templates, AutoRunner).
2. Location: `pyproject.toml`, else root `mcp-coder.toml`; both → error; per-table rule (toolkit and setup may live in different files).
3. Schema: `steps` (required, ordered; `[]` = nothing to do); step keys `argv` | `builtin`, `name`, `timeout` (argv only, positive int, default 1800); unknown keys are errors.
4. Default: no table + `pyproject.toml` → `[{ builtin = "python" }]`; no table, no `pyproject.toml` → nothing to do.
5. Built-in `python`: today's `install --source local --use-sync`, `install-from-github` overrides, `post_install_checks`, `[tool.mcp-coder.install]`; later steps see the project venv on `PATH` and in `VIRTUAL_ENV`.
6. `argv[0]` resolution: link to the rules in `toolkits.md` (do not repeat them); one example line is enough (`./mvnw` → `mvnw.cmd`, `npm` → `npm.cmd` on Windows; no `PATHEXT` match = not found).
7. Changed-files rule: setup fails on changed tracked files or new untracked, non-ignored files; Python repos must track or ignore `uv.lock`.
8. `UV_GIT_SHALLOW=0` is set by `setup` itself.
9. Recommend lockfile-frozen commands: `npm ci`, `cargo … --locked`, `--frozen-lockfile`.
10. Non-Python repos: `.mcp*.json` must not reference `${VIRTUAL_ENV}` (unset there).
11. Subdirectories: tool flags (`--prefix`, `-f`, `--manifest-path`), no `cwd` key.
12. `mcp-coder verify` `Setup` row.
13. Examples: TypeScript (npm, `mcp-coder.toml`), Java (Maven wrapper and Gradle wrapper), Rust (`cargo fetch --locked`), Python plus frontend (`pyproject.toml`) — use the issue's examples.

## HOW

Keep each page under the file-size limit; link rather than repeat (resolution rules live in `toolkits.md`, linked from `setup.md`).

## DATA

None.
