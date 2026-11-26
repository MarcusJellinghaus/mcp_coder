# Step 9: formatted commit before the CI gate on a dismiss round

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_9.md`.
> Write the tests first, then the code. Run pylint, mypy, the fast pytest set
> (`-n auto`) and `check_file_size` (max 750). Format, then make exactly one
> commit.

## WHERE

- `src/mcp_coder/workflows/review/handoff.py`: new constant
  `FORMAT_BEFORE_GATE_MESSAGE`
- `src/mcp_coder/workflows/review/core.py`: dismiss branch
- `tests/workflows/review/test_core_dismiss_format.py` (new)
- Existing review tests that count `commit_all_changes` calls on the
  implementation-lane dismiss path: adapt the expected count

## WHAT

```python
# handoff.py
FORMAT_BEFORE_GATE_MESSAGE = "style: format before the CI gate"
```

```python
# core.py, first lines of `if verdict.decision == "dismiss":`
if config.run_after_steps:
    # The rebase push in _after_steps carries this commit, so the commit
    # check_ci_proven_gate judges is formatted.
    _flush_round_log(project_dir, FORMAT_BEFORE_GATE_MESSAGE, push=False)
reason, rebase_outcome, ci_detail = _after_steps(..., is_dismiss=True)
```

## HOW

- Import `FORMAT_BEFORE_GATE_MESSAGE` from `.handoff` in `core.py`.
- Implementation lane only (`config.run_after_steps`). The plan lane's
  `_after_steps` returns without pushing, and its later dismiss flush
  already formats and pushes (step 8).
- Not `commit_changes`: no LLM message call.
- Clean tree: `commit_all_changes` returns `commit_hash=None` (INFO only), and
  `_flush_round_log` logs DEBUG, so nothing is committed and there is no
  WARNING. A failed commit logs the flush's existing WARNING, and the review
  continues. A dirty tree then trips the rebase gate's `dirty_tree` handoff,
  whose `_route_to_human` scoped flush pushes any local commit.
- The precondition is the same as step 5's, applied to
  `src/mcp_coder/workflows/review/core.py`: if `check_file_size` (max 750)
  reports it, write one line to `pr_info/.blocked.txt` and stop.

## ALGORITHM

```
if verdict.decision == "dismiss":
    if config.run_after_steps: _flush_round_log(project_dir, FORMAT_BEFORE_GATE_MESSAGE, push=False)
    reason, outcome, detail = _after_steps(..., is_dismiss=True)
    ... unchanged gate handling, final dismiss flush (formats + pushes)
```

## DATA

No new return values.

## Tests first (`test_core_dismiss_format.py`, `env` fixture)

- **Implementation lane, round-1 dismiss:** record order across
  `env.commit_all_changes`, `env.attempt_rebase_and_push` and `env.flush_push`.
  - The first `commit_all_changes` call has the message
    `FORMAT_BEFORE_GATE_MESSAGE` and comes before the rebase.
  - `formatter_mocks.format_best_effort` is called before it.
  - `env.flush_push` is not called before the rebase.
  - `env.commit_changes` is not called.
  - The run returns 0.
- **Clean tree:** `env.commit_all_changes` returns `commit_hash=None`
  (`success=True`, `error_category=None`). No WARNING or ERROR record from
  `mcp_coder.workflows.review` (caplog); returns 0.
- **Commit fails:** the first `commit_all_changes` returns `success=False`.
  WARNING logged, the review still reaches `_after_steps`, returns 0.
- **Formatter fails:** real `handoff.format_best_effort` restored,
  `commit.run_formatters` raising `FormatterConfigError`. WARNING logged,
  `commit_all_changes` called with `FORMAT_BEFORE_GATE_MESSAGE`, review
  continues.
- **Plan lane:** `_run(tmp_path, config=REVIEW_PLAN)` with a dismiss verdict.
  No `commit_all_changes` call with `FORMAT_BEFORE_GATE_MESSAGE`.

Run the whole `tests/workflows/review/` folder and fix the expected
`commit_all_changes` call counts that now include the pre-gate commit.

## Commit

`feat(review): commit the formatted tree before the CI gate on dismiss`
