# Step 1 — Re-export `verify_git` from the shim

> **Reference:** [`pr_info/steps/summary.md`](./summary.md) — Architecture & file overview.

## Goal

Make `verify_git` importable through the local shim (`mcp_coder.mcp_workspace_git`) so the CLI orchestrator (step 2) can use it. Mirrors the existing `verify_github` re-export in `mcp_workspace_github.py`.

## WHERE

| File | Change |
|---|---|
| `src/mcp_coder/mcp_workspace_git.py` | Add one import line + one `__all__` entry |
| `tests/test_mcp_workspace_git_smoke.py` | Bump `len(__all__) == 28` → `29` |

## WHAT

In `src/mcp_coder/mcp_workspace_git.py`, add:

```python
from mcp_workspace.git_operations.verification import verify_git
```

Add `"verify_git"` to the `__all__` list (alphabetical position is fine; the existing list has no strict ordering — append after `"detect_parent_branch_via_merge_base"` for minimal diff).

## HOW

- Imports use the exact upstream path `mcp_workspace.git_operations.verification` (same pattern as the other category-grouped imports in this file).
- Group the new import under a `# Verification` comment block to match the file's "category comments" style.
- Do **not** add any `@log_function_call` decorator or wrapping function — re-export only (Decision #11).

## ALGORITHM

N/A — pure re-export.

## DATA

`verify_git` is `(project_dir: Path, *, actually_sign: bool = False) -> CheckResult` upstream. The shim does not alter the signature.

## TDD Order

1. Edit `tests/test_mcp_workspace_git_smoke.py`: change `assert len(__all__) == 28` → `29`.
2. Run pytest for that file → **fails** (length is still 28).
3. Edit `src/mcp_coder/mcp_workspace_git.py`: add the import + `__all__` entry.
4. Run pytest for that file → **passes**.
5. Run all three quality checks (pylint, pytest, mypy).

## Acceptance

- `from mcp_coder.mcp_workspace_git import verify_git` succeeds.
- `tests/test_mcp_workspace_git_smoke.py` passes.
- pylint, pytest, mypy all green.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement Step 1 exactly as specified:

1. Edit tests/test_mcp_workspace_git_smoke.py: change the assertion
   `assert len(__all__) == 28` to `assert len(__all__) == 29`.
2. Run mcp__tools-py__run_pytest_check on tests/test_mcp_workspace_git_smoke.py
   and confirm it fails.
3. Edit src/mcp_coder/mcp_workspace_git.py:
   - Add `from mcp_workspace.git_operations.verification import verify_git`
     in a "# Verification" comment block (mirror the file's existing category style).
   - Add "verify_git" to the __all__ list.
4. Run all three quality checks per .claude/CLAUDE.md:
   - mcp__tools-py__run_pylint_check
   - mcp__tools-py__run_pytest_check with extra_args=["-n", "auto",
     "-m", "not git_integration and not claude_cli_integration and not
     claude_api_integration and not formatter_integration and not
     github_integration and not langchain_integration"]
   - mcp__tools-py__run_mypy_check
5. Run ./tools/format_all.sh before committing.
6. Commit with a clear message such as:
   "Re-export verify_git from mcp_workspace_git shim (#937)"

Do NOT modify verify.py, the orchestrator, or any other file in this step.
Do NOT add logging, wrapping functions, or anything beyond the import + __all__ entry.
```
