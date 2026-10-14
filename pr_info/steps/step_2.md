# Step 2 — Enable `SIM` in ruff config with tests carve-out for `SIM117`

Reference: `pr_info/steps/summary.md` (issue #1168). Requires Step 1
already committed.

## Precondition check

Run `ruff check --select SIM` over `src/` and `tests/`. Expect 0 findings
outside: the two `# noqa`'d lines added in Step 1
(`tests/conftest.py` and
`tests/llm/providers/langchain/test_langchain_integration.py`), and
`SIM117` (not yet ignored, still present only in `tests/`). If `src/` shows
any `SIM117` hits, or any other unexpected finding remains, **write one
line to `pr_info/.blocked.txt` describing what's left and stop.**

## WHERE

`pyproject.toml`, `[tool.ruff.lint]` and
`[tool.ruff.lint.per-file-ignores]` sections only.

## WHAT

No functions. Two config edits:

1. Add `"SIM"` to the `select` list.
2. Add `"SIM117"` to the existing `"tests/**/*.py"` per-file-ignore entry.

## HOW

Current state (re-read the live file before editing — it may have shifted):

```toml
select = [
    "D",
    "DOC201", "DOC202", "DOC402", "DOC403", "DOC501", "DOC502",
]
...
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["D", "DOC"]
```

Target state:

```toml
select = [
    "D",
    "DOC201", "DOC202", "DOC402", "DOC403", "DOC501", "DOC502",
    "SIM",
]
...
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["D", "DOC", "SIM117"]
```

Use `mcp__mcp-workspace__edit_file` for both edits.

## ALGORITHM

```
edit select list: append "SIM"
edit tests/**/*.py per-file-ignore: append "SIM117"
run ruff check (full project default select) -> expect 0 findings
run ruff check --select SIM117 on src/ only -> expect 0 (acceptance criterion: SIM117 in src/ stays 0)
```

## DATA

No runtime data structures. `ruff check` output goes from "SIM findings
not selected" to "0 findings, rule enabled."

## Verification before commit

- `mcp__mcp-tools-py__run_ruff_check` (project default select) — must be
  clean.
- `mcp__mcp-tools-py__run_ruff_check(select=["SIM117"], target_directories=["src"])`
  — must report 0.
- `mcp__mcp-tools-py__run_pytest_check(...)` (same filter as Step 1),
  `run_pylint_check`, `run_mypy_check` — must pass (config-only change, no
  behavior impact expected).
- `mcp__mcp-tools-py__run_format_code`.

## Commit

```
config(ruff): enable SIM with tests carve-out for SIM117

SIM117 (stacked `with mock.patch` blocks) stays allowed in tests/
only; collapsing it hurts readability and blocks per-mock comments.
src/ has zero SIM117 hits and must stay that way.
```

## LLM prompt for this step

"Implement Step 2 from `pr_info/steps/step_2.md`, following
`pr_info/steps/summary.md` for issue #1168. Requires Step 1 already
committed. Only touch `pyproject.toml`. Make exactly one commit with all
checks (ruff, pytest, pylint, mypy, format) passing."
