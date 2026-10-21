# Step 2 — Remove unused imports in `tests/`

**Commit:** `test: remove unused imports in tests`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> Make the hand edits in section A **first**, then run the ruff auto-fix sweep in
> section B, then review the diff. Do not add any `# noqa` and do not change
> `pyproject.toml`. Run all checks listed in the summary, then make one commit.

## WHERE / WHAT / HOW

### A. Hand edits (before the auto-fix)

**A1 — Import smoke tests: keep the import, assert on it.**
- `tests/llm/test_module_structure.py`
  - `test_llm_package_structure`: after the imports, add
    `assert mcp_coder.llm.interface`, `assert mcp_coder.llm.serialization` and
    `assert mcp_coder.llm.types`.
  - `test_public_api_exports`: add `assert LLMResponseDict`.
- `tests/llm/providers/test_provider_structure.py`
  - `test_providers_package_structure`: add `assert mcp_coder.llm.providers` and
    `assert mcp_coder.llm.providers.claude`.
  - Line 51: delete the `# noqa: F401` comment only. `langchain` is used on the next line.
- `tests/test_mcp_workspace_git_smoke.py`
  - Line 6: drop `# noqa: F401`, add `assert mcp_coder.mcp_workspace_git`.
  - `test_key_symbols_accessible`: add `assert <name>` for each imported name that is not
    yet asserted (`get_current_branch_name`, `get_full_status`, `git_push`).
- `tests/test_mcp_workspace_github_smoke.py`
  - Line 6: drop `# noqa: F401`, add `assert mcp_coder.mcp_workspace_github`.
  - If `ruff check --select F401` on this file still reports names, assert on those too,
    in the same way.

