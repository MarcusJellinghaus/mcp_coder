# Step 1 — Switch formatter to ruff, update CI / import-linter / comments, reformat

See [summary.md](summary.md). One commit.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement Step 1 exactly
> as specified: edit the config, CI, import-linter, gitignore and the four comment/docstring
> locations, then run `run_format_code` with
> `target_directories=["src", "tests", "tools"]` and run all listed checks. Make no hand
> edits to import order and no other code changes. Do not touch docs (that is Step 2).
> Commit everything as one commit.

## TDD

Not applicable — config, CI and comments only; no behaviour changes. The existing suite
plus the checks below verify the step. No new tests.

## WHERE / WHAT

### `pyproject.toml`

- `[project.dependencies]`: delete `"black>=26.5.1",` and `"isort>=9.0.1",`.
- `dev` extra: `"ruff>=0.9.0"` → `"ruff>=0.16.8"`.
- `[tool.mcp-tools-py]`:
  ```toml
  [tool.mcp-tools-py]
  # Formatter for run_format_code and mcp-coder workflows: ruff (import sorting + ruff format)
  formatter = "ruff"
  ```
  (the comment must not name isort or black)
- Delete the `[tool.black]` and `[tool.isort]` tables entirely.
- Add an empty `[tool.ruff.format]` table directly after the `[tool.ruff]` table (before
  `[tool.ruff.lint]`). Nothing goes inside it — all defaults.
- `[tool.ruff.lint] select`: append `"I",` (e.g. after `"UP",`). Do **not** add a
  `[tool.ruff.lint.isort]` section.
- `[tool.ruff.lint] ignore`, `E501` comment: `owned by the formatter (black)` →
  `owned by the formatter (ruff format)`.
- `[tool.deptry.per_rule_ignores] DEP002`: remove `"black", "isort",` from the
  mcp-tools-py group (keep `"mypy", "ruff", "tach", "vulture", "import-linter",`).

### `.github/workflows/ci.yml` (`test` job matrix)

- Delete the `isort` row.
- Replace the `black` row with:
  ```yaml
  - {name: "ruff-format", cmd: "ruff version && ruff format --check src tests tools"}
  ```
  (keep it as the first row; the existing `ruff` row already covers `I`).

### `.importlinter`

Delete both blocks, each including its `# ----` comment header:
`[importlinter:contract:black_isolation]` and `[importlinter:contract:isort_isolation]`.
Leave a single blank-line separation before the `Textual Library Isolation` header.

### `.gitignore`

Delete the line `*.isorted`.

### `src/mcp_coder/cli/main.py`

Module docstring: delete the `isort:skip_file` line and the blank line before it, giving
`"""Main CLI entry point for MCP Coder."""`.

### `src/mcp_coder/__init__.py` (lines 15–22)

Keep `# isort: skip_file`. Replace the comment below it with an explanation in ruff terms.
It must **not** claim ruff would move the guard (the `try/except` already separates the
import blocks, so the directive is only defensive). Suggested:

```python
# isort: skip_file
#
# This module's import order is load-bearing and must NOT be auto-sorted: the
# dependency guard below has to run before the heavy imports. ruff's import
# sorter (`I`) honours `skip_file`, so the order here is frozen and the imports
# below are kept sorted by hand. The try/except already separates the guard
# from the import block; the directive is a defensive guarantee on top.
```

### `src/mcp_coder/utils/__init__.py` (line 11)

`isort is disabled for this file - do not reorder imports.` →
`import sorting is disabled for this file - do not reorder imports.`
Keep `# isort: skip_file` (load-bearing: without it ruff `I` merges the layer-1 and layer-2 blocks).

### `tests/llm/providers/langchain/approval_harness.py` (docstring lines 25–27)

Replace the isort bullet. Suggested:

```
* ruff ``E402`` flags a module-level import placed below a statement, so a
  module-level ``importorskip`` ahead of the langchain imports it guards would
  put those imports in violation;
```

## ALGORITHM

```
apply all edits above (no import-order hand edits)
run_format_code(target_directories=["src","tests","tools"])   # ruff_imports → ruff_format
run checks below; all must pass → format → commit
```

Notes:
- No ruff version check. The reformat uses the ruff bundled with mcp-tools-py; CI's
  `ruff-format` row (latest ruff from `.[dev]`, prints `ruff version`) is the
  version-drift guard. If it fails after the reformat, upgrade ruff in mcp-tools-py and
  re-run `run_format_code`.
- Expected from `ruff_imports`: import-order fixes in `src/mcp_coder/mcp_workspace_github.py`
  and `tests/workflows/vscodeclaude/test_assessment_issue_facts.py`. Expected from
  `ruff_format`: ~109 reformatted files (64 src, 44 tests incl. `tests/README.md`,
  `tools/tach_docs.py`). Both are tool output — accept as is.

## DATA

No new functions, signatures or data structures. `run_format_code` resolves to the steps
`["ruff_imports", "ruff_format"]`.

## Checks (all must pass)

- `run_format_code(target_directories=["src","tests","tools"], check_only=True)` — clean
- `run_ruff_check(target_directories=["src","tests","tools"])` — clean (includes `I`, `E402`)
- `run_lint_imports_check`
- `run_pylint_check`
- `run_mypy_check`
- `run_pytest_check` with the fast unit-test marker filter from CLAUDE.md and `-n auto`

deptry runs in CI on the PR (`DEP002`/`DEP003`).

Manual, after the PR is up (Marcus — not part of the implementation step):
`.venv\Scripts\python -m mcp_coder verify` — the Formatter row shows `ruff_imports → ruff_format`
(other rows may report environment-specific issues; only the Formatter row matters here).
The `run_format_code(check_only=True)` check above already exercises formatter resolution.

## Commit

```
chore(format): switch formatting to ruff, retire isort and black

formatter = "ruff"; I added to ruff lint select; black/isort config,
dependencies, CI rows and import-linter contracts removed; ruff-format
CI row added. Reformat applied with ruff_imports + ruff_format over
src, tests and tools.
```
