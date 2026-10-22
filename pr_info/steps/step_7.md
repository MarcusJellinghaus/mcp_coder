# Step 7 — Review `_fail` → structured "Failed" comment

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 7** exactly as described in
> `pr_info/steps/step_7.md`. If `ReviewConfig.display_name` or
> `build_failure_comment` does not exist, write one line to `pr_info/.blocked.txt`
> and stop. Tests first, then implementation. Run pylint, pytest (fast unit set,
> `-n auto`) and mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/workflows/review/handoff.py` — `_fail` + `_FAIL_REASONS`
- Tests: `tests/workflows/review/test_core_gates.py` (`:74` Gate 2 details), `test_core.py`, `test_core_after_steps.py`, `test_handoff_route.py` — wherever the `_fail` comment text is asserted

## WHAT

```python
# reason -> (Category display, Error sentence used when `details` is None)
_FAIL_REASONS: dict[str, tuple[str, str]] = {
    "general": ("General", "The review stopped on an unrecoverable error; check the job log"),
    "timeout": ("Llm Timeout", "An LLM call timed out"),
    "mcp_unavailable": ("Mcp Unavailable", "The MCP servers were unavailable"),
    "ci": ("CI failed", "CI is still red after the review"),
    "tasks": ("Open tasks", "The task tracker still has unchecked tasks"),
    "ci_unknown": ("CI not proven green", "CI could not be proven green"),
    "commit-failed": ("Commit failed", "Committing the review fixes failed"),
    "push-failed": ("Push failed", "Pushing the review fixes failed"),
}

def _fail(config, project_dir, reason, *, update_issue_labels, post_issue_comments,
          round_number=None, verdict=None, elapsed=None, details=None) -> int:  # signature unchanged
```

## HOW

- Import `build_failure_comment` from `mcp_coder.workflow_utils.failure_handling`.
- Label lookup (`config.failure_labels.get(reason, …["general"])`) and the
  `WorkflowFailure` passed to `handle_workflow_failure` stay as today.
- `_fail` already runs after the call sites' `_flush_round_log`, so the builder's
  HEAD SHA is post-flush — no call-site change.

## ALGORITHM

```
category, sentence = _FAIL_REASONS.get(reason, _FAIL_REASONS["general"])
stage = f"{config.display_name}, round {round_number}" if round_number is not None else config.display_name
comment_body = build_failure_comment(project_dir, title=config.display_name, kind="Failed",
    fields=[("Category", category), ("Stage", stage), ("Error", details or sentence),
            ("Verdict", verdict.decision if verdict else None)],
    elapsed=elapsed)
handle_workflow_failure(failure, comment_body, ...)   # unchanged
```

## DATA

Example: `## ❌ Implementation Review Failed` / `**Category:** CI failed` /
`**Stage:** Implementation Review, round 3` / `**Error:** …` / Branch / Verdict /
Elapsed / Build. Pre-loop sites (`round_number=None`) render Stage without round.

## Tests

- Patch `_branch_head` in the review `env` fixture (`tests/workflows/review/conftest.py`) so every review test gets a fixed Branch line.
- Heading `## ❌ Implementation Review Failed` / `## ❌ Plan Review Failed`.
- `details` given → Error is `details` (Gate 2 test `test_core_gates.py:74`, formatter pre-flight, Gate 1); not given → the reason sentence.
- Stage includes `round N` inside the loop; pre-loop `_fail` → Stage is just the lane name.
- Unknown reason falls back to the `general` Category.
- Replace old assertions on `❌ review-implementation review failed: …`, `Round: N`, `Verdict: …`, `Elapsed: …` with the bold-label forms.
