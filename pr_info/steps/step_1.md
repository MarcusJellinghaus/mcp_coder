# Step 1 — Remove the `commit clipboard` command

**Goal:** Delete the obsolete `commit clipboard` CLI command and everything that
exists only to serve it. `utils/clipboard.py` stays for now (still used by icoder
— removed in Step 2). One commit.

This is a deletion step, so TDD means **delete the tests for the removed
behaviour in the same commit** and confirm the remaining suite stays green.

## WHERE

- `src/mcp_coder/cli/parsers.py`
- `src/mcp_coder/cli/main.py`
- `src/mcp_coder/cli/commands/commit.py`
- `src/mcp_coder/cli/commands/__init__.py`
- `src/mcp_coder/cli/commands/help.py`
- `tests/cli/commands/test_commit.py`
- `tests/cli/test_parsers.py`
- `docs/cli-reference.md`
- `docs/processes-prompts/development-process.md`

## WHAT

Remove these symbols / fragments:

- `cli/commands/commit.py`: functions `execute_commit_clipboard(args) -> int`
  and `get_commit_message_from_clipboard() -> Tuple[bool, str, Optional[str]]`,
  plus the now-unused import block:
  ```python
  from ...utils.clipboard import (
      get_clipboard_text,
      parse_commit_message,
      validate_commit_message,
  )
  ```
  Keep `execute_commit_auto`, `validate_git_repository`, `_push_after_commit`.
- `cli/parsers.py` → `add_commit_parsers`: delete the entire `clipboard_parser`
  block (the `commit_subparsers.add_parser("clipboard", ...)` and its two
  arguments). Keep the `auto` parser. Update the docstring
  `"""Add commit command parsers (auto, clipboard)."""` → `(auto)`.
- `cli/main.py`: in the import
  `from .commands.commit import execute_commit_auto, execute_commit_clipboard`
  drop `execute_commit_clipboard`; in `_handle_commit_command`, delete the
  `elif args.commit_mode == "clipboard": return execute_commit_clipboard(args)`
  branch.
- `cli/commands/__init__.py`: drop `execute_commit_clipboard` from both the
  `from .commit import ...` line and `__all__`.
- `cli/commands/help.py`: remove
  `Command("commit clipboard", "Use clipboard commit message")` from the `TOOLS`
  category.
- `tests/cli/commands/test_commit.py`: remove `execute_commit_clipboard` from the
  top import block, and delete the `TestCommitClipboardPush` class (the file's
  last class, ~lines 1203-end). Leave `TestGenerateCommitMessageWithLLMExtended`
  untouched — its `test_empty_parsed_commit_message` / `test_invalid_commit_message_format`
  test `commit_operations.parse_llm_commit_response`, **not** the clipboard helpers.
- `tests/cli/test_parsers.py`: remove the two `commit clipboard` parser tests
  (the `self._parse("commit", "clipboard", ...)` cases, ~lines 245-260).
- Docs: delete the `### commit clipboard` section in `docs/cli-reference.md`
  (incl. its row in the command table at the top) and the
  `mcp-coder commit clipboard` bullet in `docs/processes-prompts/development-process.md`.

## HOW (integration points)

- `commit auto` dispatch in `main.py:_handle_commit_command` is the only branch
  left besides the "not implemented" fallback — keep that fallback.
- After removing the clipboard import from `commit.py`, the symbols
  `get_clipboard_text` / `parse_commit_message` / `validate_commit_message`
  remain defined in `utils/clipboard.py` and re-exported by `utils/__init__.py`
  (`__all__`), so vulture will **not** flag them. They are deleted in Step 2.

## ALGORITHM

No logic — pure removal. Sketch of the resulting dispatch:

```
def _handle_commit_command(args):
    if args.commit_mode == "auto":
        return execute_commit_auto(args)
    log error "not yet implemented"; return 1
```

## DATA

No data-structure changes. `mcp-coder commit clipboard` now errors as an unknown
mode; `mcp-coder commit auto` is unchanged.

## VERIFY

Run formatter, then pylint / mypy / pytest (`-n auto`, unit subset) /
lint-imports / vulture. All green. `git grep -i "commit clipboard"` and
`git grep execute_commit_clipboard` return nothing.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement Step 1
> only: remove the `commit clipboard` command and all code, tests, and docs that
> exist solely for it, exactly as listed under WHERE/WHAT. Do **not** touch
> `utils/clipboard.py` or `pyperclip` (that is Step 2). Use the MCP workspace
> tools for all file edits. When done, run isort+black, then
> `run_pylint_check`, `run_mypy_check`, `run_pytest_check`
> (`extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`),
> `run_lint_imports_check`, and `run_vulture_check`. Fix any issue until all pass,
> then produce exactly one commit.
