# Step 2 — `TaskOutcome` replaces `tuple[bool, str]`

Mechanical, wide, **no behaviour change**. Kept as its own commit so the ~50-site diff does
not hide the ~40 lines that actually matter (Step 3).

## WHERE

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/implement/task_processing.py` | define `TaskOutcome`; 2 signatures, 11 returns |
| `src/mcp_coder/workflows/implement/core.py` | 1 unpack + the reason chain |
| `tests/workflows/implement/test_task_processing.py` | ~35 call sites |
| `tests/workflows/implement/test_core.py` | mock return values |
| `tests/workflows/implement/test_core_workflow.py` | mock return values **− the four failure-routing tests moved out (see below)** |
| `tests/workflows/implement/test_core_failure_routing.py` | **new module** — receives those four tests |
| `tests/workflows/implement/test_failure_reporting.py` | mock return values |
| `tests/integration/test_execution_dir_integration.py` | mock return value **+ the broken patch target / assertion** |

`src/mcp_coder/workflows/implement/__init__.py` exports names only — **no change**.

### The CI file-size gate forces a split here

`test_core_workflow.py` is **747 lines** and is **not** in `.large-files-allowlist`, so the
CI `file-size` job (`mcp-coder check file-size --max-lines 750`, `.github/workflows/ci.yml`)
leaves three lines of headroom. This step spends more than that:

- `+1` for the `TaskOutcome` import;
- `+3` at `:114`, where
  `mock_process_task.side_effect = [(True, "completed"), (False, "no_tasks")]` grows from 82
  to 104 characters and black (line-length 88) wraps it across four lines.

That lands at ~751 and breaks the gate. Rather than grandfather the file, **move the four
failure-routing tests out of `TestRunImplementWorkflowLabelTransitions` into a new module**
`tests/workflows/implement/test_core_failure_routing.py`:

| Moved test | Current lines |
|---|---|
| `test_timeout_calls_handle_failure_with_llm_timeout` | `:346-380` |
| `test_mcp_unavailable_calls_handle_failure_with_mcp_unavailable` | `:381-415` |
| `test_no_changes_after_retries_routes_to_failure` | `:416-450` |
| `test_error_calls_handle_failure_with_general` | `:451-478` |

Move them verbatim (converting their tuple mocks to `TaskOutcome` as part of this step),
carrying the module docstring, the `_DELIBERATE_HANDLER` / `_NET_HANDLER` constants and the
`_make_llm_response` helper they need. `test_core_workflow.py` drops to ~614 lines, and
Step 5's blocked-routing tests get an obvious home in the new module rather than needing
one of their own.

## WHAT

```python
@dataclass(frozen=True)
class TaskOutcome:
    """Result of one implementation task attempt."""
    success: bool
    reason: str
    detail: str = ""
```

```python
def process_single_task(...) -> TaskOutcome: ...
def process_task_with_retry(...) -> TaskOutcome: ...
```

Every `return False, "x"` becomes `return TaskOutcome(False, "x")`; `return True,
"completed"` becomes `return TaskOutcome(True, "completed")`. `detail` stays at its default
`""` everywhere in this step — it is only populated in Step 3.

## HOW

- `from dataclasses import dataclass` at the top of `task_processing.py`.
- `process_task_with_retry` returns the inner outcome unchanged:

```python
outcome = process_single_task(..., attempt=attempt, ...)
if outcome.reason != "no_changes":
    return outcome
logger.warning(...)
return TaskOutcome(False, "no_changes_after_retries")
```

- In `core.py`, bind the result to `outcome` rather than unpacking. This deliberately
  avoids the existing `reason` local, which is reused later in the final-mypy and CI
  `except` blocks (`reason = llm_failure_reason(exc) or "general"`) — no shadowing:

```python
outcome = process_task_with_retry(...)
if not outcome.success:
    if outcome.reason == "no_tasks":
        break
    if outcome.reason == "timeout":
        ...
