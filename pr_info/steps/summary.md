# Summary — Split large file `tests/cli/commands/test_prompt.py` (#1327)

Part of #353. Process: `docs/processes-prompts/refactoring-guide.md`.

## Goal

`tests/cli/commands/test_prompt.py` (1092 lines, allowlisted) is split into the base file plus three
prefixed sibling test files, one per `execute_prompt` concern. The base file ends at ~581 lines and
leaves `.large-files-allowlist`.

## Pure refactoring rules (apply to every step)

- **Move, don't change.** Classes and functions move verbatim: no logic edits, no renames, no reformatting
  beyond the formatter, no test deletions or merges.
- **Only allowed edits:** import statements, and removing the `.large-files-allowlist` entry.
  No `pytestmark` is added (the original file has none), and no module docstrings are added to the new
  test files (`D` is ignored for `tests/**`).
- **Use the refactoring tools:** `mcp__mcp-tools-py__move_symbol` (dry run first, then the real call),
  `list_symbols`, `find_references`. Never move code by hand.
- **MCP tools only, no Bash** (except the approved git commit commands).
- **No re-exports or stubs.** Siblings import **only** `_make_text_events` from `test_prompt.py`.
  They never import a `Test*` class, because pytest would then collect it twice.
- If a precondition or check fails, write one line to `pr_info/.blocked.txt` and stop.
- If a test that passed at baseline fails at its new location, do not fix it by adding fixtures,
  `conftest.py` entries or patches. Write one line to `pr_info/.blocked.txt` and stop.

## Architectural / design changes

- **Production code:** none. `src/mcp_coder/cli/commands/prompt.py` (one function, `execute_prompt`) is
  untouched.
- **Test layout:** a single module maps to prefixed siblings `test_prompt_<concern>.py` in the same
  directory, next to the existing `test_prompt_streaming.py`. The conftest chain
  (`tests/conftest.py` + `tests/cli/commands/conftest.py`, including its autouse fixtures) is identical
  for all files.
- **Shared helper:** `_make_text_events` stays in `test_prompt.py`, because its caller
  `TestExecutePrompt` stays there. `test_prompt_claude_cwd.py` and `test_prompt_system_prompts.py` import
  it with `from tests.cli.commands.test_prompt import _make_text_events`. This follows the existing
  precedent `tests/llm/providers/langchain/test_langchain_agent_streaming_tool_output.py:5`.
- **No `@patch` target changes:** every patch target is in `mcp_coder.cli.commands.prompt.*`,
  `builtins.open`, `os.path.exists` or `mcp_coder.llm.providers.langchain._load_langchain_config`.

## Target layout

| File | Contents | Tests | ~lines |
|---|---|---:|---:|
| `tests/cli/commands/test_prompt.py` (modified) | `_make_text_events`, `TestExecutePrompt` (core path, `--continue-session-from`, env vars) | 10 | ~581 |
| `tests/cli/commands/test_prompt_session_id_format.py` (new) | `TestSessionIdOutputFormat` | 4 | ~185 |
| `tests/cli/commands/test_prompt_claude_cwd.py` (new) | `TestPromptClaudeCwd` | 3 | ~145 |
| `tests/cli/commands/test_prompt_system_prompts.py` (new) | `TestAddSystemPromptsFlag` | 5 | ~215 |
| `tests/cli/commands/test_prompt_streaming.py` (existing) | unchanged | — | 455 |

Total: 22 tests before and after. Baseline counts (2026-10-26): `tests/cli/commands/` = **1039**,
whole suite = **6463**.

## Files created / modified

- **Created:** `tests/cli/commands/test_prompt_session_id_format.py`,
  `tests/cli/commands/test_prompt_claude_cwd.py`, `tests/cli/commands/test_prompt_system_prompts.py`
- **Modified:** `tests/cli/commands/test_prompt.py` (classes moved out; `from typing import Any` removed),
  `.large-files-allowlist` (entry `tests/cli/commands/test_prompt.py` removed, in step 3)
- **Not touched:** `src/`, `tests/cli/commands/conftest.py`, `tests/cli/commands/test_prompt_streaming.py`,
  `docs/architecture/architecture.md` (its reference to `cli/commands/test_prompt.py` stays true),
  `vulture_whitelist.py`

## Steps (one commit each)

1. `step_1.md`: record the baseline, then move `TestSessionIdOutputFormat` → `test_prompt_session_id_format.py`
2. `step_2.md`: move `TestPromptClaudeCwd` → `test_prompt_claude_cwd.py`
3. `step_3.md`: move `TestAddSystemPromptsFlag` → `test_prompt_system_prompts.py`, then remove the
   allowlist entry (the base file is now under the limit, so the entry would be stale)

TDD note: this is a test-only refactoring. The moved tests are the deliverable. The "test" in each step
is that the moved tests are collected and pass, with unchanged counts.

## Shared definitions

**Fast-unit exclusion** (the `-m` value used in every step):

```
not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration
```

**Standard checks** (end of every step, all MCP tools):
`run_format_code` → `run_ruff_check` → `run_pylint_check` → `run_mypy_check` →
`run_pytest_check(extra_args=["-n", "auto", "-m", "<fast-unit exclusion>"])` →
`run_lint_imports_check` → `run_tach_check` → `run_vulture_check` → `check_file_size`.

**Compact-diff rule:** `mcp__mcp-workspace__git(command="diff", compact=true)` may show only these:
moved blocks, import-line changes, new-file import headers, blank-line-only hunks, and (in step 3) the
one allowlist line. No hunk may touch a test body, `_make_text_events`, `TestExecutePrompt` or the module
docstring.
