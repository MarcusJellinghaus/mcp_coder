# Summary — Split `tests/llm/providers/claude/test_claude_code_cli.py` (#1313)

Part of #353. Process: `docs/processes-prompts/refactoring-guide.md`.

## Goal

Get `tests/llm/providers/claude/test_claude_code_cli.py` (827 lines, allowlisted) under the
750-line limit and off `.large-files-allowlist` by a **pure move**. This is a test-only split: no
source file changes.

## Rules (from the issue — apply to every step)

- **Move, don't change.** Classes, functions and constants move verbatim. No logic edits, renames,
  reformatting beyond the formatter, test deletions or merges.
- **Only allowed edits:** import statements, `conftest.py` placement, `.large-files-allowlist`.
- **Use the refactoring tools** (`list_symbols`, `move_symbol` with a dry run first,
  `find_references`). Never move code by hand.
- **Clean deletion.** No stubs, no re-exports.
- No new module docstrings (`D` is ignored for `tests/**`).

## Architectural / design changes

| Before | After |
|---|---|
| `test_claude_code_cli.py` holds tests for two source modules (`claude_code_cli` and `claude_code_cli_streaming`) plus private mock helpers | Tests are split by source module: `test_claude_code_cli.py` ↔ `claude_code_cli.py`, `test_claude_code_cli_streaming.py` ↔ `claude_code_cli_streaming.py` |
| `_MockStreamResult` and `_make_stream_gen` are local to `test_claude_code_cli.py` | Both live in `tests/llm/providers/claude/conftest.py`, next to `StreamJsonFactory`, and both test files import them via `from .conftest import ...` |

Design decisions:
- The helpers go to `conftest.py` so that neither test file imports from the other. The directory
  already imports `StreamJsonFactory` from `.conftest`, so this follows existing practice.
- `TestClaudeCodeCliBackwardCompatibility` and `TestSessionIdPropagation` stay because they call
  `ask_claude_code_cli`. Their streaming patches are only the mocking seam.
- The duplicate copies of `_MockStreamResult` in `test_claude_cli_wrappers.py`,
  `test_claude_code_cli_heartbeat.py` and `test_claude_mcp_config.py` are left untouched.
  Removing them would be a code change, which is out of scope.

## Files created / modified

| Path | Change |
|---|---|
| `tests/llm/providers/claude/conftest.py` | modified — receives `_MockStreamResult`, `_make_stream_gen` and their imports (`Iterator`, `CommandResult`) |
| `tests/llm/providers/claude/test_claude_code_cli.py` | modified — loses the helpers and `TestAskClaudeCodeCliStream`; imports trimmed (~485 lines) |
| `tests/llm/providers/claude/test_claude_code_cli_streaming.py` | **created** — `TestAskClaudeCodeCliStream` (~335 lines) |
| `.large-files-allowlist` | modified — entry `tests/llm/providers/claude/test_claude_code_cli.py` removed |

No source files under `src/` and no packages or folders are added.

## Test counts

`test_claude_code_cli.py`: 39 → 30. `test_claude_code_cli_streaming.py`: 0 → 9. The
`tests/llm/providers/claude/` directory total must stay the same (check with `--collect-only -q`
and no marker filter).

## TDD note

This is a pure refactoring, so no new tests are written. The existing tests act as the safety net:
each step collects tests before and after the move, the totals must match, and the full check suite
must pass.

## Steps

1. [step_1.md](./step_1.md) — move the shared helpers into `conftest.py`.
2. [step_2.md](./step_2.md) — move `TestAskClaudeCodeCliStream` into the new
   `test_claude_code_cli_streaming.py` and remove the allowlist entry.
