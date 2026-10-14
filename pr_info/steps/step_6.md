# Step 6 — `B010`: `setattr` with a constant attribute (reposition existing `noqa`)

Context: see `pr_info/steps/summary.md`. Resolves the 1 `B010` finding by
repositioning an existing `noqa` — not a real code fix.

**Deviation, requires sign-off:** issue #1165's acceptance criterion is
"All 22 findings fixed, not suppressed." This site suppresses rather than
fixes. Confirm with the issue owner before committing this step, unless a
rewrite is found that satisfies `B010` without losing the Windows-only
`winerror` attribute's cross-platform mypy bypass.

## WHERE

- `tests/llm/providers/langchain/test_langchain_diagnostics.py` —
  `TestIsConnectionReset.test_oserror_winerror_10054()`

## WHAT

Current code:

```python
setattr(
    exc, "winerror", 10054
)  # noqa: B010  # Windows-only attr; bypass type checker for cross-platform CI
```

The `# noqa: B010` is already there with a documented rationale (bypassing
the type checker for a Windows-only attribute in a cross-platform test), but
ruff reports a multi-line call's violation on the **opening** line
(`setattr(`), not the closing one — so this `noqa` has never actually
applied, which is why it's still one of the 22 findings. This step does not
rewrite the `setattr` call or change its rationale; it only moves the
comment onto the line ruff actually flags.

## HOW

Run `mcp__mcp-tools-py__run_ruff_check(select=["B010"])` to confirm the exact
current line. Move the `# noqa: B010  # Windows-only attr; bypass type
checker for cross-platform CI` comment to the end of the `setattr(` line,
keeping the call itself multi-line (so the line stays within the 88-char
limit):

```python
setattr(  # noqa: B010  # Windows-only attr; bypass type checker for cross-platform CI
    exc, "winerror", 10054
)
```

## ALGORITHM

```
locate the setattr(...) call and its trailing noqa comment
move "  # noqa: B010  # Windows-only attr; ..." to the end of the opening "setattr(" line
```

## DATA

No behavior change — same `setattr` call, same rationale, correctly
positioned suppression comment.

## Precondition

If `mcp__mcp-tools-py__run_ruff_check(select=["B010"])` reports a different
count than 1, or a location outside the file named above, write one line to
`pr_info/.blocked.txt` and stop.

## Verification

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_ruff_check(select=["B010"])    # expect 0 findings
mcp__mcp-tools-py__run_ruff_check()
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_mypy_check
```

Note: `run_format_code` (black) may reformat the multi-line `setattr(...)`
call's line breaks — if it does, re-verify the `# noqa: B010` comment still
sits on the physical line ruff reports for the violation before committing.

## Commit

```
fix(tests): reposition misplaced noqa on multi-line setattr (B010)
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`. Implement
> step 6 exactly as specified: move the existing `# noqa: B010` comment onto
> the line ruff actually reports for this multi-line `setattr()` call,
> without changing the call or its rationale. If the precondition fails,
> write one line to `pr_info/.blocked.txt` and stop. Otherwise run the
> verification commands in step 6 — re-checking the `noqa` placement after
> `run_format_code` — fix anything flagged, and make exactly one commit.
