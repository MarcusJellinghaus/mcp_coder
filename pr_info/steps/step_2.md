# Step 2 — `_fail(exc=)` and the three core.py catch sites

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` only
> (Step 1 is done: `exception_summary` and `comment_safe` exist). TDD: write the
> tests first, then the code. Run pylint, mypy, pytest (`-n auto`, fast unit
> markers) and lint-imports; all must pass. Format, then make exactly one commit.

## Precondition

If `mcp_coder.llm.error_summary.comment_safe` or
`mcp_coder.workflow_utils.failure_handling.exception_summary` does not exist, write
one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/workflows/review/handoff.py` — `_fail`
- `src/mcp_coder/workflows/review/core.py` — `except` blocks at the fresh reviewer
  (~220), the supervisor `_get_verdict` (~269) and the fix-task reviewer (~460)
- Create `tests/workflows/review/test_core_failure_detail.py`
- `tests/workflows/review/test_core.py` — extend two tests

## WHAT

```python
def _fail(
    config, project_dir, reason, *, update_issue_labels, post_issue_comments,
    round_number=None, verdict=None, elapsed=None, details=None,
    exc: BaseException | None = None,
) -> int: ...
```

Docstring: document `exc` (logged with traceback; summary appended to the banner;
comment-safe summary replaces the default Error sentence unless `details` is given).

## HOW

- `handoff.py` imports `exception_summary` (extend the existing
  `failure_handling` import) and `comment_safe` from `mcp_coder.llm.error_summary`.
- core.py: add `exc=exc` to the three `_fail(...)` calls inside `except Exception as exc:`.
  The fix-task site keeps `changes=reason` / `escalate_reason=reason` in
  `write_round_log` unchanged.

## ALGORITHM (`_fail`)

```
message = f"{config.name} review failed: {reason}"
summary = exception_summary(exc) if exc is not None else None
if summary is not None:
    logger.error("%s: %s", message, summary, exc_info=exc)   # traceback, once
    message = f"{message}: {summary}"
error_text = details or (comment_safe(summary) if summary is not None else sentence)
# use message in WorkflowFailure, error_text in the ("Error", ...) field
```

## DATA

Return value unchanged (`1`). `WorkflowFailure.message` gains `": <summary>"` only
when `exc` is given. Label/Category selection is unchanged.

## Tests

Comment body is `env.handle_workflow_failure.call_args.args[1]`; banner message is
`env.handle_workflow_failure.call_args.args[0].message`. Use the `env` fixture and
the helpers from `tests.workflows.review.conftest` (`_run`, `_resp`, `_reviewer`,
`_DISMISS`, `_TASKS`); pass `config=REVIEW_PLAN` to `_run` for these core-site tests.

`test_core_failure_detail.py` (new). Import `CalledProcessError` from
`mcp_coder.utils.subprocess_runner` — never `import subprocess` (the
`subprocess_isolation` import-linter contract forbids it under `tests` too).
- reviewer raises `CalledProcessError(1, "claude", stderr="529 Overloaded " + "x"*400 + " Stream file: /agent/s.log")`:
  comment contains `"CalledProcessError: 529 Overloaded"`, does not contain
  `"Stream file"` or `"/agent/s.log"`; the `**Error:**` line value is ≤ 300 chars and
  ends with `"…"`; banner message contains `"529 Overloaded"`
- reviewer raises `CalledProcessError(1, "claude", stderr="first line\nsecond line\r\n" + "y"*400 + "\nStream file: /agent/s.log")`:
  exactly one comment line starts with `"**Error:** "`; its value contains
  `"first line second line"`, is ≤ 300 chars, and the comment does not contain
  `"Stream file"`
- supervisor raises `RuntimeError("sup boom")` (`prompt_llm.side_effect = [_reviewer(), RuntimeError("sup boom")]`):
  comment contains `"RuntimeError: sup boom"`
- fix-task reviewer raises `RuntimeError("fix boom")`
  (`[_reviewer(), _resp(_TASKS), RuntimeError("fix boom")]`): comment contains
  `"RuntimeError: fix boom"`; the round log's Changes value is still `"general"`
- `caplog.at_level(logging.ERROR, logger=handoff.__name__)`: reviewer
  `RuntimeError("kaboom")` → exactly one record with `exc_info`, and its
  `exc_info[1]` is the raised exception

`test_core.py`:
- `test_generic_exception_at_reviewer_fails_general` (~426): also assert
  `"RuntimeError: kaboom"` in the comment body
- `test_mcp_unavailable_maps_to_mcp_label` (~333): also assert
  `"MCP servers unavailable"` in the comment body (label assertion unchanged)
