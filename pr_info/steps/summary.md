# Summary — Enable ruff `F`, remove unused imports (#1169)

## Goal

Add `F` (pyflakes) to `[tool.ruff.lint] select` and clear every finding, with no
per-file-ignores and no `# noqa: F401` / `# noqa: F811` anywhere in `src` or `tests`.

Measured on this branch (`e6d559a`): **123 findings**. That is 110 `F401` (4 in `src`,
106 in `tests`) and 13 `F811` (all in `tests`). The issue said 118. The 5 extra come from
#1254: `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py` re-imports
`MagicMock` inside three functions while also importing it at module level.

## Architectural / design changes

This is mechanical cleanup. There is no new module, API or `__all__` design.

1. **`git_repo` fixture is discovered by conftest, not imported.**
   `git_repo` and `setup_git_config` move from `tests/utils/conftest.py` into root
   `tests/conftest.py`. Every test can then use the fixture through normal conftest
   discovery. The two `from tests.utils.conftest import git_repo` imports go away, and so do
   their `.importlinter` ignore entries. That resolves the TODO in the
   `test_module_independence` contract.
   `git_repo_with_files` (stays in `tests/utils/conftest.py`) now builds on the `git_repo`
   fixture instead of repeating the repository setup.
   `tests/workflows/rebase/conftest.py` keeps its own deliberate copy and is not touched.
2. **Optional-dependency checks without `noqa`.**
   - `src`: `import x` followed by `del x`. This keeps the real import, so the
     `builtins.__import__` patches and the `sys.modules` MagicMocks in tests keep working.
     Do not use `find_spec` or `importlib.import_module`.
   - `tests`: `pytest.importorskip("mlflow")` replaces the `try/except ImportError → skip`
     wrappers. A `hasattr` loop replaces the import-everything-in-a-`try` block.
   - `tests`: obsolete test-first guards around first-party imports
     (`try: import ... / except ImportError: X_MODULE_AVAILABLE = False` plus `skipif`)
     are deleted. The import becomes plain, or goes away if unused.
3. **Import smoke tests assert on what they import.** The import stays and is now "used".
4. **Lint policy.** ruff `F` owns unused-import detection. pylint `W0611` stays disabled,
   with an updated comment that explains why: pylint flags the `X as X` re-export
   convention that ruff accepts.
5. **One public-surface change:** `mcp_coder.llm.providers.langchain` no longer imports
   `LLMMCPLaunchError`. No caller uses that path; everything imports it from `._exceptions`.

## Steps (one commit each)

| Step | Commit | Content |
|---|---|---|
| 1 | `test: move git_repo fixture to root conftest` | fixture move, import + `.importlinter` cleanup |
| 2 | `test: remove unused imports in tests` | hand edits first, then `ruff --fix` sweep |
| 3 | `build(ruff): enable F (pyflakes)` | config, 4 dead `src` imports, 5 `del x` rewrites |

Order matters. Step 1 first keeps every commit green, because removing the `git_repo`
imports needs the fixture to be discoverable. Step 3 last means `F` is switched on only
when the code is already clean.

Within step 2, the hand edits come **before** the auto-fix. The new assertions make the
smoke-test imports "used", so `ruff --fix` only removes genuinely dead imports and
nothing has to be restored afterwards.

## Files modified

No files are created or deleted, apart from the `pr_info/steps/` plan files.

Step 1:
- `tests/conftest.py`: add `git_repo`, `setup_git_config`
- `tests/utils/conftest.py`: remove both, `git_repo_with_files` requests `git_repo`
- `tests/cli/commands/test_define_labels.py`: delete line 31 import
- `tests/workflows/test_create_pr_integration.py`: delete line 24 import
- `.importlinter`: delete lines 476-480

Step 2 (hand edits):
- `tests/llm/test_module_structure.py`
- `tests/llm/providers/test_provider_structure.py`
- `tests/test_mcp_workspace_git_smoke.py`
- `tests/test_mcp_workspace_github_smoke.py`
- `tests/test_module_exports.py`
- `tests/test_module_integration.py`
- `tests/integration/test_mlflow_integration.py`
- `tests/workflows/vscodeclaude/test_launch_vscode_env_vars.py`
- `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py`
- `tests/cli/commands/test_check_branch_status.py`
- `tests/cli/commands/test_check_branch_status_auto_fixes.py`
- `tests/cli/commands/test_check_branch_status_ci_waiting.py`
- `tests/cli/commands/test_check_branch_status_cli_integration.py`
- `tests/cli/commands/test_check_branch_status_pr_waiting.py`
- any further test file with the same first-party guard pattern (found by the A4 sweep)

Step 2 (`ruff --fix` sweep): about 60 further test files under `tests/`, with import lines
removed only.

Step 3:
- `pyproject.toml`: `select` gets `"F"`; comments at lines 208 and 328
- `src/mcp_coder/cli/commands/coordinator/core.py`: line 10 `Optional`
- `src/mcp_coder/workflows/create_pr/helpers.py`: line 10 `Optional`
- `src/mcp_coder/llm/storage/session_finder.py`: line 12 `Path`
- `src/mcp_coder/llm/providers/langchain/__init__.py`: line 28 `LLMMCPLaunchError`
- `src/mcp_coder/llm/mlflow_logger.py`: line 48
- `src/mcp_coder/llm/providers/langchain/agent.py`: lines 49, 53
- `src/mcp_coder/llm/providers/langchain/_exceptions.py`: line 237
- `src/mcp_coder/llm/providers/langchain/_preflight.py`: line 28

## Out of scope

- `F821` noqa in `_http.py` and `F841` noqa in `tests/conftest.py`.
- The 4 `X as X` re-exports that pylint would flag.
- Enabling pylint `W0611`.
- Propagation to `mcp-tools-py` / `mcp-workspace`.

## Checks for every step

Run these through the MCP tools:
- `run_format_code`
- `run_ruff_check`
- `run_pylint_check`
- `run_mypy_check`
- `run_lint_imports_check`
- pytest unit run with `-n auto` and the marker exclusion list from `.claude/CLAUDE.md`
- pytest with `markers=["git_integration"]`
