# Step 2 — Move `TestAskClaudeCodeCliStream` to `test_claude_code_cli_streaming.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly. Step 1 must
> already be done (the helpers are in `conftest.py`). This is a pure refactoring: move code with
> `mcp__mcp-tools-py__move_symbol` (dry run first) and change nothing except imports and
> `.large-files-allowlist`. Run all checks listed below, then make exactly one commit.

## Preconditions

- `_make_stream_gen` is defined in `tests/llm/providers/claude/conftest.py` and not in
  `test_claude_code_cli.py`. If this does not hold, write one line to `pr_info/.blocked.txt` and stop.
- `tests/llm/providers/claude/test_claude_code_cli_streaming.py` does not exist. If it does, write
  one line to `pr_info/.blocked.txt` and stop.

## WHERE

- Source: `tests/llm/providers/claude/test_claude_code_cli.py`
- Destination: `tests/llm/providers/claude/test_claude_code_cli_streaming.py` (**new**)
- `.large-files-allowlist`

## WHAT (moved verbatim — no edits)

```python
class TestAskClaudeCodeCliStream:  # 9 tests, exercises claude_code_cli_streaming.ask_claude_code_cli_stream
    ...
```

## HOW

1. **Baseline:** run `run_pytest_check(extra_args=["--collect-only", "-q", "tests/llm/providers/claude/"])`
   with no marker filter. Note the directory total; `test_claude_code_cli.py` should show 39.
2. Run `move_symbol(source_file="tests/llm/providers/claude/test_claude_code_cli.py",
   symbol_names=["TestAskClaudeCodeCliStream"],
   dest_file="tests/llm/providers/claude/test_claude_code_cli_streaming.py", dry_run=True)`.
   If the dry run reports an error, write one line to `pr_info/.blocked.txt` and stop.
3. Run the same call with `dry_run=False`.
4. Make the imports of the new file exactly this, with no module docstring added:
   ```python
   import json
   import tempfile
   from pathlib import Path
   from unittest.mock import MagicMock, patch

   import pytest

   from mcp_coder.llm.providers.claude.claude_code_cli_streaming import (
       ask_claude_code_cli_stream,
   )

   from .conftest import _make_stream_gen
   ```
   Convert any absolute `tests.llm.providers.claude.conftest` import to the relative form above.
5. Original file: remove the now-unused `ask_claude_code_cli_stream` import. Keep `json`,
   `tempfile`, `Path`, `MagicMock`, `patch`, `pytest`, `TimeoutExpired`, `CalledProcessError`,
   and `from .conftest import StreamJsonFactory, _make_stream_gen`.
6. Delete the line `tests/llm/providers/claude/test_claude_code_cli.py` from `.large-files-allowlist`.

## ALGORITHM

```
check preconditions; if any fails: write blocked line, stop
collect baseline
dry-run move class -> new file; if error: write blocked line, stop
apply move; normalize imports in both files
remove allowlist entry
format, run checks, collect again (30 + 9, directory total == baseline); commit
```

## DATA

- `test_claude_code_cli.py`: 30 tests, ~485 lines. `test_claude_code_cli_streaming.py`: 9 tests,
  ~335 lines. The directory total is unchanged.

## Checks (all must pass)

- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_ruff_check`
- `mcp__mcp-tools-py__run_pytest_check` with `-n auto` and the fast-unit marker exclusion from
  CLAUDE.md. The moved tests carry no integration markers.
- `run_pytest_check(extra_args=["--collect-only", "-q", "tests/llm/providers/claude/"])`: the
  directory total equals the baseline, `test_claude_code_cli.py` = 30 and
  `test_claude_code_cli_streaming.py` = 9.
- `run_pytest_check(markers=["claude_cli_integration"], extra_args=["-n", "auto"])` if the Claude CLI
  is available. Otherwise, note in the commit body that it was skipped and why. The PR description
  must also state that it was skipped and why; do not rely on the commit body alone.
- `mcp__mcp-tools-py__run_lint_imports_check`
- `mcp__mcp-tools-py__run_tach_check`
- `mcp__mcp-tools-py__run_vulture_check`
- `mcp__mcp-workspace__check_file_size`: passes and reports no stale allowlist entries.
- `mcp__mcp-workspace__git` diff with `compact=true`: only import changes, the new file header and
  the allowlist line may remain visible.

## Commit

`test(claude): split streaming tests out of test_claude_code_cli`
