# Summary — Remove commit-clipboard, claude-code-sdk, and unused dependencies (#960)

## Goal

Delete obsolete / dead surface area and prune dependencies that `mcp_coder` no
longer imports directly. Four coupled cleanups delivered as a **single PR**:

1. Remove the `commit clipboard` CLI command.
2. Drop `pyperclip` (migrate icoder to Textual's native clipboard first).
3. Remove the dead Claude Python-SDK ("API") path and drop `claude-code-sdk`.
4. Remove four transitively-provided dependencies (`GitPython`, `PyGithub`,
   `structlog`, `python-json-logger`).

The work is almost entirely **deletion**. The only real constraint is that two
modules being deleted still host live code that must be **relocated first**.

## Architectural / design changes

- **`commit` command shrinks to a single mode (`auto`).** The `clipboard` mode,
  its parser, dispatch branch, help entry, and the two functions
  (`execute_commit_clipboard`, `get_commit_message_from_clipboard`) are removed.
- **Clipboard concern leaves the codebase.** `utils/clipboard.py` is deleted in
  full. icoder's Ctrl+C copy migrates from `pyperclip` (OS clipboard) to
  Textual's `App.copy_to_clipboard()` (OSC 52 terminal escape). Behavioural note:
  OSC 52 is terminal-dependent and differs from the OS-clipboard path — accepted
  for a TUI.
- **The Claude provider becomes CLI-only, in fact as well as in practice.** The
  SDK/`query`-based path (`claude_code_api.py`) was already dead in production
  (`interface.py` always routes to the CLI). It is removed. Two genuinely-live
  helpers are relocated out first:
  - `ClaudeAPIError` → **new module** `llm/providers/claude/errors.py` (its
    natural, well-named home; imported by `workflow_utils/commit_operations.py`).
  - `_verify_claude_before_use` → **folded into** its sole consumer
    `llm/providers/claude/claude_cli_verification.py` (removes a module boundary
    and an import edge — KISS over a shared module). It carries two dependencies
    (`setup_claude_path`, `verify_claude_installation`), so that module's imports
    gain `setup_claude_path`.
  - The two dead helpers `_extract_real_error_message` and `_retry_with_backoff`
    are **deleted** (no production callers), not relocated.
- **The dead formatter + serialization chain is removed.** The dual SDK/dict
  response handling existed only for the API path. `format_text_response`,
  `format_verbose_response`, `format_raw_response` and the whole
  `llm/formatting/sdk_serialization.py` module are deleted. `print_stream_event`
  (the live CLI streaming formatter) stays. `llm/formatting`'s public surface
  (`__all__`) shrinks accordingly — a deliberate public-API reduction.
- **Dependency graph narrows.** `claude-code-sdk`, `pyperclip` + `types-pyperclip`,
  `GitPython`, `PyGithub`, `structlog`, `python-json-logger` leave
  `pyproject.toml`. `black`/`isort` stay (invoked by mcp-tools-py runners via
  `sys.executable`). GitPython/PyGithub remain forbidden-from-direct-import via
  their isolation contracts (provided through `mcp-workspace`); structlog/
  json-logger come via `mcp-coder-utils` through the `log_utils` shim.
- **Import-linter contracts pruned.** `pyperclip_isolation`, `claude_sdk_isolation`,
  `structlog_isolation`, and `jsonlogger_isolation` are removed. The GitPython /
  PyGithub isolation contracts are **kept** (per the issue) as guards.

### Design decisions (resolved here, simplest option preserving requirements)

| Topic | Decision |
|-------|----------|
| `_verify_claude_before_use` home | **Fold** into `claude_cli_verification.py` (sole consumer) — not a shared module |
| `ClaudeAPIError` home | Tiny new `errors.py` (well-named; cross-layer consumer) |
| Dead helpers | Delete `_extract_real_error_message`, `_retry_with_backoff` |
| `sdk_serialization.py` + 3 `format_*` | Delete the whole chain (verified no callers) |
| Kept-test relocation | Copy keepers to new homes (Step 3); delete old SDK test files wholesale (Step 4) — no surgical line-editing of `test_claude_code_api_error_handling.py` |
| Sequencing | Relocate-before-delete; otherwise one verification pass per step |

## Implementation steps (one commit each)

| Step | Title | Independently green? |
|------|-------|----------------------|
| 1 | Remove the `commit clipboard` command | Yes |
| 2 | Migrate icoder to Textual clipboard, delete `clipboard.py`, drop `pyperclip` | Yes (after 1) |
| 3 | Relocate live helpers (`errors.py` + fold verify) and repoint importers/tests | Yes |
| 4 | Delete the Claude SDK/API path + formatter chain + `claude-code-sdk` | Yes (after 3) |
| 5 | Remove 4 unused transitive deps + regenerate dependency docs | Yes (after 2 & 4) |

**Ordering constraints:** 2 depends on 1 (clipboard helpers must be unused before
`clipboard.py` is deleted). 4 depends on 3 (live helpers must be relocated before
`claude_code_api.py` is deleted). 5 runs last so the regenerated dependency docs
reflect every removed package.

## Files created / modified / deleted

### Created
- `src/mcp_coder/llm/providers/claude/errors.py` — `ClaudeAPIError` (Step 3)
- `tests/llm/providers/claude/test_errors.py` — `ClaudeAPIError` tests (Step 3)

### Modified
- `src/mcp_coder/cli/parsers.py` — drop `clipboard` subparser (Step 1)
- `src/mcp_coder/cli/main.py` — drop clipboard import + dispatch branch (Step 1)
- `src/mcp_coder/cli/commands/commit.py` — delete clipboard functions + imports (Step 1)
- `src/mcp_coder/cli/commands/__init__.py` — drop `execute_commit_clipboard` export (Step 1)
- `src/mcp_coder/cli/commands/help.py` — drop `commit clipboard` entry (Step 1)
- `tests/cli/commands/test_commit.py` — drop clipboard import + `TestCommitClipboardPush` (Step 1)
- `tests/cli/test_parsers.py` — drop clipboard parser tests (Step 1)
- `docs/cli-reference.md` — drop `commit clipboard` section (Step 1)
- `docs/processes-prompts/development-process.md` — drop `commit clipboard` line (Step 1)
- `src/mcp_coder/icoder/ui/widgets/detail_modal.py` — Textual `copy_to_clipboard()` (Step 2)
- `tests/icoder/ui/test_detail_modal.py` — rewrite Ctrl+C copy test (Step 2)
- `src/mcp_coder/utils/__init__.py` — drop clipboard re-exports (Step 2)
- `src/mcp_coder/workflow_utils/commit_operations.py` — repoint `ClaudeAPIError` import (Step 3)
- `src/mcp_coder/llm/providers/claude/claude_cli_verification.py` — fold helper + add `setup_claude_path` (Step 3)
- `tests/llm/providers/claude/test_claude_cli_verification.py` — add `TestVerifyClaudeBeforeUse` (Step 3)
- `tests/workflow_utils/test_commit_operations.py` — repoint `ClaudeAPIError` import (Step 3)
- `src/mcp_coder/llm/formatting/formatters.py` — drop 3 `format_*` + sdk import (Step 4)
- `src/mcp_coder/llm/formatting/__init__.py` — shrink `__all__`/imports (Step 4)
- `tests/test_input_validation.py` — drop API-function params/import (Step 4)
- `tests/llm/providers/test_provider_structure.py` — drop `claude_code_api` asserts (Step 4)
- `tests/llm/providers/claude/test_claude_integration.py` — drop `"api"` fixture/import/TODOs (Step 4)
- `docs/architecture/architecture.md` — fix `sdk_serialization.py` + `clipboard.py` lines (Steps 4 & 2)
- `pyproject.toml` — remove deps + mypy override (Steps 2, 4, 5)
- `.importlinter` — remove 4 isolation contracts (Steps 2, 4, 5)
- `vulture_whitelist.py` — drop `_retry_with_backoff` entry (Step 4)
- `docs/architecture/dependencies/readme.md` — fix third-party contract count/list (Step 5)
- `docs/architecture/dependencies/*` — regenerate graph (Step 5)

### Deleted
- `src/mcp_coder/utils/clipboard.py` (Step 2)
- `tests/utils/test_clipboard.py` (Step 2)
- `src/mcp_coder/llm/providers/claude/claude_code_api.py` (Step 4)
- `src/mcp_coder/llm/formatting/sdk_serialization.py` (Step 4)
- `tests/llm/providers/claude/test_claude_code_api.py` (Step 4)
- `tests/llm/providers/claude/test_claude_code_api_error_handling.py` (Step 4)
- `tests/llm/formatting/test_sdk_serialization.py` (Step 4)
- `docs/providers/claude_sdk_response_structure.md` (Step 4)

## Verification (run at the end of every step)

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
mcp__tools-py__run_pytest_check  (extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_lint_imports_check
mcp__tools-py__run_vulture_check
```

Vulture is load-bearing here: this PR is mostly deletions, and it catches any
helper or import left dangling. Run the formatter (`isort`, `black`) before each
commit.
