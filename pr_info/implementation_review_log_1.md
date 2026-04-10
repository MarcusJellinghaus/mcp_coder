# Implementation Review Log — Issue #748

**MCP Server Connection Status at Startup + Verify**

## Round 1 — 2026-04-10

**Findings:**
- F1 (Critical): Layered architecture violation — `utils/mcp_verification.py` imports from `llm` layer (`find_claude_executable`). lint-imports fails.
- F2 (Accept): Redundant `elif mcp_result is None:` in `verify.py` line ~412 — logically equivalent to `else:`.
- F3 (Skip): Conditional imports in `verify.py` for langchain — pre-existing, out of scope.
- F4 (Skip): Long line in `on_mount()` generator — cosmetic, code works fine.
- F5 (Skip): Linear search in `_connection_status_suffix` — only 2 servers, irrelevant.
- F6 (Accept): `ClaudeMCPStatus` imported inside test method bodies instead of at file top in `test_verify_command.py` and `test_verify_orchestration.py`.

**Decisions:**
- F1: Accept — refactor to dependency injection (`claude_executable: str | None` parameter). Callers resolve the executable.
- F2: Accept — change to `else:`.
- F3: Skip — pre-existing.
- F4: Skip — cosmetic.
- F5: Skip — trivial scale.
- F6: Accept — Boy Scout cleanup, move to top-level imports.

**Changes:**
- `src/mcp_coder/utils/mcp_verification.py`: Removed `llm` import, added `claude_executable` parameter to `parse_claude_mcp_list()`
- `src/mcp_coder/cli/commands/verify.py`: Caller resolves claude executable, passes it in. Changed `elif` to `else`.
- `src/mcp_coder/icoder/env_setup.py`: Caller resolves claude executable, passes it in.
- `tests/utils/test_mcp_verification.py`: Updated tests to pass `claude_executable` directly instead of monkeypatching.
- `tests/icoder/test_env_setup.py`: Updated lambda mocks for new parameter.
- `tests/cli/commands/test_verify_command.py`: Moved `ClaudeMCPStatus` import to top-level.
- `tests/cli/commands/test_verify_orchestration.py`: Moved `ClaudeMCPStatus` import to top-level.

**Status:** All 5 quality checks + ruff pass. Ready to commit.
