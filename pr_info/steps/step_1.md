# Step 1 — Shared primitives: `llm_failure_reason` + `run_guarded`

**Reference:** `pr_info/steps/summary.md` §Architectural changes 1. This step is purely
**additive** — it introduces the shared harness without changing any workflow's behavior.
`implement/llm_failures.py` keeps working untouched (deleted in Step 2). TDD: write the tests
first, then the implementation, one commit.

## WHERE

- Modify `src/mcp_coder/workflow_utils/failure_handling.py`
- Modify `tests/workflow_utils/test_failure_handling.py` (add classifier tests)
- Create `tests/workflow_utils/test_run_guarded.py`

## WHAT

Add to `failure_handling.py`:

```python
from mcp_coder.llm.interface import LLMTimeoutError   # new import (McpServersUnavailableError already imported)

def llm_failure_reason(exc: BaseException) -> str | None: ...

@dataclass(frozen=True)
class GuardOutcome:
    caught_exception: BaseException | None
    sigterm_received: bool
    elapsed_time: float
    stage: str
    message: str

def run_guarded(
    body: Callable[[], int],
    *,
    project_dir: Path,
    from_label_id: str,
    general_category: str,
    comment_header: str,
    build_comment: Callable[[GuardOutcome], str] | None = None,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
    issue_number: int | None = None,
) -> int: ...
```

## HOW

- `llm_failure_reason`: `LLMTimeoutError → "timeout"`, `McpServersUnavailableError →
  "mcp_unavailable"`, else `None`. Identical logic to the current
  `implement/llm_failures.py::llm_failure_reason` (do **not** delete that file yet).
- `run_guarded` reuses the existing module-level `handle_workflow_failure`,
  `format_mcp_unavailable_message`, `format_elapsed_time`, and `WorkflowFailure`.
- New imports needed: `signal`, `sys`, `time`, `Callable` (from `typing`).

## ALGORITHM — `run_guarded`

```
start = time.time(); sigterm = False
def handler(signum, frame): nonlocal sigterm; sigterm = True; sys.exit(1)
try: prev = signal.signal(SIGTERM, handler)          # guard OSError/ValueError
try:
    return body()                                    # clean return (0 or 1) = terminal, net silent
except SystemExit: _net(caught=None, sigterm); raise # net THEN re-raise
except Exception as exc: _net(caught=exc, sigterm); return 1
finally: restore prev handler (guard OSError/ValueError)
```

`_net(caught, sigterm)` (inline helper, wrapped in try/except so net-failure never crashes):

```
stage = "SIGTERM received" if sigterm else "Unexpected exit"
if isinstance(caught, McpServersUnavailableError): msg = format_mcp_unavailable_message(caught)
elif sigterm: msg = "Workflow terminated by signal"
else: msg = "Workflow exited without reaching a terminal state"
outcome = GuardOutcome(caught, sigterm, time.time()-start, stage, msg)
comment = build_comment(outcome) if build_comment else (
    f"{comment_header}\n**Stage:** {stage}\n**Error:** {msg}\n"
    f"**Elapsed:** {format_elapsed_time(outcome.elapsed_time)}")
handle_workflow_failure(
    WorkflowFailure(general_category, stage, msg, outcome.elapsed_time),
    comment, project_dir, from_label_id=from_label_id,
    update_issue_labels=update_issue_labels, post_issue_comments=post_issue_comments,
    issue_number=issue_number)
```

## DATA

- `llm_failure_reason` → `str | None` (`"timeout"` / `"mcp_unavailable"` / `None`).
- `run_guarded` → `int` exit code (body's code on clean return; `1` on netted escape;
  re-raises `SystemExit`).
- `GuardOutcome` → frozen dataclass carrying the escape context for a `build_comment` closure.

## TESTS (write first)

`test_failure_handling.py` — add `TestLlmFailureReason`: timeout→`"timeout"`,
mcp→`"mcp_unavailable"`, `ValueError`→`None`.

`test_run_guarded.py`:
- body returns `0` → returns `0`, no label/comment (patch `handle_workflow_failure`, assert not
  called).
- body returns `1` → returns `1`, net silent.
- body raises `ValueError` → returns `1`, `handle_workflow_failure` called once with
  `category == general_category`; comment contains the header.
- body raises `McpServersUnavailableError` → comment/message names the servers.
- body calls `sys.exit(1)` (no SIGTERM) → labeled general **and** `SystemExit` re-raised
  (`pytest.raises(SystemExit)`), `handle_workflow_failure` called.
- body raises `SystemExit` after setting sigterm via the installed handler → labeled + re-raised
  (message "terminated by signal").
- `build_comment` provided and body mutates a small holder then raises → returned comment
  reflects the **live** mutated value (guards the closure/outcome contract).

## Verify

`run_pylint_check`, `run_pytest_check` (`-n auto` + unit-exclusion markers), `run_mypy_check`,
and `run_lint_imports_check` (confirm the new `LLMTimeoutError` import keeps layers green).

## LLM Prompt

> Implement Step 1 of `pr_info/steps/summary.md`. In
> `src/mcp_coder/workflow_utils/failure_handling.py` add `llm_failure_reason(exc)`, a frozen
> `GuardOutcome` dataclass, and `run_guarded(body, …)` exactly as specified in
> `pr_info/steps/step_1.md` (WHAT/HOW/ALGORITHM). This is additive — do **not** modify or delete
> `implement/llm_failures.py` or any workflow yet. Follow TDD: first add the `llm_failure_reason`
> tests to `tests/workflow_utils/test_failure_handling.py` and create
> `tests/workflow_utils/test_run_guarded.py` with the cases listed under TESTS, then implement
> until green. Run pylint, pytest (`-n auto` with the unit-test exclusion markers), mypy, and
> lint-imports. Produce exactly one commit.
