# Step 5 — Move dispatch classes → `test_core_dispatch.py`; final verification

## LLM prompt

> Read `pr_info/steps/summary.md`, then do `pr_info/steps/step_5.md`. This is a pure refactor:
> move both classes in one `mcp__mcp-tools-py__move_symbol` call (dry run first). Edit only
> imports, the last stale docstring bullet and the allowlist entry. Run the full verification
> list. The step ends in exactly one commit.

## WHERE

- Source: `tests/cli/commands/coordinator/test_core.py`
- Destination (**new**): `tests/cli/commands/coordinator/test_core_dispatch.py`
- `.large-files-allowlist`, if the entry is still there

## WHAT

Move these classes in one call, in source order (18 tests in total):

| Class | Tests |
|---|---:|
| `TestDispatchWorkflow` | 4 |
| `TestDispatchWorkflowSilentFallthroughGuard` | 14 |

The guard class has 14 tests from two `parametrize` stacks: `WORKFLOW_MAPPING` × `executor_os`.
It also has a `@staticmethod _make_issue`.

## HOW

1. **Pre-counts:** run `--collect-only -q` on each path below and note the numbers.

   | Path | Expected |
   |---|---:|
   | `test_core.py` | 32 |
   | `test_core.py::TestDispatchWorkflowSilentFallthroughGuard` | 14 |
   | whole suite | — |

2. **Dry run:**
   - Call `move_symbol(..., symbol_names=["TestDispatchWorkflow",
     "TestDispatchWorkflowSilentFallthroughGuard"],
     dest_file="tests/cli/commands/coordinator/test_core_dispatch.py", dry_run=True)`.
   - If it lists files other than the source and the destination: write one line to
     `pr_info/.blocked.txt` and stop.
3. **Move:** run the same call without `dry_run`.
4. **Check the decorators:** both `parametrize` decorators must be unchanged. If they changed:
   write one line to `pr_info/.blocked.txt` and stop.
5. **Destination imports**, exactly. All of them are module-level, so `WORKFLOW_MAPPING` is
   imported above the class whose decorator reads it.
   ```python
   import logging
   from unittest.mock import MagicMock, patch

   import pytest

   from mcp_coder.cli.commands.coordinator import WORKFLOW_MAPPING, dispatch_workflow
   from mcp_coder.mcp_workspace_github import IssueData
   from tests.github_factories import make_issue_data
   ```
   - No `RepoIdentifier`: it is only patched by a string target.
   - If the tool imported from `coordinator.core` or `coordinator.workflow_constants`, rewrite
     the import to the package.
6. **`test_core.py` final state:**
   - Module docstring:
     ```text
     """Tests for coordinator core.py functions.

     This module contains tests for:
     - Configuration management functions (load_repo_config, validate_repo_config, get_jenkins_credentials)
     """
     ```
     Delete only the bullet `- Workflow dispatch function (dispatch_workflow)`.
   - Imports:
     ```python
     from unittest.mock import MagicMock, patch

     import pytest

     from mcp_coder.cli.commands.coordinator import (
         get_jenkins_credentials,
         load_repo_config,
         validate_repo_config,
     )
     ```
   - Remaining classes: `TestLoadRepoConfig`, `TestValidateRepoConfig`,
     `TestGetJenkinsCredentials`.
7. **Allowlist:** if `.large-files-allowlist` still lists
   `tests/cli/commands/coordinator/test_core.py`, remove that line.

## ALGORITHM

```
record counts -> dry-run -> move 2 classes in one call
verify parametrize decorators unchanged
set destination imports; reduce test_core.py imports/docstring to final state
ensure allowlist entry removed
full verification list
```

## DATA — expected collect counts after the step

| Path | Expected |
|---|---:|
| `test_core.py` | 14 |
| `test_core_eligibility.py` | 5 |
| `test_core_dispatch.py` | 18 |
| `test_core_dispatch.py::TestDispatchWorkflowSilentFallthroughGuard` | 14 |
| `test_command_templates.py` | 32 |
| `tests/utils/test_user_config_cache_refresh.py` | 4 |
| `tests/utils/test_user_config.py` | 27 |
| `tests/test_mcp_workspace_github_cache.py` | 8 |
| `tests/test_mcp_workspace_github_smoke.py` | 5 |
| `tests/cli/commands/coordinator/` | step-1 baseline − 12 |
| `tests/utils/` | step-1 baseline + 4 |
| whole suite | step-1 baseline |

Run these tests at their new locations → 13 passed:
- `tests/utils/test_user_config_cache_refresh.py`
- `tests/test_mcp_workspace_github_cache.py`
- `tests/cli/commands/coordinator/test_command_templates.py::TestCommandTemplates`

If any count is off, or a test fails: write one line to `pr_info/.blocked.txt` and stop.

## Checks (full verification)

- `run_format_code`
- `run_ruff_check`: no `F401` / `F811` / `F821`
- `run_pylint_check`
- `run_mypy_check`
- fast unit `run_pytest_check` with `-n auto`
- `run_lint_imports_check`
- `run_tach_check`
- `run_vulture_check`
- `check_file_size`: passes, all files are under 750 lines, and no stale allowlist entries
- `mcp__mcp-workspace__git` diff with `compact=true` against the base branch. It may show only:
  - moved blocks
  - import changes
  - new-file headers
  - the six deleted docstring bullets
  - the allowlist line
  - blank-line hunks

## Commit

`test(coordinator): split dispatch tests into test_core_dispatch.py`
