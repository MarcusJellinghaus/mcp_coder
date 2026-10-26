# Step 3 — Move `TestAddSystemPromptsFlag` → `test_prompt_system_prompts.py` + drop allowlist entry

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`.
> This is a pure refactoring: move code only with `mcp__mcp-tools-py__move_symbol`, edit only imports and
> `.large-files-allowlist`. Use MCP tools only. If any check below fails, write one line to
> `pr_info/.blocked.txt` and stop. Finish with the standard checks from the summary and produce exactly one commit.

## WHERE

- Source: `tests/cli/commands/test_prompt.py`
- Destination (new): `tests/cli/commands/test_prompt_system_prompts.py`
- `.large-files-allowlist` (remove the line `tests/cli/commands/test_prompt.py`)

## WHAT

Move the class `TestAddSystemPromptsFlag` (5 tests; covers `--add-system-prompts` → `inject_prompts` on the
stream, session-id and json paths) as a whole. It calls `_make_text_events`, which **stays**. There are no
function signatures to add or change.

The allowlist removal is in this step because only now does the base file drop under the limit. Leaving
the entry in would make `check_file_size` report it as stale.

## HOW

1. Precondition: steps 1–2 are committed and both new files exist. If not, write one line to
   `pr_info/.blocked.txt` and stop.
2. Dry run: `move_symbol(source_file="tests/cli/commands/test_prompt.py", symbol_names=["TestAddSystemPromptsFlag"], dest_file="tests/cli/commands/test_prompt_system_prompts.py", dry_run=true)`.
   It must list only those two files. If it lists any other file, write one line to `pr_info/.blocked.txt` and stop.
3. Real call with `dry_run=false`. If it times out or reports `Token <…> cannot be matched`, write one line to
   `pr_info/.blocked.txt` and stop.
4. Same checks as step 2:
   - `_make_text_events` is still defined in `test_prompt.py`.
   - The destination imports it from `tests.cli.commands.test_prompt`.
   - The three call sites in the moved class are still bare `_make_text_events(`.

   If any of these fails, move the class back, write one line to `pr_info/.blocked.txt` and stop.
5. Fix imports only.
6. Remove the line `tests/cli/commands/test_prompt.py` from `.large-files-allowlist`, matching it by path text,
   with `edit_file`.

## ALGORITHM

```
dry = move_symbol(..., dry_run=True); assert dry.files == {source, dest}
move_symbol(..., dry_run=False)
assert helper stays; dest imports helper; call sites bare
fix_imports(); remove allowlist line
run_format_code(); assert lines(test_prompt.py) < 600
run_standard_checks(); check counts + audits; commit
```

## DATA — expected end state

- `test_prompt_system_prompts.py` imports: `argparse`, `from pathlib import Path`,
  `from unittest.mock import Mock, patch`, `pytest`, `from mcp_coder.cli.commands.prompt import execute_prompt`,
  `from tests.cli.commands.test_prompt import _make_text_events`.
- `test_prompt.py` imports: `argparse`, `json`, `logging`, `from pathlib import Path`, `from unittest import mock`,
  `from unittest.mock import Mock, mock_open, patch`, `pytest`, `execute_prompt`. It contains only the module
  docstring, `_make_text_events` and `TestExecutePrompt`, all unchanged. ~581 lines; if it is 600 lines or more
  after formatting, write one line to `pr_info/.blocked.txt` and stop.
- Collect counts (no marker filter): `test_prompt.py` **10**, `test_prompt_session_id_format.py` **4**,
  `test_prompt_claude_cwd.py` **3**, `test_prompt_system_prompts.py` **5**, `tests/cli/commands/` **1039**,
  whole suite **6463** (or the step-1 baseline).

## Verification

- Standard checks from the summary: all green. `check_file_size` passes and reports no stale allowlist entries.
- Run the four files with the fast-unit exclusion → **22 passed**.
- Call-site audit (`search_files`, `glob="tests/**/*.py"`):
  - `test_prompt\.\w` → 0 matches
  - `from tests\.cli\.commands\.test_prompt import _make_text_events` → 2 matches (`_claude_cwd`, `_system_prompts`)
- Compact diff over the whole branch, run before the commit: first stage the step-3 changes
  (`git add tests/ .large-files-allowlist`), so the new `test_prompt_system_prompts.py` is tracked. Then diff the
  remote-tracking base ref `origin/<base>` (`<base>` from `get_base_branch`, e.g. `origin/main`; this checkout
  has no local `main` ref, so a bare `main` fails with `bad revision`) against the index:
  `mcp__mcp-workspace__git(command="diff", args=["--cached", "origin/<base>"], compact=true,
  pathspec=["tests/", ".large-files-allowlist"])`. This leaves out the `pr_info/` changes and shows the committed
  steps 1–2 together with the staged step-3 changes. The diff must follow the summary's compact-diff rule. The only non-move hunks:
  the removed `from typing import Any`, the new files' import headers, and the one allowlist line.
- If any count or check deviates, write one line to `pr_info/.blocked.txt` and stop.

## Commit

`test(prompt): move system-prompts tests to test_prompt_system_prompts.py`
