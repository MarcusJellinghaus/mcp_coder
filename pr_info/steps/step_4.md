# Step 4 — Delete the Claude SDK/API path, formatter chain, and `claude-code-sdk`

**Goal:** With the live helpers relocated (Step 3), delete the dead SDK/API path
end-to-end: `claude_code_api.py`, the `sdk_serialization.py` module, the three
unused `format_*_response` formatters, all their tests, the `claude-code-sdk`
dependency + contract, and the SDK docs. Surgically fix the three remaining test
files that import the deleted SDK functions at module level. One commit.

**Depends on Step 3.**

TDD note: this is wholesale deletion. The "test" work is removing dead test files
and trimming three test modules so collection passes; the kept formatter test
(`test_formatters.py`) already covers the surviving `print_stream_event`.

## WHERE

Deleted:
- `src/mcp_coder/llm/providers/claude/claude_code_api.py`
- `src/mcp_coder/llm/formatting/sdk_serialization.py`
- `tests/llm/providers/claude/test_claude_code_api.py`
- `tests/llm/providers/claude/test_claude_code_api_error_handling.py`
- `tests/llm/formatting/test_sdk_serialization.py`
- `docs/providers/claude_sdk_response_structure.md`

Modified:
- `src/mcp_coder/llm/formatting/formatters.py`
- `src/mcp_coder/llm/formatting/__init__.py`
- `tests/test_input_validation.py`
- `tests/llm/providers/test_provider_structure.py`
- `tests/llm/providers/claude/test_claude_integration.py`
- `pyproject.toml`
- `.importlinter`
- `vulture_whitelist.py`
- `docs/architecture/architecture.md`

## WHAT

### Source deletions / edits
- Delete `claude_code_api.py` and `sdk_serialization.py` entirely.
- `formatters.py`:
  - Remove functions `format_text_response`, `format_verbose_response`,
    `format_raw_response`.
  - Remove `from .sdk_serialization import extract_tool_interactions, serialize_message_for_json`.
  - Update module `__all__` to `["print_stream_event"]`.
  - Keep `print_stream_event`, `_normalize_event_to_ndjson`, and all imports they
    still use (`json`, `sys`, `StreamEvent`, the `render_actions` classes,
    `stream_renderer` helpers). Vulture will flag any import left unused — drop
    those if reported.
- `llm/formatting/__init__.py`:
  - From the `.formatters` import drop `format_raw_response`, `format_text_response`,
    `format_verbose_response` (keep `print_stream_event`).
  - Delete the whole `from .sdk_serialization import (...)` block.
  - Remove from `__all__`: `format_text_response`, `format_verbose_response`,
    `format_raw_response`, `is_sdk_message`, `get_message_role`,
    `get_message_tool_calls`, `serialize_message_for_json`,
    `extract_tool_interactions`. Keep `print_stream_event`, the renderer, and the
    render-action exports.

### Test edits (these break **collection**, not just runtime — required)
- `tests/test_input_validation.py`: delete the import
  ```python
  from mcp_coder.llm.providers.claude.claude_code_api import (
      ask_claude_code_api,
      ask_claude_code_api_detailed_sync,
  )
  ```
  and drop both API tuples from each of the four `@pytest.mark.parametrize`
  lists, keeping the `prompt_llm` and `ask_claude_code_cli` entries.
- `tests/llm/providers/test_provider_structure.py`:
  - `test_providers_package_structure`: drop `claude_code_api` from the
    `from ...claude import (...)` import and delete
    `assert hasattr(claude_code_api, "ask_claude_code_api")`. Keep the
    `claude_code_cli` import + assert.
  - `test_claude_provider_functions`: remove
    `from ...claude_code_api import ask_claude_code_api` and
    `assert callable(ask_claude_code_api)`. Keep the CLI / executable-finder lines.
- `tests/llm/providers/claude/test_claude_integration.py`: remove the
  `from ...claude_code_api import ask_claude_code_api` import (line ~19), delete
  the now-dead `method` (`params=["cli", "api"]`) and `ask_function` fixtures
  (lines ~28-39, unused by any test), drop the unused `Callable, Any` import if
  orphaned, and remove the stale "Removed Claude Code SDK imports" TODO comments.
  Leave the `@pytest.mark.claude_cli_integration` tests intact.

### Config / docs
- `pyproject.toml`: remove `"claude-code-sdk",` from `[project] dependencies`.
- `.importlinter`: remove the entire
  `[importlinter:contract:claude_sdk_isolation]` block.
- `vulture_whitelist.py`: remove lines 82-83 — the comment
  `# claude_code_api.py - Retry utility for future API retry logic` and the entry
  `_._retry_with_backoff`.
- Delete `docs/providers/claude_sdk_response_structure.md`.
- `docs/architecture/architecture.md`: remove/replace the line
  `- sdk_serialization.py - SDK message object handling (tests: llm/formatting/test_sdk_serialization.py)`.

## HOW (integration points)

- The CLI prompt path imports only `print_stream_event` from `llm.formatting`
  (`cli/commands/prompt.py`) — unaffected.
- `claude-code-sdk` was imported **only** by `claude_code_api.py`; once deleted,
  removing the dependency + contract is safe with no other code change.
- `test_claude_cli_verification.py` needs **no** change — its `@patch` targets the
  use-site module, which still defines `_verify_claude_before_use` (Step 3).

## ALGORITHM

None — deletion + import trimming only.

## DATA

`llm.formatting` public API shrinks to streaming-only
(`print_stream_event`, `StreamEventRenderer`, render-action dataclasses). No
runtime data structures change.

## VERIFY

Run formatter, then pylint / mypy / pytest (`-n auto` unit subset) / lint-imports
/ vulture. Confirm `git grep claude_code_api`, `git grep sdk_serialization`,
`git grep ask_claude_code_api`, `git grep claude_code_sdk`,
`git grep format_verbose_response` all return nothing. Vulture must report no new
dead code (watch for an orphaned import in `formatters.py`).

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement Step 4
> only: delete `claude_code_api.py`, `sdk_serialization.py`, and their test files
> (`test_claude_code_api.py`, `test_claude_code_api_error_handling.py`,
> `test_sdk_serialization.py`); remove the three `format_*_response` functions and
> the sdk import from `formatters.py`; shrink `llm/formatting/__init__.py`'s
> `__all__`/imports; surgically trim `tests/test_input_validation.py`,
> `tests/llm/providers/test_provider_structure.py`, and
> `tests/llm/providers/claude/test_claude_integration.py` to drop the deleted SDK
> symbols; remove `claude-code-sdk` from `pyproject.toml`, the
> `claude_sdk_isolation` contract from `.importlinter`, the `_retry_with_backoff`
> entry (lines 82-83) from `vulture_whitelist.py`; delete
> `docs/providers/claude_sdk_response_structure.md`; and fix the
> `sdk_serialization.py` line in `architecture.md`. Use MCP workspace tools. Run
> isort+black then `run_pylint_check`, `run_mypy_check`, `run_pytest_check`
> (unit subset `-n auto`), `run_lint_imports_check`, `run_vulture_check`. Fix until
> all pass, then one commit.
