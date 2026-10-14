# Step 4 — Annotate the icoder mock/stub-callable sites

Read `pr_info/steps/summary.md` first for overall context.

Part of issue #1171. These are the "mock callable standing in for a real
function" pattern — fix by mirroring the signature of the function/builtin
being replaced.

## Precondition check

Run `mcp__mcp-tools-py__run_ruff_check` with
`select=["ANN001","ANN002","ANN003","ANN202"]`, `max_issues=10`. If it does
not report `mock_execute` at `tests/icoder/test_cli_icoder_parser.py:74` and
`fake_open` at `tests/icoder/test_event_log.py:390`, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- Modify: `tests/icoder/test_cli_icoder_parser.py`
- Modify: `tests/icoder/test_event_log.py`

## WHAT

`test_cli_icoder_parser.py:74` — `mock_execute` replaces
`execute_icoder(args: argparse.Namespace) -> int`
(`src/mcp_coder/cli/commands/icoder.py`). Change:

```python
def mock_execute(args):  # type: ignore[no-untyped-def]
```
to
```python
def mock_execute(args: argparse.Namespace) -> int:
```

Add `import argparse` if not already present in that file; keep the `return 0`
body unchanged.

`test_event_log.py:390` — `fake_open` replaces the builtin `open()` as called
in `src/mcp_coder/icoder/core/event_log.py` (always `open(path, "a",
encoding="utf-8")` or `open(path, "r", encoding="utf-8")` — text mode only).
Change:

```python
def fake_open(file, *args, **kwargs):  # type: ignore[no-untyped-def]
```
to
```python
def fake_open(file: str | os.PathLike[str], *args: Any, **kwargs: Any) -> IO[str]:
```

`*args`/`**kwargs` stay `Any` — this mirrors `open()`'s genuinely polymorphic
signature, which is exactly the case `ANN401` is excluded for. Add
`import os` and `from typing import IO, Any` if not already present (check
existing imports in the file first — do not duplicate).

## HOW

Direct signature edits, no new abstraction, no behavior change.

## ALGORITHM

N/A — type-annotation-only changes.

## DATA

N/A.

## TDD

Not applicable: no new behavior, pure annotation. Verification is
mypy/ruff/pytest agreeing.

## Verification

- `mcp__mcp-tools-py__run_pytest_check` targeting `tests/icoder/` first
  (`extra_args=["tests/icoder", "-n", "auto"]`), then the full fast suite.
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_format_code`, then commit.

## Commit

One commit: `fix(tests): annotate icoder mock/stub callables`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement
> step 4 exactly as specified: annotate `mock_execute` in
> `test_cli_icoder_parser.py` and `fake_open` in `test_event_log.py` per the
> signatures given. Run the verification commands listed in the step, fix
> anything they report, then run `run_format_code` and commit with the given
> message. If the precondition check fails, write one line to
> `pr_info/.blocked.txt` and stop.
