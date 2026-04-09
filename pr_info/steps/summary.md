# Summary: Split implement/core.py (#310)

## Goal

Reduce `src/mcp_coder/workflows/implement/core.py` from 1,369 lines to ~803 lines by extracting CI operations into a sibling module and moving an inline prompt to `prompts.md`.

## Architectural / Design Changes

- **New module**: `src/mcp_coder/workflows/implement/ci_operations.py` — contains all CI-related functions (~550 lines): polling, analysis, fix attempts, and the orchestrating `check_and_fix_ci` entry point.
- **Prompt externalisation**: `FINALISATION_PROMPT` moves from an inline f-string constant to `src/mcp_coder/prompts/prompts.md`, loaded at runtime via `get_prompt_with_substitutions`.
- **No logic changes**: Functions are moved as-is. Only import paths and the prompt loading mechanism change.
- **No architecture contract changes**: `ci_operations.py` is a sibling of `core.py` inside `workflows.implement`. No cross-layer dependencies are introduced.

## Files Created

| File | Purpose |
|------|---------|
| `src/mcp_coder/workflows/implement/ci_operations.py` | CI check/fix operations extracted from core.py |
| `tests/workflows/implement/test_ci_operations.py` | Tests for CI operations (moved from test_core.py) |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/implement/core.py` | Remove CI functions + FINALISATION_PROMPT, add import of `check_and_fix_ci` from ci_operations |
| `src/mcp_coder/prompts/prompts.md` | Add Finalisation Prompt section |
| `tests/workflows/implement/test_core.py` | Remove CI test classes, update remaining imports |
| `src/mcp_coder/workflows/implement/__init__.py` | No change expected (check_and_fix_ci not in exports) |
| `.large-files-allowlist` | No change expected (core.py stays on list at ~803 lines) |
| `.importlinter` | No change expected (no new cross-layer imports) |

## Constraints

- **Move, don't change**: No logic modifications — verified via compact-diff.
- **Prompt fidelity**: The FINALISATION_PROMPT is reproduced exactly (including the doubled `pr_info/pr_info/` path in the commit message line — existing behavior preserved).
- **Each step = one commit** for reviewability.