**A2 — `try/except ImportError` sites (ruff's fix does not touch these).**
- `tests/test_module_exports.py::test_no_import_errors` (lines 147-164): replace the body
  with the code below and drop the `try/except → pytest.fail`.
  ```python
  import mcp_coder

  for name in (
      "LLM_RESPONSE_VERSION", "LLMResponseDict", "collect_branch_status",
      "deserialize_llm_response", "generate_commit_message_with_llm", "prompt_llm",
      "serialize_llm_response", "verify_claude", "verify_langchain", "verify_mlflow",
  ):
      assert hasattr(mcp_coder, name), name
  ```
- `tests/test_module_integration.py:160`: delete `import mcp_coder.utils`. It is already
  loaded transitively. Nothing else in that test changes.
- `tests/integration/test_mlflow_integration.py`, in `test_real_mlflow_available` (line 211)
  and `test_sqlite_backend_with_tilde_expansion` (line 233):
  - Replace `try: import mlflow` with a first statement `pytest.importorskip("mlflow")`.
  - Dedent the former `try` body one level.
  - Delete the `except ImportError: pytest.skip(...)` block.

  Removing only the import is not enough: the wrapper would then catch unrelated
  ImportErrors.

**A3 — Function-local re-imports shadowing module imports (`F811`).**
- `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py`: delete the
  local `from unittest.mock import MagicMock` at lines 103, 221 and 458. Keep line 6.
- `tests/workflows/vscodeclaude/test_launch_vscode_env_vars.py`: delete the local
  `from pathlib import Path` / `from unittest.mock import MagicMock` at lines 40-41. The
  module-level `MagicMock` (line 9) is then unused, and B removes it.

**A4 — Obsolete test-first import guards (ruff's fix does not touch these).**

These files guard a first-party import with a test-first block, written before the module
existed:

```python
try:
    from mcp_coder.cli.commands.<module> import execute_<command>

    <MODULE>_MODULE_AVAILABLE = True
except ImportError:          # test_create_pr.py: `except Exception` + traceback print
    <MODULE>_MODULE_AVAILABLE = False

    execute_<command> = unavailable_command_stub   # only in some files
```

| File | Flag | Stub fallback |
|---|---|---|
| `tests/cli/commands/test_check_branch_status.py` | `CHECK_BRANCH_STATUS_MODULE_AVAILABLE` | yes |
| `tests/cli/commands/test_check_branch_status_auto_fixes.py` | `CHECK_BRANCH_STATUS_MODULE_AVAILABLE` | no |
| `tests/cli/commands/test_check_branch_status_ci_waiting.py` | `CHECK_BRANCH_STATUS_MODULE_AVAILABLE` | no |
| `tests/cli/commands/test_check_branch_status_cli_integration.py` | `CHECK_BRANCH_STATUS_MODULE_AVAILABLE` | no |
| `tests/cli/commands/test_check_branch_status_pr_waiting.py` | `CHECK_BRANCH_STATUS_MODULE_AVAILABLE` | no |
| `tests/cli/commands/test_implement.py` | `IMPLEMENT_MODULE_AVAILABLE` | yes |
| `tests/cli/commands/test_create_pr.py` | `CREATE_PR_MODULE_AVAILABLE` | yes |

In each file:
- Delete the `# Test-first approach ...` comment, the whole `try/except` block (including
  the stub assignment and, in `test_create_pr.py`, the traceback print) and the flag.
- Delete every `@pytest.mark.skipif(not <MODULE>_MODULE_AVAILABLE, ...)` decorator
  (class- and function-level).
- If any test in the file calls the command function through the module-level name
  (not through a function-local import), keep a plain top-level
  `from mcp_coder.cli.commands.<module> import execute_<command>`.
  Otherwise drop the import entirely.
- Delete `from tests.cli.commands.conftest import unavailable_command_stub`.
- If `pytest` becomes unused after the `skipif` removal, B removes it.

Then delete the now-dead stub helper:
- `tests/cli/commands/conftest.py`: delete `unavailable_command_stub` (lines 18-20).
  `argparse` stays: `_make_args` uses it.
- `tests/cli/commands/test_conftest_helpers.py`: delete the file. Its only test covers the
  stub.

Finally, confirm nothing is left:
`search_files(glob="tests/**/*.py", pattern="_MODULE_AVAILABLE|unavailable_command_stub")`
must find nothing. The remaining `except ImportError` sites in `tests/` are out of A4's
scope: A2 covers `test_module_exports.py`, `test_module_integration.py` and the mlflow
file. The `httpx` / `anthropic` guards in the langchain tests (optional packages, used)
and the `typing` / `typing_extensions` `TypedDict` fallback in `tests/conftest.py` are
not F401 findings and stay.

### B. Auto-fix sweep

`run_ruff_fix(select=["F401"], target_directories=["tests"])`

Review the diff with `git diff`. Each removed import must be truly dead. If one was kept
for a side effect (registration, monkeypatch target, plugin load), restore it as a
used-form statement (for example `assert module`), not a `noqa`.

## ALGORITHM

```
apply A1, A2, A3, A4 by hand
run_ruff_fix(select=["F401"], target_directories=["tests"])
git diff -> inspect every removed import
run_ruff_check(select=["F401","F811"], target_directories=["tests"]) -> must be 0
run format, pylint, mypy, pytest (unit + git_integration)
```

## DATA

No runtime data changes. Each touched test keeps the same pass/skip behaviour. The mlflow
tests skip via `importorskip` instead of `pytest.skip`. The `check_branch_status`,
`implement` and `create_pr` tests lose their `skipif`: a broken import now fails collection instead of skipping silently.

## Postcondition

`run_ruff_check(select=["F401", "F811"], target_directories=["tests"])` must report 0
issues, and `search_files(glob="tests/**/*.py", pattern="noqa: F(401|811)")` must find
nothing. If either still reports something that needs a design decision beyond this step,
write one line to `pr_info/.blocked.txt` and stop.

## Tests (TDD)

This step only edits tests. The existing tests are the specification. The unit run and
`git_integration` must pass. The mlflow tests are marked `mlflow_integration`; run
`extra_args=["tests/integration/test_mlflow_integration.py"]` once to confirm they pass or
skip cleanly.
