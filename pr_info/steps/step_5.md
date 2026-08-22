# Step 5 — `core.py` routes `blocked`, and the final-mypy commit path is cleaned

Closes the loop: the reason produced in Step 3 now reaches the label defined in Step 4.

## WHERE

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/implement/failure_reporting.py` | `FAILURE_LABELS`, `CATEGORY_DISPLAY`, `append_detail()` |
| `src/mcp_coder/workflows/implement/core.py` | `blocked` branch, detail on timeout/mcp messages, marker cleanup before the final-mypy commit |
| `tests/workflows/implement/test_failure_reporting.py` | mapping assertions |
| `tests/workflows/implement/test_core_blocked.py` | **new module** — routing tests |
| `tests/workflows/implement/test_core.py` | final-mypy cleanup test |

The routing tests go in a **new** module, not in `test_core_workflow.py`: that file is already
747 lines and is not in `.large-files-allowlist`, so four more tests would breach the CI
`file-size` gate (`mcp-coder check file-size --max-lines 750`, `.github/workflows/ci.yml`).

## WHAT

`failure_reporting.py`:

```python
FAILURE_LABELS["blocked"] = "implementation_blocked"
CATEGORY_DISPLAY["blocked"] = "Blocked"

def append_detail(message: str, detail: str) -> str:
    """Append an agent-reported blocked reason to a failure message."""
    return f"{message} (agent reported: {detail})" if detail else message
```

`core.py` — inside the task loop's `if not outcome.success:` chain, directly after the
`no_tasks` branch:

```python
if outcome.reason == "blocked":
    logger.error("Implementation blocked: %s", outcome.detail)
    return fail(
        "blocked",
        stage="Task implementation",
        message=outcome.detail,
    )
```

and the two existing typed-failure branches gain the detail:

```python
if outcome.reason == "timeout":
    return fail(
        "timeout",
        stage="Task implementation",
        message=append_detail("LLM timed out during task processing", outcome.detail),
    )
# same shape for mcp_unavailable
```

## HOW

- Import `append_detail` from `.failure_reporting` (which `core.py` already imports
  `Progress`, `_fail` and `format_failure_comment` from) and `read_and_clear_blocked` from
  `.task_processing` (which it already imports `check_and_fix_mypy` and
  `process_task_with_retry` from).
- **No retry, terminal.** `fail(...)` returns `1` and the `return` exits the loop — nothing
  further is needed to make `blocked` terminal.
- **The ERROR log is unconditional**, deliberately independent of `post_issue_comments`:
  comment posting can be off, and the reason text is the entire point of the change.
- `outcome.detail` becomes the `**Error:**` line of the failure comment, via `_fail`'s
  `message` argument.
- **Do not** refactor the reason chain into a data-driven table while you are here. The
  failure comments are asserted byte-for-byte in `test_failure_reporting.py`; add one `if`.

### Final-mypy commit path (§6 of the issue)

`check_and_fix_mypy` runs its own LLM turns, so a marker written there would be staged by
the block that follows. Immediately before that block's `get_full_status`:

```python
read_and_clear_blocked(project_dir)   # never let a marker reach a commit
status = get_full_status(project_dir)
```

Cleanup only — no blocked channel in the final-mypy path.

## ALGORITHM

```
outcome = process_task_with_retry(...)
if not outcome.success:
    no_tasks                -> break (legitimate completion)
    blocked                 -> log ERROR; fail("blocked", message=outcome.detail)   # terminal
    timeout / mcp_unavailable -> fail(reason, message=append_detail(base, outcome.detail))
    no_changes_after_retries / error -> unchanged
```

## DATA

| Reason | Label id | Comment Category | `**Error:**` line |
|---|---|---|---|
| `blocked` | `implementation_blocked` | `Blocked` | the agent's text |
| `timeout` | `llm_timeout` | `Llm Timeout` | base message + `(agent reported: …)` when a marker was present |
| `mcp_unavailable` | `mcp_unavailable` | `Mcp Unavailable` | as above |

## TESTS (write first)

`tests/workflows/implement/test_failure_reporting.py`:
1. `FAILURE_LABELS["blocked"] == "implementation_blocked"` and
   `CATEGORY_DISPLAY["blocked"] == "Blocked"`.
2. `append_detail("base", "")  == "base"` and `append_detail("base", "why")` contains both.
3. `format_failure_comment("blocked", ...)` renders `**Category:** Blocked`.

`tests/workflows/implement/test_core_blocked.py` — a new module (see WHERE); model the mock
setup on `test_core_workflow.py`'s `test_no_changes_after_retries_routes_to_failure` at
`:416`, including its `_DELIBERATE_HANDLER` patch target and the seven prerequisite patches:
4. `test_blocked_routes_to_failure` — `process_task_with_retry` returns
   `TaskOutcome(False, "blocked", "pytest times out at 300s")` → result is `1`,
   `failure_arg.category == "implementation_blocked"`, and the failure message **is** the
   detail text.
5. `test_blocked_does_not_loop` — the same mock, `mock_process.call_count == 1`.
6. `test_blocked_reason_logged_at_error` — with `post_issue_comments=False`, assert via
   `caplog` at `ERROR` that the detail text was logged.
7. `test_timeout_appends_marker_detail` — `TaskOutcome(False, "timeout", "why")` → the
   message contains both the base timeout text and `why`.

`tests/workflows/implement/test_core.py`:
8. Extend the existing final-mypy test (or add one modelled on it) to patch
   `core.read_and_clear_blocked` and assert it is called before `core.get_full_status` in
   that block — attaching both to a `Mock` manager and asserting on `mock_calls` order is
   the simplest way.

## COMMIT

`Route blocked outcome to implementation_blocked label`

## LLM PROMPT

```
Read pr_info/steps/summary.md (sections 5 and 8) and pr_info/steps/step_5.md, then
implement Step 5 only.

This step wires the "blocked" reason produced in Step 3 to the implementation_blocked
label defined in Step 4, and adds marker cleanup to the final-mypy commit path.

Work test-first: write the failure_reporting, blocked-routing and core tests described in
the step file, watch them fail, then implement.

The four blocked-routing tests go in a NEW module,
tests/workflows/implement/test_core_blocked.py. Do NOT add them to test_core_workflow.py:
that file is at 747 lines and is not allowlisted, so it would breach the CI file-size gate
(mcp-coder check file-size --max-lines 750).

Requirements that are easy to get wrong:
- The ERROR log of the blocked reason is unconditional. It must NOT be gated on
  post_issue_comments — that flag can be off, and the text is the whole point.
- blocked is terminal and does not retry. fail() returning 1 plus the return statement is
  all that is needed; do not add retry logic.
- The agent's text becomes the **Error:** line of the failure comment, i.e. it is passed
  as _fail's `message` argument.
- When a marker AND a typed LLM failure are both present, the LLM failure keeps its label
  (llm_timeout / mcp_unavailable) and the marker text is appended to its message. Step 3
  already put the text in outcome.detail; here you only append it.
- Do NOT refactor core.py's reason if/elif chain into a table. The failure comments are
  asserted byte-for-byte; add one branch.

Use MCP tools for all file operations. When done, run all three checks and fix everything
they report:
  mcp__tools-py__run_pylint_check
  mcp__tools-py__run_mypy_check
  mcp__tools-py__run_pytest_check with
    extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and
    not claude_api_integration and not formatter_integration and not github_integration
    and not langchain_integration"]

Then run ./tools/format_all.sh and make exactly one commit.
```
