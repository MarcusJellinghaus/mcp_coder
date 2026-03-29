# Step 1: HelpHintArgumentParser class + unit tests

## Context

See [summary.md](./summary.md) for overall design. This step creates the core class and its unit tests.

## LLM Prompt

> Implement Step 1 of issue #624 (CLI help hints). Read `pr_info/steps/summary.md` and this file for context.
> Create `HelpHintArgumentParser` in `parsers.py` with unit tests in `tests/cli/test_parsers.py`.
> Run all three code quality checks (pylint, mypy, pytest) and fix any issues. Commit when green.

## WHERE

- `src/mcp_coder/cli/parsers.py` — add class, export it
- `tests/cli/test_parsers.py` — new test file

## WHAT

### New class in `parsers.py`

```python
class HelpHintArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn: ...
```

### Test functions in `test_parsers.py`

```python
class TestHelpHintArgumentParser:
    def test_error_appends_help_hint(self) -> None: ...
    def test_error_exits_with_code_2(self) -> None: ...
    def test_error_includes_prog_name_in_hint(self) -> None: ...
    def test_subparser_inherits_help_hint_class(self) -> None: ...
    def test_subparser_error_uses_subcommand_prog(self) -> None: ...
```

## HOW

- Import `NoReturn` from `typing` in `parsers.py`
- Class inherits from `argparse.ArgumentParser` (not `WideHelpFormatter`)
- Override `error()` method only
- Tests use `capsys` to capture stderr output and `pytest.raises(SystemExit)` for exit code

## ALGORITHM (HelpHintArgumentParser.error)

```
def error(self, message):
    self.print_usage(sys.stderr)           # print usage line
    self._print_message(                   # print "prog: error: message"
        f"{self.prog}: error: {message}\n", sys.stderr
    )
    self._print_message(                   # print help hint
        f"Try '{self.prog} --help' for more information.\n", sys.stderr
    )
    self.exit(2, "")                       # exit code 2 (argparse/POSIX standard)
```

Note: We fully override rather than calling `super().error()` after appending, because `super().error()` calls `self.exit()` — we can't append text after it. The implementation replicates argparse's own `error()` logic (usage + error message) and adds the hint line.

## DATA

- Input: `message: str` (from argparse, e.g., `"unrecognized arguments: --resume-session"`)
- Output: none (calls `sys.exit(2)`)
- Side effect: prints to stderr:
  ```
  usage: mcp-coder [--version] [--log-level LEVEL] COMMAND ...
  mcp-coder: error: unrecognized arguments: --resume-session
  Try 'mcp-coder --help' for more information.
  ```
