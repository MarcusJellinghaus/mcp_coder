# Step 7 — Enable ruff `ANN` (excluding `ANN401`)

Read `pr_info/steps/summary.md` first for overall context.

Part of issue #1171. This is the config flip, done last so every
intermediate step stayed green: steps 1-6 already fixed all 64 non-`ANN401`
findings while `ANN` wasn't selected, so enabling it now should produce zero
new issues.

## Precondition check

Run `mcp__mcp-tools-py__run_ruff_check` with
`select=["ANN001","ANN002","ANN003","ANN201","ANN202","ANN204"]`,
`max_issues=0`. If this reports anything other than 0 issues, steps 1-6
weren't fully applied — write one line to `pr_info/.blocked.txt` and stop.

## WHERE

`pyproject.toml`, `[tool.ruff.lint]` section.

## WHAT

In `select`, add `"ANN"` (after the existing `"D"` entry, before the `DOC*`
block — ordering doesn't matter functionally, keep it readable). In
`ignore`, add:

```toml
"ANN401",  # Any is correct at library/CLI boundaries; mypy strict covers the rest
```

## HOW

Direct edit to the existing `select = [...]` and `ignore = [...]` lists; no
other `[tool.ruff.lint]` keys change. `tests/**/*.py` per-file-ignores
(currently `["D", "DOC"]`) stays as-is — `ANN` must reach `tests/` too.

## ALGORITHM

N/A — config change.

## DATA

N/A.

## TDD

Not applicable: this step's own test *is* the ruff run below.

## Verification

- `mcp__mcp-tools-py__run_ruff_check` with `select=["ANN"]`, `max_issues=0` —
  must report 0 issues (421 `ANN401` are now ignored by config, not by
  selection — confirm separately with
  `select=["ANN401"]` that ruff reports them as ignored/not selected rather
  than erroring).
- `mcp__mcp-tools-py__run_mypy_check` (confirm `warn_unused_ignores` raises
  nothing new — all stale ignores were removed in steps 2-6).
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_pytest_check` with
  `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
- `mcp__mcp-tools-py__run_format_code`, then commit.

## Commit

One commit: `feat(ruff): enable ANN rule group, exclude ANN401 (#1171)`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_7.md`. Implement
> step 7 exactly as specified: add `"ANN"` to `select` and `"ANN401"` (with
> its comment) to `ignore` in `pyproject.toml`'s `[tool.ruff.lint]`. Run the
> verification commands listed in the step. If `ruff check --select ANN`
> reports anything, that means an earlier step (1-6) was incomplete — do not
> silence it with a new ignore; fix the underlying site instead. Once clean,
> run `run_format_code` and commit with the given message. If the
> precondition check fails, write one line to `pr_info/.blocked.txt` and
> stop.
