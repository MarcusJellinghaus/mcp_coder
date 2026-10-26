# Step 1 — Baseline + move `TestSessionIdOutputFormat` → `test_prompt_session_id_format.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`.
> This is a pure refactoring: move code only with `mcp__mcp-tools-py__move_symbol`, and edit only imports.
> Use MCP tools only. If any check below fails, write one line to `pr_info/.blocked.txt` and stop.
> Finish with the standard checks from the summary and produce exactly one commit.

## WHERE

- Source: `tests/cli/commands/test_prompt.py`
- Destination (new): `tests/cli/commands/test_prompt_session_id_format.py`

## WHAT

Move the class `TestSessionIdOutputFormat` (4 tests; covers the `output_format="session-id"` branch of
`execute_prompt`, which calls `prompt_llm`). There are no function signatures to add or change.

## HOW

1. **Baseline** (no marker filter for the `--collect-only` runs). Record the numbers in this file under "Notes":
   - `run_pytest_check(extra_args=["--collect-only", "-q", "tests/cli/commands/test_prompt.py"])` → expect 22
   - `run_pytest_check(extra_args=["--collect-only", "-q", "tests/cli/commands/"])` → expect 1039
   - `run_pytest_check(extra_args=["--collect-only", "-q"])` → expect 6463
   - `run_pytest_check(extra_args=["-q", "-n", "auto", "-m", "<fast-unit exclusion>", "tests/cli/commands/test_prompt.py"])` → expect 22 passed
   - If the actual counts differ from these, use the actual counts as the baseline for all later checks.
2. `list_symbols("tests/cli/commands/test_prompt.py")` must show `_make_text_events`,
   `TestSessionIdOutputFormat`, `TestExecutePrompt`, `TestPromptClaudeCwd` and `TestAddSystemPromptsFlag`.
   If it doesn't, write one line to `pr_info/.blocked.txt` and stop.
3. Dry run: `move_symbol(source_file="tests/cli/commands/test_prompt.py", symbol_names=["TestSessionIdOutputFormat"], dest_file="tests/cli/commands/test_prompt_session_id_format.py", dry_run=true)`.
   It must list only those two files. If it lists any other file, write one line to `pr_info/.blocked.txt` and stop.
4. Real call: the same arguments with `dry_run=false`. If it times out or reports `Token <…> cannot be matched`,
   write one line to `pr_info/.blocked.txt` and stop.
5. Fix imports only (the formatter decides the order).

## ALGORITHM

```
baseline = collect_counts()
dry = move_symbol(..., dry_run=True); assert dry.files == {source, dest}
move_symbol(..., dry_run=False)
fix_imports(source, dest)        # ruff F401 / expected end state below
run_format_code(); run_standard_checks(); assert counts match the expected values below
commit
```

## DATA — expected end state

- `test_prompt_session_id_format.py` imports: `argparse`, `logging`, `from typing import Any`,
  `from unittest.mock import Mock, patch`, `pytest`, `from mcp_coder.cli.commands.prompt import execute_prompt`.
  It must **not** import `_make_text_events`.
- `test_prompt.py`: `from typing import Any` removed. Everything else (docstring, `_make_text_events`,
  remaining classes) is unchanged.
- Collect counts (no marker filter): `test_prompt.py` **18**, `test_prompt_session_id_format.py` **4**,
  `tests/cli/commands/` **1039**, whole suite **6463**.
- The `.large-files-allowlist` entry stays (the base file is still ~917 lines).

## Verification

- Standard checks from the summary: all green.
- Run the two files with the fast-unit exclusion → 22 passed.
- Compact diff follows the summary's compact-diff rule.
- If any count or check deviates, write one line to `pr_info/.blocked.txt` and stop.

## Commit

`test(prompt): move session-id format tests to test_prompt_session_id_format.py`

## Notes

<!-- baseline numbers recorded here -->
