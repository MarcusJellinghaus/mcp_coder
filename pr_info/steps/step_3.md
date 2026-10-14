# Step 3 — Shared import-fallback command stub

Read `pr_info/steps/summary.md` first for overall context.

Part of issue #1171. Consolidates the 3 identical import-fallback stubs in
`tests/cli/commands/test_check_branch_status.py`, `test_create_pr.py`, and
`test_implement.py` into one shared, typed helper in the existing
`tests/cli/commands/conftest.py`.

## Precondition check

Run `mcp__mcp-tools-py__run_ruff_check` with
`select=["ANN001","ANN002","ANN003","ANN201"]`, `max_issues=10`. If it does
not report one `(*args, **kwargs)` stub each in
`tests/cli/commands/test_check_branch_status.py` (line ~33),
`tests/cli/commands/test_create_pr.py` (line ~30), and
`tests/cli/commands/test_implement.py` (line ~26), write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- Modify: `tests/cli/commands/conftest.py` (already exists)
- Modify: `tests/cli/commands/test_check_branch_status.py`
- Modify: `tests/cli/commands/test_create_pr.py`
- Modify: `tests/cli/commands/test_implement.py`

## WHAT

Add to `tests/cli/commands/conftest.py`:

```python
def unavailable_command_stub(args: argparse.Namespace) -> int:
    """Stand-in for a CLI command module that failed to import."""
    raise NotImplementedError("command module unavailable")
```

(`argparse` is already imported in this file.)

## HOW

In each of the three test files, replace the local stub definition in the
`except ImportError:` (or `except Exception as e:` for `test_create_pr.py`)
branch:

```python
# before (test_check_branch_status.py)
def execute_check_branch_status(*args, **kwargs):  # type: ignore
    """Stub for when check_branch_status module is unavailable."""

# after
from tests.cli.commands.conftest import unavailable_command_stub

execute_check_branch_status = unavailable_command_stub
```

Same pattern for `execute_create_pr` in `test_create_pr.py` and
`execute_implement` in `test_implement.py` — each binds the same shared
function under its own locally-expected name. Add the
`from tests.cli.commands.conftest import unavailable_command_stub` import
inside the `except` block (matching where the stub definition currently
lives) or at module top — either works since the import has no heavy
dependency; prefer module top for consistency with the rest of each file's
imports, keeping the `except` block to the one assignment line.

## ALGORITHM

N/A — direct substitution, no branching logic beyond what exists today.

## DATA

`unavailable_command_stub` return type: `int` (never actually reached —
guarded by each file's `@pytest.mark.skipif(not MODULE_AVAILABLE, ...)` —
but matches the real `execute_*` functions' return type).

## TDD

Add one direct test to `tests/cli/commands/conftest.py`'s own coverage via a
new small test in `tests/cli/commands/test_check_branch_status.py` (or a new
tiny file `tests/cli/commands/test_conftest_helpers.py` if that reads
cleaner) asserting the contract:

```python
def test_unavailable_command_stub_raises() -> None:
    with pytest.raises(NotImplementedError):
        unavailable_command_stub(argparse.Namespace())
```

Write this test first, confirm it fails (function doesn't exist yet), then
add the function, then migrate the three call sites.

## Verification

- `mcp__mcp-tools-py__run_pytest_check` with
  `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_format_code`, then commit.

## Commit

One commit:
`refactor(tests): consolidate CLI command import-fallback stubs`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement
> step 3 exactly as specified: add the test for `unavailable_command_stub`
> first, then the function in `tests/cli/commands/conftest.py`, then migrate
> the three stub definitions in `test_check_branch_status.py`,
> `test_create_pr.py`, and `test_implement.py` to use it, removing the
> `# type: ignore` comments. Run the verification commands listed in the
> step, fix anything they report, then run `run_format_code` and commit with
> the given message. If the precondition check fails, write one line to
> `pr_info/.blocked.txt` and stop.
