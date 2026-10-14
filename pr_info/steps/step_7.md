# Step 7 — `B011`: `assert False` → `raise AssertionError(...)`

Context: see `pr_info/steps/summary.md`. Fixes the 1 `B011` finding.

## WHERE

- `tests/llm/session/test_resolver.py` — `test_continue_from_invalid_json()`

## WHAT

```python
try:
    json.loads(invalid_json)
    assert False, "Should have raised JSONDecodeError"
except json.JSONDecodeError:
    pass
```

`assert False` is removed by `python -O`, silently defeating the test's
own safety net. `raise AssertionError(...)` is unconditional and carries
the exact same message.

## HOW

Run `mcp__mcp-tools-py__run_ruff_check(select=["B011"])` to confirm the exact
line. Replace `assert False, "Should have raised JSONDecodeError"` with
`raise AssertionError("Should have raised JSONDecodeError")`.

## ALGORITHM

```
locate "assert False, <message>"
replace with "raise AssertionError(<message>)"
```

## DATA

No data/behavior change for a normal `pytest` run (the exception raised and
its message are identical); the only behavioral difference removed is
disappearing under `python -O`, which is the point of the fix.

## Precondition

If `mcp__mcp-tools-py__run_ruff_check(select=["B011"])` reports a different
count than 1, or a location outside the file named above, write one line to
`pr_info/.blocked.txt` and stop.

## Verification

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_ruff_check(select=["B011"])    # expect 0 findings
mcp__mcp-tools-py__run_ruff_check()
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_mypy_check
```

## Commit

```
fix(tests): raise AssertionError instead of assert False (B011)
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_7.md`. Implement
> step 7 exactly as specified: replace the single `assert False, "..."` with
> `raise AssertionError("...")` in the file listed. If the precondition
> fails, write one line to `pr_info/.blocked.txt` and stop. Otherwise run the
> verification commands in step 7, fix anything they flag, and make exactly
> one commit.
