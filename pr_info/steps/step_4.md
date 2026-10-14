# Step 4 — E721: use `is` for type-literal comparisons in `test_types.py`

See `pr_info/steps/summary.md` for the overall goal and rationale.

## Precondition check

Run `mcp__mcp-tools-py__run_ruff_check` with `select=["E721"]` and
`extra_args=["--preview"]`. Confirm it reports `E721` at exactly
`tests/llm/test_types.py` lines 67, 68, 69, 75. If the locations differ,
write one line to `pr_info/.blocked.txt` and stop.

## WHERE

`tests/llm/test_types.py`, inside `test_llm_response_dict_field_types`
(lines 67–75):

```python
assert hints["version"] == str
assert hints["timestamp"] == str
assert hints["text"] == str
...
assert hints["provider"] == str
```

## WHAT

No function signatures change. Replace `==` with `is` at these 4 sites.
These compare a type-hint value against the class literal `str` — a type
comparison, not an instance check — so `isinstance(hints["version"], str)`
would be semantically wrong (always `False`: the class `str` is not an
instance of `str`). `is` is correct per ruff's own E721 message, and
preserves the existing assertion (`str` is a singleton class object, so
`==` and `is` already agree here; `is` just states the intent precisely).

Line 72 (`hints["session_id"] == str | None`) is a union-type comparison,
not a bare class-literal comparison, and is not flagged by E721 — leave it
unchanged.

## HOW

Direct in-place edits, 4 occurrences, `==` → `is`.

## ALGORITHM

N/A — single-operator swap, no control-flow change.

## DATA

No change to return values or data structures — the assertions still check
the same 4 hint types.

## Test-first note

The assertion's truth value is unchanged (`str is str` and `str == str` are
both `True`), so no new test is needed. Verification is the existing test
passing unchanged.

## Steps

1. At lines 67, 68, 69, 75, change `== str` to `is str`.
2. Run `mcp__mcp-tools-py__run_pytest_check` with
   `extra_args=["-n", "auto", "tests/llm/test_types.py"]`, then the full
   unit-test selection:
   `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`.
3. Run `mcp__mcp-tools-py__run_pylint_check` and `mcp__mcp-tools-py__run_mypy_check`.
4. Run `mcp__mcp-tools-py__run_ruff_check` with `select=["E721"]`,
   `extra_args=["--preview"]` — must report 0 findings.
5. Run `mcp__mcp-tools-py__run_format_code`.
6. Commit: `fix(lint): use is for type-literal comparisons in test_types.py`.

## LLM prompt for this step

> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_4.md`: change the 4 listed `== str` type comparisons
> in `tests/llm/test_types.py` to `is str`. Follow the precondition check
> first — if it fails, write one line to `pr_info/.blocked.txt` and stop.
> Otherwise make the edits, run the checks listed in the step, format the
> code, and produce exactly one commit with the given message.