```

- Do **not** add `__iter__` or use `NamedTuple` to preserve two-value unpacking. An object
  with three fields that unpacks to two is a trap: the next reader writes
  `s, r = outcome` and never learns `detail` exists.

## ALGORITHM

None — pure type substitution.

## DATA

`TaskOutcome(success, reason, detail="")`. Reason strings are unchanged from today:
`completed` \| `no_tasks` \| `no_changes` \| `error` \| `timeout` \| `mcp_unavailable`
(+ `no_changes_after_retries` from the wrapper).

## TESTS

No new tests — convert existing ones, and relocate four of them (see "The CI file-size gate
forces a split here"). Two mechanical patterns:

```python
# call sites against the real function
success, reason = process_single_task(...)   →   outcome = process_single_task(...)
assert success is True                       →   assert outcome.success is True
assert reason == "completed"                 →   assert outcome.reason == "completed"

# mock return values / side effects
mock_process.return_value = (False, "no_changes")
                                             →   TaskOutcome(False, "no_changes")
mock_process.side_effect = [(False, "no_changes"), (True, "completed")]
                                             →   [TaskOutcome(...), TaskOutcome(...)]
```

Import `TaskOutcome` from `mcp_coder.workflows.implement.task_processing` in each test
module that constructs one.

### Also in this step: fix the broken integration test

`tests/integration/test_execution_dir_integration.py`,
`test_implement_workflow_passes_execution_dir_to_task_processing`:

1. `:332` patches `mcp_coder.workflows.implement.core.process_single_task` — a name
   `core.py` does not import. Change the patch target to `...core.process_task_with_retry`.
2. `:377-379` asserts `assert_called_once_with(project_dir, "claude", None, None,
   execution_dir)`, which does not match the real call — `core.py` also passes
   `format_code=` and `check_type_hints=` as keyword arguments. Add them.

Compute the expected keyword values in the test rather than hard-coding them, so the
assertion tracks the real defaults:

```python
from mcp_coder.utils.pyproject_config import get_implement_config
cfg = get_implement_config(project_dir)
mock_process_task.assert_called_once_with(
    project_dir, "claude", None, None, execution_dir,
    format_code=cfg.format_code, check_type_hints=cfg.check_type_hints,
)
```

The test carries a `require_claude_cli` fixture, so the default run **skips** it and the
`AttributeError` stays masked. Verify it explicitly with
`markers=["claude_cli_integration"]`; if the environment skips it anyway, at minimum
confirm by inspection that `core.py` imports `process_task_with_retry` and that the patch
string matches.

## COMMIT

`Replace (success, reason) tuple with TaskOutcome dataclass`

## LLM PROMPT

```
Read pr_info/steps/summary.md (section 2) and pr_info/steps/step_2.md, then implement
Step 2 only.

This is a mechanical, behaviour-preserving refactor: process_single_task and
process_task_with_retry return a TaskOutcome dataclass instead of tuple[bool, str].
Leave `detail` at its default "" everywhere — populating it is Step 3.

Do not add __iter__, do not use NamedTuple, and do not use getattr() fallbacks to keep
stale tuple mocks working. Every mock that returns a task outcome must construct a real
TaskOutcome.

Also fix the two pre-existing defects in
tests/integration/test_execution_dir_integration.py described in the step file: the patch
target names a symbol core.py does not import, and the assertion omits the format_code /
check_type_hints keyword arguments.

One thing you must not skip: tests/workflows/implement/test_core_workflow.py is 747 lines
and is NOT in .large-files-allowlist, so it has three lines of headroom against the CI
file-size gate (750). This step's import plus black's rewrap of line 114 spends four. Move
the four failure-routing tests listed in the step file into a new module
tests/workflows/implement/test_core_failure_routing.py as part of this commit, then verify
with `mcp-coder check file-size --max-lines 750` that no file breaches the gate.

Success criterion: the full test suite passes with no test asserting anything new. If a
test starts failing for a reason other than the tuple→dataclass change, stop and report it
rather than adjusting the assertion.

Use MCP tools for all file operations. When done, run all three checks and fix everything
they report:
  mcp__tools-py__run_pylint_check
  mcp__tools-py__run_mypy_check
  mcp__tools-py__run_pytest_check with
    extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and
    not claude_api_integration and not formatter_integration and not github_integration
    and not langchain_integration"]
Additionally run mcp__tools-py__run_pytest_check with markers=["claude_cli_integration"]
to exercise the integration test you fixed; report if it skips.

Then run ./tools/format_all.sh and make exactly one commit.
```
