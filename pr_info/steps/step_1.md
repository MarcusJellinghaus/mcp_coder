# Step 1 — fix-conflict sets the final label on every handled outcome

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> TDD: update the tests in `tests/workflows/fix_conflict/test_core.py` first, then change
> `src/mcp_coder/workflows/fix_conflict/core.py` until they pass. Keep the change minimal.
> Run pylint, the fast pytest suite (`-n auto` with the non-integration marker filter from
> CLAUDE.md) and mypy; all must pass. Format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/fix_conflict/core.py`
- `tests/workflows/fix_conflict/test_core.py`

## Precondition

`src/mcp_coder/workflow_utils/failure_handling.py` exports `WorkflowFailure`,
`build_failure_comment`, `handle_workflow_failure`, and `FIELD_ORDER` contains `Verdict`,
`Reason`, `Base`, `Likely conflicting files`, `Uncommitted files`. If not, write one line to
`pr_info/.blocked.txt` and stop.

## Tests first (`test_core.py`)

- `_patch_all(mergeable_states, outcome=RebaseOutcome("ok", "main", "abc1234"))`: use
  `outcome` as the `_attempt_rebase_and_push` return value and append a 7th patch,
  `patch(f"{MODULE}.handle_workflow_failure")`. Update existing `with` blocks for the extra
  patch (index 6).
- Replace `test_dirty_on_first_poll_transitions_to_pr_merge_conflict`,
  `test_unknown_for_all_attempts_leaves_label_untouched` and
  `test_no_open_pr_found_treated_as_unresolved` with one parametrized
  `test_unresolved_outcomes_go_to_pr_merge_conflict`, cases:
  - `dirty`: states `[[{"mergeable_state": "dirty"}]]`, outcome
    `RebaseOutcome("conflict", "main", "abc1234", ("a.py", "b.py"))`; expect
    `"still conflicting"`, `"**Reason:** conflict"`, `"**Base:** main"`,
    `"**Likely conflicting files:** a.py, b.py"`.
  - no PR: states `[[]] * 6`, outcome ok; expect `"no open PR found for branch"`, and
    `"**Reason:**"` NOT in comment.
  - unknown + failed rebase: states `[[{"mergeable_state": "unknown"}]] * 6`, outcome
    `RebaseOutcome("push_failed", "main", "abc1234")`; expect
    `"mergeable state unknown, rebase did not complete"`, `"**Reason:** push_failed"`.
  - Each case also patches `_BRANCH_HEAD` (`return_value=(BRANCH_NAME, "abc1234")`) and asserts:
    result `0`; `handle_workflow_failure` called once; `call_args[0][0].category ==
    "pr_merge_conflict"`; comment (`call_args[0][1]`) first line `"## ❌ Fix Conflict Failed"`
    and contains `"**Verdict:** <verdict>"` plus the expected substrings;
    kwargs `from_label_id="fixing_merge_conflict"`, `update_issue_labels=True`,
    `post_issue_comments=True`; `update_workflow_label` not called;
    `mock_sleep.call_count == expected_sleeps` (keeps the existing poll-cadence checks:
    `0` for a `dirty` first poll, `5` for no PR and for `unknown` on every attempt).
- Replace `test_clean_transitions_to_pr_created` with parametrized
  `test_settled_or_self_healing_outcomes_go_to_pr_created`, cases:
  `[[{"mergeable_state": "clean"}]]` and `[[{"mergeable_state": "unknown"}]] * 6` (outcome ok).
  Assert result `0`, `update_workflow_label.assert_called_once_with(mock_issue_cls.return_value,
  "fixing_merge_conflict", "pr_created")`, `handle_workflow_failure.assert_not_called()`,
  `mock_sleep.call_count == expected_sleeps` (`0` for `clean`, `5` for `unknown`).
- Add one assertion that a `dirty_tree` outcome renders `Uncommitted files` and no `Base`
  (may be a 4th case of the `status-74` parametrization with state `dirty`, outcome
  `RebaseOutcome("dirty_tree", files=("uv.lock",))`, `expected_sleeps=0`).
- Keep `test_no_current_branch_returns_1_without_rebase`, the crash and SystemExit tests
  unchanged (they patch `_SHARED_HANDLER`, the `run_guarded` path).

## WHAT (`core.py`)

```python
def _fail(project_dir: Path, verdict: str, outcome: RebaseOutcome) -> None:
    """status-74 verdict: structured "Fix Conflict Failed" comment + pr_merge_conflict label."""
```

Imports: `WorkflowFailure`, `build_failure_comment`, `handle_workflow_failure` from
`mcp_coder.workflow_utils.failure_handling` (alongside `run_guarded`); `RebaseOutcome` from
`mcp_coder.workflow_steps.rebase`.

## ALGORITHM

`_fail`:
```
files_label = "Likely conflicting files" if outcome.reason == "conflict" else "Uncommitted files"
fields = [("Verdict", verdict), ("Reason", None if outcome.ok else outcome.reason),
          ("Base", outcome.base_branch),
          (files_label, ", ".join(outcome.files) if outcome.files else None)]
comment = build_failure_comment(project_dir, title="Fix Conflict", kind="Failed", fields=fields)
handle_workflow_failure(WorkflowFailure(category="pr_merge_conflict",
    stage="Merge-conflict verdict", message=verdict), comment, project_dir,
    from_label_id="fixing_merge_conflict", update_issue_labels=True, post_issue_comments=True)
```

`body()` after `state = _poll_mergeable_state(...)`:
```
if state == "dirty": verdict = "still conflicting"
elif state is None: verdict = "no open PR found for branch"
elif state == "unknown" and not outcome.ok: verdict = "mergeable state unknown, rebase did not complete"
else: verdict = None
if verdict: _fail(project_dir, verdict, outcome)
else: (if state == "unknown": logger.info(... returning to status-10 ...)); update_workflow_label(IssueManager(project_dir), "fixing_merge_conflict", "pr_created")
return 0
```

## HOW

- `run_guarded(...)` wrapping is unchanged; `branch is None` → `return 1` unchanged.
- Remove the "leaving at status-72 for next coordinator poll" log message.
- Update the `run_fix_conflict_workflow` docstring: 0 on every handled outcome (settled
  non-dirty or `unknown` after a successful rebase → `status-10`; `dirty`, no open PR, or
  `unknown` after a failed rebase → `status-74` with a comment); 1 on missing branch or a
  netted crash.

## DATA

- `_fail` returns `None`; `body()` still returns `0` on all handled outcomes.
- Comment example:
  ```
  ## ❌ Fix Conflict Failed
  **Reason:** conflict
  **Branch:** 123-fix-something @ abc1234
  **Base:** main
  **Likely conflicting files:** a.py, b.py
  **Verdict:** still conflicting
  ```
