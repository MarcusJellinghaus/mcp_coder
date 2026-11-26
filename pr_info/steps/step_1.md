# Step 1: pass HEAD as `expected_sha` at implement step 5.6

Context: read [summary.md](./summary.md) first.

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`.
> Use TDD. First add the autouse stub to `tests/workflows/implement/conftest.py` and the
> parametrized test to `tests/workflows/implement/test_core.py`, and confirm the test fails.
> Then change the step 5.6 call in `src/mcp_coder/workflows/implement/core.py`.
> Only touch the three files this step names. Run format code, pylint, mypy
> and the fast pytest set (`-n auto`), and make all of them pass. The result is
> one commit.

## Precondition

`src/mcp_coder/workflows/implement/core.py` has a step 5.6 block that calls
`check_and_fix_ci(` inside `if current_branch:`. If that call or that block is
missing, write one line to `pr_info/.blocked.txt` and stop.

## 1. Autouse stub (test infrastructure)

**WHERE:** `tests/workflows/implement/conftest.py`, next to `_stub_branch_head`.

**WHAT:**

```python
@pytest.fixture(autouse=True)
def _stub_head_sha() -> Iterator[None]:
    """Keep implement's step 5.6 HEAD read away from real git."""
    with patch(
        "mcp_coder.workflows.implement.core.get_latest_commit_sha",
        return_value=None,
    ):
        yield
```

**DATA:** Returning `None` keeps existing tests at today's call shape
(`expected_sha=None`). A test's own `@patch` on the same target is applied
inside the fixture's patch, so it overrides the stub.

## 2. Test (write first, must fail before step 3)

**WHERE:** `tests/workflows/implement/test_core.py`, class `TestRunImplementWorkflow`.

**WHAT:** `test_ci_check_receives_head_sha_as_expected_sha(self, ..., sha: str | None)`,
decorated with `@pytest.mark.parametrize("sha", ["PUSHEDSHA", None])`.
Import `pytest` at the top of the file.

**HOW:** Reuse the patch stack of `test_run_implement_workflow_success` in the same
file: `check_and_fix_ci`, `run_finalisation`, `get_full_status`, `run_formatters`,
`check_and_fix`, `prepare_llm_environment`, `get_current_branch_name` (a branch name),
`process_task_with_retry`, `log_progress_summary`, `prepare_task_tracker`,
`check_prerequisites`, `check_main_branch` and `check_git_clean`. Copy that stack
as it is, with no other patches. Add `@patch("mcp_coder.workflows.implement.core.get_latest_commit_sha")` and set
its `return_value = sha`. Match the existing test's style:
patch-decorators first, then the `parametrize` decorator outermost.

**ALGORITHM:**

```
set the prerequisite mocks to True; process_task_with_retry -> TaskOutcome(False, "no_tasks")
mock_sha.return_value = sha
result = run_implement_workflow(Path("/test/project"), "claude")
assert result == 0
mock_check_ci.assert_called_once()
assert mock_check_ci.call_args.kwargs["expected_sha"] == sha
```

Docstring: "Step 5.6 passes local HEAD as expected_sha; None when HEAD is unknown."

## 3. Implementation

**WHERE:** `src/mcp_coder/workflows/implement/core.py`.

**HOW:**

- Import: `from mcp_coder.mcp_workspace_git import (get_current_branch_name, get_full_status, get_latest_commit_sha)`.
- In the step 5.6 `check_and_fix_ci(...)` call, add one keyword argument after
  `settings_file=settings_file,`:

```python
                    # Wait for the run of the commit just pushed, not the newest run.
                    expected_sha=get_latest_commit_sha(project_dir),
```

**DATA:** `get_latest_commit_sha(project_dir) -> str | None`, forwarded unchanged.
Add no guard and no other logic. `None` keeps today's behaviour.

## Out of scope

Don't change `workflow_steps/ci.py`, `workflows/fix_ci/core.py`,
`cli/commands/check_branch_status.py`, create-pr, auto-merge, or
`tests/workflow_steps/test_rebase.py`.

## Checks

- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pytest_check` with the fast unit-test marker set and `-n auto`
