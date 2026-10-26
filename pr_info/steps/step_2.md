# Step 2 — Move `TestPromptClaudeCwd` → `test_prompt_claude_cwd.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`.
> This is a pure refactoring: move code only with `mcp__mcp-tools-py__move_symbol`, and edit only imports.
> Use MCP tools only. If any check below fails, write one line to `pr_info/.blocked.txt` and stop.
> Finish with the standard checks from the summary and produce exactly one commit.

## WHERE

- Source: `tests/cli/commands/test_prompt.py`
- Destination (new): `tests/cli/commands/test_prompt_claude_cwd.py`

## WHAT

Move the class `TestPromptClaudeCwd` (3 tests; covers the Claude subprocess cwd: CWD fallback,
`--project-dir`, and the combination with other args). It calls `_make_text_events`, which **stays** in
`test_prompt.py`. There are no function signatures to add or change.

## HOW

1. Precondition: step 1 is committed and `test_prompt_session_id_format.py` exists. If not, write one line
   to `pr_info/.blocked.txt` and stop.
2. Dry run: `move_symbol(source_file="tests/cli/commands/test_prompt.py", symbol_names=["TestPromptClaudeCwd"], dest_file="tests/cli/commands/test_prompt_claude_cwd.py", dry_run=true)`.
   It must list only those two files. If it lists any other file, write one line to `pr_info/.blocked.txt` and stop.
3. Real call with `dry_run=false`. If it times out or reports `Token <…> cannot be matched`, write one line to
   `pr_info/.blocked.txt` and stop.
4. Check:
   - `_make_text_events` is still defined in `test_prompt.py`.
   - The destination imports it with `from tests.cli.commands.test_prompt import _make_text_events`.
   - The three call sites in the moved class are still bare `_make_text_events(` (not `test_prompt._make_text_events(`).

   If any of these fails, move the class back with `move_symbol`, write one line to `pr_info/.blocked.txt` and stop.
5. Fix imports only.

## ALGORITHM

```
dry = move_symbol(..., dry_run=True); assert dry.files == {source, dest}
move_symbol(..., dry_run=False)
assert "_make_text_events" in list_symbols(source)
assert dest imports _make_text_events from tests.cli.commands.test_prompt
fix_imports(); run_format_code(); run_standard_checks(); check counts; commit
```

## DATA — expected end state

- `test_prompt_claude_cwd.py` imports: `argparse`, `from pathlib import Path`,
  `from unittest.mock import Mock, patch`, `pytest`, `from mcp_coder.cli.commands.prompt import execute_prompt`,
  `from tests.cli.commands.test_prompt import _make_text_events`. It imports no `Test*` class.
- `test_prompt.py`: no import changes expected (`argparse`, `Path`, `Mock`, `patch`, `pytest` are still used
  by `TestExecutePrompt` / `TestAddSystemPromptsFlag`).
- Collect counts (no marker filter): `test_prompt.py` **15**, `test_prompt_claude_cwd.py` **3**,
  `test_prompt_session_id_format.py` **4**, `tests/cli/commands/` **1039**, whole suite **6463**
  (or the step-1 baseline if it differed). A higher count means a `Test*` class was imported.
- The `.large-files-allowlist` entry stays (the base file is still ~785 lines).

## Verification

- Standard checks from the summary: all green.
- Run the three files with the fast-unit exclusion → 22 passed.
- `search_files(pattern="test_prompt\\.\\w", glob="tests/**/*.py")` → 0 matches.
- Compact diff follows the summary's compact-diff rule.
- If any count or check deviates, write one line to `pr_info/.blocked.txt` and stop.

## Commit

`test(prompt): move Claude cwd tests to test_prompt_claude_cwd.py`
