# review-implementation review log 1

## Round 1 — 2026-10-21
**Findings**:
Review in progress: source diff read; now checking the review CI-gate exception handling and the review formatter call site.`src/mcp_coder/workflow_steps/commit.py:98` — low — `except FormatterConfigError: raise` can never run: nothing inside the `try` raises `FormatterConfigError`. A `ValueError` that `resolve_steps` raises inside `run_format_code` still falls into the broad `except` and becomes `False` instead of a config error. Either drop the clause or re-raise `ValueError` as `FormatterConfigError`.
`tests/workflows/implement/test_core.py:150` — low — Issue step 9 asks for a "`format_code = false` → formatter not called" test for each workflow. Rebase, review, fix-ci and `check_branch_status` have one; implement has none (only `run_formatters` is mocked).
`tests/workflow_steps/test_commit.py:94` — low — `test_resolves_cleanly_returns_none` passes only because the autouse fixture in `tests/conftest.py` mocks `resolve_steps`, so it never checks real resolution. Write a `[tool.black]` pyproject into `tmp_path` and undo the fixture's patch so the real `resolve_steps` runs.
**Decisions**:
Verdict(decision='tasks', tasks=['In src/mcp_coder/workflow_steps/commit.py around line 98, make config errors propagate: catch the ValueError that resolve_steps raises inside run_format_code and re-raise it as FormatterConfigError (chained with `from`), so it no longer falls into the broad except and returns False. Remove the `except FormatterConfigError: raise` clause, which can never run, unless the new re-raise needs it. Add a test that a resolve_steps ValueError surfaces as FormatterConfigError.', 'In tests/workflows/implement/test_core.py, add a test for the implement workflow: with `format_code = false` in [tool.mcp-coder], the formatter is not called. Match the existing tests for rebase, review, fix-ci and check_branch_status.', "In tests/workflow_steps/test_commit.py, change test_resolves_cleanly_returns_none (line 94) so the real resolve_steps runs. Undo the autouse fixture's resolve_steps patch for this test, for example by monkeypatching the original back or with a marker or fixture override. Write a pyproject.toml with a [tool.black] section into tmp_path and assert the function returns None."], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-10-21
**Findings**:
Source diff reviewed; checking the upstream `run_format_code` signature next.Review found nothing substantive so far; running the affected test files to confirm.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
