# Step 1 — Move `mcp_manager.py` under `providers/langchain/`

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`).
> Implement ONLY step 1: move `src/mcp_coder/llm/mcp_manager.py` to
> `src/mcp_coder/llm/providers/langchain/mcp_manager.py` and update all 5
> import sites. Do NOT touch `pyproject.toml`, `.importlinter`, or docs —
> those are later steps. After the move, run pylint, pytest (fast unit
> subset), mypy, and `lint-imports`; all must pass. Commit with message:
> `refactor(llm): move mcp_manager under providers/langchain`.

## WHERE

**Source move:**
- `src/mcp_coder/llm/mcp_manager.py` → `src/mcp_coder/llm/providers/langchain/mcp_manager.py`

**Import sites to update (5 — auto-updated by `move_module` tool):**
- `src/mcp_coder/cli/commands/icoder.py:9`
- `src/mcp_coder/icoder/services/llm_service.py:11` (TYPE_CHECKING block)
- `src/mcp_coder/icoder/core/commands/info.py:21` (TYPE_CHECKING block)
- `tests/llm/test_mcp_manager.py:11`
- `tests/icoder/test_info_command.py:16`

**Test file location unchanged:** `tests/llm/test_mcp_manager.py` stays put;
only its import statement updates. No new test file required.

## WHAT

No signature changes. The module exports remain:

```python
class MCPServerStatus:      # frozen dataclass, unchanged
class MCPManager:           # unchanged public API: tools(), status(), close()
```

All code inside the moved file is kept identical.

## HOW

Use the refactoring tool:

```
mcp__tools-py__move_module(
    source_module="src/mcp_coder/llm/mcp_manager.py",
    dest_package="src/mcp_coder/llm/providers/langchain",
)
```

This automatically updates the 5 known import sites from
`mcp_coder.llm.mcp_manager` to `mcp_coder.llm.providers.langchain.mcp_manager`.

**Incidental cleanup (no extra code change needed):** the existing
module-top-level `from mcp_coder.llm.providers.langchain.agent import _sanitize_tool_schema`
is now an intra-package import — the pre-existing layering leak is resolved
by the move itself.

## ALGORITHM

```
1. Invoke move_module(src → dest)
2. Tool moves file and rewrites 5 import statements
3. Verify grep for "mcp_coder.llm.mcp_manager" returns only historical/doc mentions
4. Run lint-imports → green (langchain_library_isolation now implicitly covers
   the moved file's _sanitize_tool_schema import)
5. Run pylint + pytest (fast subset) + mypy → green
```

## DATA

No data/API changes. Sole invariant: after the move,
`from mcp_coder.llm.providers.langchain.mcp_manager import MCPManager, MCPServerStatus`
works from all 5 call sites, and the old path raises `ModuleNotFoundError`.

## Verification

- `mcp__tools-py__run_pytest_check` (fast unit subset, per CLAUDE.md)
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_mypy_check`
- `mcp__tools-py__run_lint_imports_check` — must still pass (no new contract
  yet; existing `langchain_library_isolation` continues to hold)

## Commit

```
refactor(llm): move mcp_manager under providers/langchain

mcp_manager is only instantiated on the langchain code path and already
imported _sanitize_tool_schema from providers.langchain.agent at module top
level. Moving it under providers/langchain/ resolves that layering leak
incidentally and positions the module for the langchain_transitive_isolation
contract added in a follow-up commit.

Refs #829
```
