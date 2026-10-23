# Summary — #1175 Migrate formatting to ruff: retire isort and black

## Goal

Switch the repo from isort + black to ruff in one PR:

- imports → ruff lint rule `I` (and the `ruff_imports` step of `run_format_code`)
- code → `ruff format` (the `ruff_format` step)

Absorbs #1174. Part of epic #1163.

## Architectural / design changes

| Area | Before | After |
|---|---|---|
| Formatter selection (`[tool.mcp-tools-py] formatter`) | `"black"` → `run_format_code` runs `isort → black` | `"ruff"` → `run_format_code` runs `ruff_imports → ruff_format` |
| Formatter config | `[tool.black]`, `[tool.isort]` (`float_to_top`) | empty `[tool.ruff.format]` (all defaults); line length only in `[tool.ruff] line-length = 88` |
| Import-order lint | isort `--check` CI job | ruff `I` in `[tool.ruff.lint] select`; existing `ruff` CI row covers it |
| Misplaced-import guard | isort `float_to_top` auto-moves imports | ruff `E402` flags them (already enabled, 0 hits); no auto-move — accepted loss |
| CI `test` matrix | `black`, `isort` rows | one `ruff-format` row: `ruff version && ruff format --check src tests tools` |
| Declared deps | `black`, `isort` in `[project.dependencies]` + deptry `DEP002` ignores | removed (they still arrive transitively via mcp-tools-py — expected) |
| `ruff` floor (`dev` extra) | `>=0.9.0` | `>=0.16.8` (mcp-tools-py's floor) |
| import-linter | `black_isolation`, `isort_isolation` contracts | removed; deptry `DEP003` guards direct imports in `src` |

There is no new runtime code. mcp_coder already sends formatting through mcp-tools-py's
`resolve_steps` (#1173), so changing the one config key changes every formatting entry point
(`run_format_code`, commit tooling, implement's `run_formatters`, `mcp-coder verify`).

## Key constraints

- isort and ruff `I` must never run side by side. That is why everything is switched in one PR.
- Import-order fixes come from the tool only: `run_format_code` runs `ruff check --select I --fix`
  as its `ruff_imports` step, replacing the issue's separate `run_ruff_fix(select=["I"])`
  call (same ruff, same command). No hand edits, no `noqa`, no `[tool.ruff.lint.isort]` section.
- `run_format_code` must be called with `target_directories=["src", "tests", "tools"]`.
  The default targets skip `tools/`, so `tools/tach_docs.py` would fail the `ruff-format` CI row.
- `# isort: skip_file` stays in `src/mcp_coder/__init__.py` (defensive) and
  `src/mcp_coder/utils/__init__.py` (load-bearing); ruff `I` honours both.
- TDD does not apply: the change is config, CI, comments and docs only. The formatter
  resolution itself is already tested (mcp-tools-py; `tests/cli/commands/test_verify_project_section.py`).
  The quality checks are the verification.
- Test mocks naming `["isort", "black"]` (`tests/conftest.py`, `tests/workflow_steps/test_commit.py`)
  and `test_verify_project_section.py` don't depend on this repo's config — they stay unchanged.

## Out of scope

- `docs/configuration/config.md:25` — describes general detection; still accurate.
- `project_idea.md`, `docs/architecture/dependencies/pydeps_graph.dot` (stale generated graph),
  `tools/mlflow/analyze_bash_commands.py` (command-name data list).
- Cleanup of the unused `formatter_integration` marker.
- `main` branch protection (required checks: drop `black`/`isort`, add `ruff-format`) —
  a manual GitHub settings change by the maintainer before merge.

## Files modified

Step 1 — switch + reformat:

- `pyproject.toml`
- `.github/workflows/ci.yml`
- `.importlinter`
- `.gitignore`
- `src/mcp_coder/__init__.py` (comment)
- `src/mcp_coder/cli/main.py` (docstring)
- `src/mcp_coder/utils/__init__.py` (docstring)
- `tests/llm/providers/langchain/approval_harness.py` (docstring)
- tool-generated: `src/mcp_coder/mcp_workspace_github.py`,
  `tests/workflows/vscodeclaude/test_assessment_issue_facts.py` (import order), plus the
  `ruff format` reformat of ~109 files under `src/`, `tests/`, `tools/` (incl. `tests/README.md` code block)

Step 2 — docs:

- `docs/repository-setup/python.md`
- `docs/repository-setup/github.md`
- `docs/architecture/architecture.md`
- `docs/architecture/dependencies/readme.md`
- `tests/README.md`

No files are created or deleted (except the `pr_info/` planning files).

## Steps

1. [step_1.md](step_1.md) — Switch formatter to ruff, update CI / import-linter / comments, reformat.
2. [step_2.md](step_2.md) — Update docs to the ruff toolchain.
