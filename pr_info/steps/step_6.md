# Step 6 — Enable ruff `E`, exclude `E501`, in `pyproject.toml`

See `pr_info/steps/summary.md` for the overall goal and rationale. This step
depends on steps 1–5 already being merged (all 70 non-`E501` findings must
be resolved before this config change is made).

## Precondition check

Run `mcp__mcp-tools-py__run_ruff_check` with `select=["E741", "E402", "E721"]`
and `extra_args=["--preview"]`. Confirm it reports 0 findings (steps 1–5
done). If it reports any findings, write one line to `pr_info/.blocked.txt`
and stop.

## WHERE

`pyproject.toml`, `[tool.ruff.lint]`:

```toml
[tool.ruff.lint]
preview = true
explicit-preview-rules = true
select = [
    "D",
    "DOC201", "DOC202", "DOC402", "DOC403", "DOC501", "DOC502",
]
ignore = [
    "D104",
    "D107",
]
```

## WHAT

No function signatures change — this is a config-only step. Add `"E"` to
`select`. Add `"E501"` to `ignore` with a comment stating line length is
owned by black/ruff-format, not this linter, and that the exclusion is
permanent (not tied to the current formatter).

## HOW

Edit the two lists in place:

```toml
select = [
    "D",
    "DOC201", "DOC202", "DOC402", "DOC403", "DOC501", "DOC502",
    "E",
]
ignore = [
    "D104",  # missing docstring in __init__.py (low value)
    "D107",  # missing docstring in __init__ method (redundant with class docstring)
    "E501",  # line length is owned by the formatter (black); not re-checked here
]
```

## ALGORITHM

N/A — declarative config change, no logic.

## DATA

No change to return values or data structures.

## Test-first note

The "test" for a lint-config change is the lint run itself, not a unit
test: after this edit, `ruff check` with the project's full config must
report zero findings (steps 1–5 already removed every non-`E501` `E`
finding). No new pytest test is added for this step.

## Steps

1. Add `"E"` to `select` and `"E501"` (with comment) to `ignore` as shown
   above.
2. Run `mcp__mcp-tools-py__run_ruff_check` with no overrides (full project
   config) — must report 0 findings.
3. Run `mcp__mcp-tools-py__run_pytest_check` with
   `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`.
4. Run `mcp__mcp-tools-py__run_pylint_check` and `mcp__mcp-tools-py__run_mypy_check`.
5. Run `mcp__mcp-tools-py__run_format_code`.
6. Commit: `feat(lint): enable ruff E, exclude E501 (owned by formatter)`.

## LLM prompt for this step

> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_6.md`: in `pyproject.toml`, add `"E"` to
> `[tool.ruff.lint] select` and add `"E501"` to `ignore` with the
> explanatory comment. Follow the precondition check first — if it fails,
> write one line to `pr_info/.blocked.txt` and stop. Otherwise make the
> edit, confirm a full `ruff check` is clean, run the other checks listed in
> the step, format the code, and produce exactly one commit with the given
> message.
