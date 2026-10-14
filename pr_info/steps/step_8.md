# Step 8 — `B017`: narrow `pytest.raises(Exception)` to the real exception type

Context: see `pr_info/steps/summary.md`. Fixes the 1 `B017` finding.

## WHERE

- `tests/icoder/test_log_inventory.py` — `test_logsummary_is_frozen_and_hashable()`

## WHAT

```python
with pytest.raises(Exception):
    summary.n_turns = 4  # type: ignore[misc]
```

`LogSummary` is `@dataclass(frozen=True)` (`src/mcp_coder/icoder/core/types.py`).
Mutating a frozen dataclass instance raises `dataclasses.FrozenInstanceError`
specifically, not a blind `Exception` — asserting the exact type is both
more precise and the actual contract being tested.

## HOW

Run `mcp__mcp-tools-py__run_ruff_check(select=["B017"])` to confirm the exact
line. Add `import dataclasses` to the file's imports (it is not currently
imported there). Replace `pytest.raises(Exception)` with
`pytest.raises(dataclasses.FrozenInstanceError)`.

## ALGORITHM

```
add "import dataclasses" to the top-level imports
replace pytest.raises(Exception) -> pytest.raises(dataclasses.FrozenInstanceError)
```

## DATA

No data/behavior change — `FrozenInstanceError` is the exact exception
`dataclasses` raises on frozen-instance mutation; narrowing the assertion
does not change what the test exercises.

## Precondition

If `mcp__mcp-tools-py__run_ruff_check(select=["B017"])` reports a different
count than 1, or a location outside the file named above, or `LogSummary` is
no longer a frozen dataclass, write one line to `pr_info/.blocked.txt` and
stop.

## Verification

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_ruff_check(select=["B017"])    # expect 0 findings
mcp__mcp-tools-py__run_ruff_check()
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_mypy_check
```

## Commit

```
fix(tests): narrow pytest.raises to FrozenInstanceError (B017)
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_8.md`. Implement
> step 8 exactly as specified: narrow the single `pytest.raises(Exception)`
> to `pytest.raises(dataclasses.FrozenInstanceError)`, adding the
> `dataclasses` import. If the precondition fails, write one line to
> `pr_info/.blocked.txt` and stop. Otherwise run the verification commands
> in step 8, fix anything they flag, and make exactly one commit.
