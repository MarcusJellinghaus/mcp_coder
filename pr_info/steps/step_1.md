# Step 1 — `C408`: unnecessary `dict()` calls → literal dicts

Context: see `pr_info/steps/summary.md` for the overall goal and file list.
This step fixes the 4 `C408` findings only. `C4`/`B` are **not** enabled in
`pyproject.toml` yet (that's step 10) — this step's commit must pass the
project's *current* ruff config unchanged.

## WHERE

- `tests/cli/commands/test_check_branch_status_pr_waiting.py` — `_make_base_args()` and `_make_report()`
- `tests/workflows/review/test_reviewer.py` — `_call()` and `_call_get_verdict()`

## WHAT

Each of the 4 functions builds a `dict[str, object]` (or untyped dict) via
`dict(key=value, ...)`. Ruff `C408` flags this because a keyword-call
`dict(...)` is unnecessary when every key is a valid identifier — a literal
is equivalent and preferred.

## HOW

For each of the 4 sites: run `mcp__mcp-tools-py__run_ruff_check(select=["C408"])`
to get the exact current line. Replace `dict(k1=v1, k2=v2, ...)` with
`{"k1": v1, "k2": v2, ...}`. Keep the exact same keys and values, in the same
order. Do not touch anything else in these functions (e.g. `.update(overrides)`
calls stay as-is — only the `dict(...)` construction changes).

## ALGORITHM

```
for site in [the 4 C408 locations]:
    read the dict(...) call
    rewrite dict(k=v, ...) -> {"k": v, ...}, same keys/values/order
    leave surrounding code untouched
```

## DATA

No data structures change shape — a `dict[str, object]` literal is
value-identical to the `dict(...)` call it replaces.

## Precondition

If `mcp__mcp-tools-py__run_ruff_check(select=["C408"])` reports a different
count than 4, or reports locations outside the two files named above, write
one line to `pr_info/.blocked.txt` and stop.

## Verification

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_ruff_check(select=["C408"])        # expect 0 findings
mcp__mcp-tools-py__run_ruff_check()                        # default rules still pass
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_mypy_check
```

## Commit

One commit, e.g.:

```
refactor(tests): rewrite dict() calls as literals (C408)
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement
> step 1 exactly as specified: fix all 4 ruff `C408` findings by rewriting
> `dict(...)` keyword calls as dict literals in the two files listed, with no
> other behavior change. If the precondition in step 1 fails, write one line
> to `pr_info/.blocked.txt` and stop. Otherwise run the verification commands
> listed in step 1, fix anything they flag, and when all are green make
> exactly one commit for this step.
