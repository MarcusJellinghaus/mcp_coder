# Step 2 — Update docs to the ruff toolchain

See [summary.md](summary.md). One commit. Precondition: Step 1 is committed.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement Step 2 exactly
> as specified: update the five documentation files so they describe the ruff toolchain
> (no `black`/`isort` CI rows or config tables) and match `.github/workflows/ci.yml` as
> changed in Step 1. Docs only — no code or config changes. Run the checks, then commit.

## TDD

Not applicable — documentation only.

## WHERE / WHAT

### `docs/repository-setup/python.md`

- Key Sections table (lines 19–21):
  - Keep the `[tool.mcp-tools-py] formatter` row unchanged (it documents both values generically).
  - Delete the `[tool.black]` and `[tool.isort]` rows.
  - Add in their place:
    `| [tool.ruff.format] | mcp__mcp-tools-py__run_format_code | ruff format config; selects ruff when formatter is unset and [tool.black] is absent |`
    (with backticks like the neighbouring rows).
- `[tool.ruff]` / `[tool.ruff.lint]` row (line 26): "Read by" becomes
  `` `tools/ruff_check.sh` / `.bat`, `mcp__mcp-tools-py__run_format_code` `` (line length + `I` rules are also read by the formatter).
- CI table (lines 182–193): delete the `black` and `isort` rows; add at the top:
  ```
  | `ruff` | Linter (includes import sorting, `I`) |
  | `ruff-format` | Code formatter (`ruff format --check`) |
  ```

### `docs/repository-setup/github.md`

- Line 418 note: `(black, pytest, mypy, etc.)` → `(ruff, pytest, mypy, etc.)`.
- Example matrix (lines 440–441): replace the `black` and `isort` rows with:
  ```yaml
  - {name: "ruff", cmd: "ruff version && ruff check src tests tools"}
  - {name: "ruff-format", cmd: "ruff version && ruff format --check src tests tools"}
  ```

### `docs/architecture/architecture.md` (line 408)

`Each check (black, isort, pylint, tests, mypy)` → `Each check (ruff, ruff-format, pylint, tests, mypy)`.

### `docs/architecture/dependencies/readme.md` (line 77)

`**Third-party (7)**: github, git, jenkins, mcp_tools_py, requests, black, isort` →
`**Third-party (5)**: github, git, jenkins, mcp_tools_py, requests`.
Hand-written list, not generated.

### `tests/README.md` (lines 16, 54) — minimal wording only

- Line 16: `# Code formatter tests (black, isort)` → `# Code formatter tests (ruff)`.
- Line 54: requirements column `black, isort` → `ruff`.

## ALGORITHM

None — text edits.

## DATA

None.

## Checks (all must pass)

- Search the repo for `isort|black` (`search_files`): remaining hits only in the places the
  summary lists as out of scope or as intentionally kept (`# isort: skip_file` directives,
  test mocks, `test_verify_project_section.py`, `docs/configuration/config.md`, `python.md`'s
  generic `formatter` row and line 33, `project_idea.md`, `pydeps_graph.dot`,
  `tools/mlflow/analyze_bash_commands.py`).
- `run_format_code(target_directories=["src","tests","tools"], check_only=True)` — clean
  (`tests/README.md` contains a Python code block that ruff formats).
- `run_pylint_check`, `run_mypy_check`, `run_pytest_check` (fast unit-test filter, `-n auto`)
  — unchanged code, should still pass.

## Commit

```
docs: describe ruff formatting toolchain instead of isort/black
```
