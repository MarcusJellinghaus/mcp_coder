# Step 10 — Enable `C4` and `B` in `pyproject.toml`; full verification

Context: see `pr_info/steps/summary.md`. This is the final step: by now
steps 1–9 have fixed all 22 findings, so enabling the rule groups should
flip ruff from "unchecked" to "fully green" in this one commit.

## WHERE

- `pyproject.toml` — `[tool.ruff.lint]` → `select`

## WHAT

```toml
select = [
    "D",
    "DOC201", "DOC202", "DOC402", "DOC403", "DOC501", "DOC502",
    "C4", "B",
]
```

No `ignore` entries are needed for `C4`/`B` — there are no remaining
findings to suppress once steps 1–9 have landed.

## HOW

Add `"C4", "B"` to the existing `select` list in `[tool.ruff.lint]`. Leave
`preview`, `explicit-preview-rules`, `ignore`, and `per-file-ignores`
untouched — `C4`/`B` are stable (non-preview) rules and need none of that
machinery.

## ALGORITHM

```
open pyproject.toml
append "C4", "B" to [tool.ruff.lint] select
```

## DATA

N/A — configuration-only change.

## Precondition

Run `mcp__mcp-tools-py__run_ruff_check(select=["C4", "B"])` **before**
editing `pyproject.toml`, to confirm 0 findings remain (i.e. steps 1–9 are
all in). If it reports any findings, write one line to `pr_info/.blocked.txt`
and stop — do not enable the rules with known findings outstanding.

## Verification

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_ruff_check()                   # now includes C4 + B — expect 0 findings
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_lint_imports_check
```

## Commit

```
feat(ruff): enable C4 and B rule groups

Closes #1165.
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_10.md`. Implement
> step 10 exactly as specified: first confirm zero `C4`/`B` findings remain,
> then add `"C4", "B"` to `[tool.ruff.lint] select` in `pyproject.toml`. If
> the precondition fails, write one line to `pr_info/.blocked.txt` and stop
> without editing `pyproject.toml`. Otherwise run the verification commands
> in step 10, fix anything they flag, and make exactly one commit.
