# Step 5 — Annotate `make_copilot_jsonl_output` usages

Read `pr_info/steps/summary.md` first for overall context.

Part of issue #1171. `tests/llm/providers/copilot/conftest.py` already
declares the fixture's real type
(`make_copilot_jsonl_output() -> Callable[..., list[str]]`); the 6 test
parameters consuming it in `test_copilot_cli.py` should use that exact type,
not `Any`.

## Precondition check

Run `mcp__mcp-tools-py__run_ruff_check` with `select=["ANN001"]`,
`max_issues=10`. If it does not report 6 occurrences in
`tests/llm/providers/copilot/test_copilot_cli.py` at lines 45, 51, 57, 63,
74, 99, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

`tests/llm/providers/copilot/test_copilot_cli.py`

## WHAT

For each of the 6 test methods, change:

```python
def test_parse_output_extracts_text(self, make_copilot_jsonl_output) -> None:  # type: ignore[no-untyped-def]
```
to
```python
def test_parse_output_extracts_text(
    self, make_copilot_jsonl_output: Callable[..., list[str]]
) -> None:
```

Remove the `# type: ignore[no-untyped-def]` on each of the 6 lines (74
through the file — see current locations: 45, 51, 57, 63, 74, 99).

## HOW

`from collections.abc import Callable` is already imported in this file
(used by the conftest fixture's own annotation style) — confirm, add if
missing.

## ALGORITHM

N/A — type-annotation-only change, mirroring the fixture's own declared
return type.

## DATA

N/A.

## TDD

Not applicable: no new behavior.

## Verification

- `mcp__mcp-tools-py__run_pytest_check` targeting
  `tests/llm/providers/copilot/test_copilot_cli.py`, then the full fast
  suite.
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_format_code`, then commit.

## Commit

One commit: `fix(tests): annotate make_copilot_jsonl_output parameters`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement
> step 5 exactly as specified: annotate the 6
> `make_copilot_jsonl_output` parameters in `test_copilot_cli.py` as
> `Callable[..., list[str]]`, removing the `# type: ignore` comments. Run the
> verification commands listed in the step, fix anything they report, then
> run `run_format_code` and commit with the given message. If the
> precondition check fails, write one line to `pr_info/.blocked.txt` and
> stop.
