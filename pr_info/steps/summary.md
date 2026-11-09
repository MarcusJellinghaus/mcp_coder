# Summary — #1196 Add the command toolkit and LLM access for it

Part of epic #1192. The issue body is the specification (Scope 1–13, Decisions,
Constraints, Done when). This plan implements it with the KISS simplifications
agreed in the discussion.

## Goal

A project on any stack (e.g. npm) configures its own `format` / `check` / `test`
commands in `[tool.mcp-coder.toolkit.command]` (in `pyproject.toml` or
`mcp-coder.toml`) and gets the same workflow behaviour as Python. Claude
sessions that re-run checks get exact `Bash(<argv joined by spaces>)` grants.

## Architectural / design changes

1. **New toolkit package `mcp_coder.toolkits.command`.** It is the first toolkit
   inside mcp-coder. It implements the `Toolkit` ABC from `mcp_coder.utils.toolkit`
   and is registered as entry point `command` in group `mcp_coder.toolkits`
   (new `[project.entry-points."mcp_coder.toolkits"]` table in `pyproject.toml`).
   Core reaches it **only through the registry**: an `.importlinter` contract
   forbids every core package from importing `mcp_coder.toolkits`. `tach.toml`
   gets a module entry (layer `tools`, depends on `mcp_coder.utils`).
   - Two modules: `config.py` (pure parsing + one problem list + grants) and
     `toolkit.py` (`CommandToolkit`: describe / verify / prompt_fragments / run,
     including the `exit-code` and `junit` parsers).
   - **One validator** (`parse_config`) feeds `describe`, `verify` and `run`, so
     they never disagree. Problems are tagged global or `(action, depth)`, and
     `error` or `warning`.
   - Fail closed: any global problem → no grants and every `run` returns
     `error`; a malformed step → its depth returns `error`.
2. **Claude provider grants.** `build_cli_command` gets `bash_grants`. With grants:
   `--tools ToolSearch,Bash --allowedTools <grant> <grant> …`; without grants the
   command is byte-for-byte unchanged. The parameter is threaded
   `prompt_llm` / `prompt_llm_stream` → `ask_claude_code_cli` /
   `ask_claude_code_cli_stream` → `build_cli_command`. Copilot / Langchain ignore it.
3. **One core permission function** in `utils/toolkit_runner.py`:
   `llm_permissions(project_dir, provider, entry=None)` — the loaded toolkit's
   `llm_permissions`, union over everything (`entry=None`) or the binding's
   requests at the resolved depth (`_resolve_depth`), with `Bash(` entries
   dropped for non-Claude providers (warning once per process, only when some
   were dropped) and `[]` + warning when the toolkit fails to load. Sessions
   keep only `Bash(` entries via `bash_grants_of(perms)`.
4. **Granted sessions** (each call site computes its own grants, nothing is
   threaded through configs): implement task, mypy fix call, finalisation,
   `_run_ci_fix`, rebase fix turns. All other sessions unchanged.
5. **Rebase.** `_run_all_checks` returns `(keys, fix_texts)`, refreshed on
   every re-check in the fix loop. The Rebase
   Regression Fix prompt gets toolkit-filled placeholders for the check-tool
   sentence and the shell ban, plus `[fix_text]`; it is rendered from
   `llm_permissions(project_dir, provider, entry)` — no toolkit-name switch, not
   from `REBASE_LLM_PERMISSIONS`. Grants are passed on fix turns only.
6. **`mcp-coder verify`.** Toolkit `verify("format")` runs only when formatting
   is on and the commit binding is non-empty; the mcp-tools-py Formatter row is
   shown only for the `mcp-tools-py` toolkit.

## Files created / modified

Created:
- `src/mcp_coder/toolkits/__init__.py`
- `src/mcp_coder/toolkits/command/__init__.py`
- `src/mcp_coder/toolkits/command/config.py`
- `src/mcp_coder/toolkits/command/toolkit.py`
- `tests/toolkits/__init__.py`, `tests/toolkits/command/__init__.py`
- `tests/toolkits/command/test_config.py`
- `tests/toolkits/command/test_toolkit_describe.py`
- `tests/toolkits/command/test_toolkit_run.py`
- `tests/toolkits/command/test_registration.py`
- `tests/llm/providers/claude/test_bash_grants_integration.py`
- `tests/utils/test_toolkit_permissions.py`
- `tests/workflows/rebase/test_command_toolkit_binding.py`
- `docs/configuration/command-toolkit.md`

Modified:
- `pyproject.toml` (entry-point table)
- `.importlinter` (toolkits isolation contracts; `tests.toolkits` in test independence)
- `tach.toml` (`mcp_coder.toolkits` module; `tests` depends_on)
- `vulture_whitelist.py` (`CommandToolkit` if vulture flags it)
- `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py`
- `src/mcp_coder/llm/interface.py`
- `src/mcp_coder/utils/toolkit_runner.py`
- `src/mcp_coder/workflows/implement/task_processing.py`
- `src/mcp_coder/workflows/implement/finalisation.py`
- `src/mcp_coder/workflow_steps/ci.py`
- `src/mcp_coder/workflows/rebase.py`
- `src/mcp_coder/workflows/rebase_checks.py`
- `src/mcp_coder/workflows/rebase_permissions.py` (docstring)
- `src/mcp_coder/prompts/prompts.md` (Rebase Regression Fix)
- `src/mcp_coder/cli/commands/verify_sections.py`
- `docs/README.md` (link to the new page)
- `tests/conftest.py` (`fake_npm` fixture: PATH launcher for npm-style test steps)
- tests next to each modified module (existing test files)

## Steps

1. Command toolkit config model (`config.py`).
2. `CommandToolkit.describe` and `run` with the `exit-code` and `junit` parsers.
3. `CommandToolkit.verify` / `prompt_fragments` + registration and import contracts.
4. Claude provider `bash_grants` parameter + probe integration test.
5. `llm_permissions` + granted implement / finalisation / CI-fix sessions.
6. Rebase checks: `_run_all_checks` returns `(keys, fix_texts)`; binding-level Done-when test.
7. Rebase prompt: toolkit-filled placeholders, `[fix_text]`, fix-turn grants.
8. `mcp-coder verify` gating (Scope 8a).
9. Docs page `docs/configuration/command-toolkit.md`.

## Conventions for every step

- TDD: write the tests first, then the code.
- Import through shims only: `mcp_coder.utils.toolkit`, `mcp_coder.utils.subprocess_runner`.
- Tests that use `CommandToolkit` through the registry must re-patch
  `mcp_coder.utils.toolkit_runner._toolkit_class` (the autouse
  `_resolvable_formatter` fixture returns `PythonToolkit`).
- Before committing: `run_format_code`, pylint, mypy, pytest (fast unit set with
  `-n auto`), `run_lint_imports_check`, `run_tach_check`, `run_ruff_check`.
