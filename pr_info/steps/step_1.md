# Step 1 — Move shared stream-mock helpers into `conftest.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly. This is a pure
> refactoring: move code with `mcp__mcp-tools-py__move_symbol` (dry run first) and change nothing
> except imports. Run all checks listed below, then make exactly one commit.

## WHERE

- Source: `tests/llm/providers/claude/test_claude_code_cli.py`
- Destination: `tests/llm/providers/claude/conftest.py` (existing)

## WHAT (moved verbatim — no edits)

```python
class _MockStreamResult:
    def __init__(self, lines: list[str], return_code: int = 0, timed_out: bool = False) -> None: ...
    def __iter__(self) -> Iterator[str]: ...
    @property
    def result(self) -> CommandResult: ...

def _make_stream_gen(lines: list[str], return_code: int = 0, timed_out: bool = False) -> _MockStreamResult: ...
```

## HOW

1. **Baseline:** run `mcp__mcp-tools-py__run_pytest_check(extra_args=["--collect-only", "-q", "tests/llm/providers/claude/"])`
   with no marker filter. Note the directory total and the count for `test_claude_code_cli.py`
   (expected 39).
2. Run `move_symbol(source_file="tests/llm/providers/claude/test_claude_code_cli.py",
   symbol_names=["_MockStreamResult", "_make_stream_gen"],
   dest_file="tests/llm/providers/claude/conftest.py", dry_run=True)`. If the dry run reports an
   error, write one line to `pr_info/.blocked.txt` and stop.
3. Run the same call with `dry_run=False`.
4. Check the imports in `conftest.py`. It must have `from collections.abc import Callable, Iterator`
   (one line) and `from mcp_coder.utils.subprocess_runner import CommandResult`. Add only what is
   missing. Place the helpers after the existing `StreamJsonFactory` alias or fixture; the tool's
   placement is acceptable.
5. Fix the imports in `test_claude_code_cli.py`:
   - It must import the helper as `from .conftest import StreamJsonFactory, _make_stream_gen`, as a
     single line. If the tool wrote an absolute import (`tests.llm.providers.claude.conftest`),
     change it to this relative form.
   - Remove `Iterator` and `CommandResult` if they are no longer used. Do not import
     `_MockStreamResult`.
   - `ask_claude_code_cli_stream` stays for now (it is still used until step 2).

## ALGORITHM

```
collect baseline
dry-run move helpers -> conftest; if error: write blocked line, stop
apply move
normalize imports (conftest gains Iterator/CommandResult; test file imports _make_stream_gen from .conftest)
format, run checks, collect again; totals must equal baseline
commit
```

## DATA

- No behavioural change. Collected test counts are unchanged: 39 in `test_claude_code_cli.py`, and
  the directory total equals the baseline.

## Checks (all must pass)

- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_ruff_check`
- `mcp__mcp-tools-py__run_pytest_check` with `-n auto` and the fast-unit marker exclusion from CLAUDE.md
- `run_pytest_check(extra_args=["--collect-only", "-q", "tests/llm/providers/claude/"])`: the
  directory total equals the baseline. This also proves that the integration modules, which share
  `conftest.py`, still import.
- `mcp__mcp-workspace__git` diff with `compact=true`: only import changes may remain visible.

## Commit

`test(claude): move stream mock helpers to conftest`
