# Step 1: Mark all six comment-posting sites with `❌`

See [summary.md](./summary.md) for full context. This step implements design
point 1 only: no status-file changes yet (that's steps 2-3).

## WHERE

All changes are to existing functions/strings; no new files.

| File | Function | Change |
|---|---|---|
| `src/mcp_coder/workflows/review/handoff.py` | `_route_to_human` | prefix `comment_body` with `"❌ "` |
| `src/mcp_coder/workflows/implement/failure_reporting.py` | `format_failure_comment` | heading `"## Implementation Failed"` → `"## ❌ Implementation Failed"` |
| `src/mcp_coder/workflows/create_pr/helpers.py` | `format_failure_comment` | heading `"## PR Creation Failed"` → `"## ❌ PR Creation Failed"` |
| `src/mcp_coder/workflows/create_plan/core.py` | `_format_failure_comment` | heading `"## Planning Failed"` → `"## ❌ Planning Failed"` |
| `src/mcp_coder/workflows/create_plan/core.py` | `run_create_plan_workflow` (the `run_guarded(...)` call at the bottom) | `comment_header="## Planning Failed"` → `comment_header="## ❌ Planning Failed"` |
| `src/mcp_coder/workflows/create_pr/core.py` | `run_create_pr_workflow` (the `run_guarded(...)` call at the bottom) | `comment_header="## PR Creation Failed"` → `comment_header="## ❌ PR Creation Failed"` |

Do **not** touch `_fail` in `handoff.py` (already `❌ `-prefixed), or the
`run_guarded` calls in `implement/core.py` / `review/core.py` (they already
pass a `build_comment` closure or already bake `❌` into `comment_header`).

## WHAT

No new function signatures. Every change is a literal-string edit inside an
existing function body or an existing keyword argument value.

## HOW

No new imports, no new decorators, no integration points — this step only
changes string literals that are already being built and passed to
`handle_workflow_failure` / `run_guarded` exactly as before.

## ALGORITHM

Not applicable — no logic changes, only literal text.

## DATA

Not applicable — return types and call signatures are unchanged.

## Tests (write first, then make the change)

Update the existing assertions that pin the old text to the new marked text:

| Test file | Line (approx) | Old assertion | New assertion |
|---|---|---|---|
| `tests/workflows/review/test_handoff_route.py` | `test_route_flushes_comments_labels_returns_zero` | `routed.issue_manager.return_value.add_comment.assert_called_once_with(42, "handing off")` | `...assert_called_once_with(42, "❌ handing off")` |
| `tests/workflows/implement/test_failure_reporting.py` | ~line 75 | `assert "## Implementation Failed" in result` | `assert "## ❌ Implementation Failed" in result` |
| `tests/workflows/create_pr/test_failure_handling.py` | ~line 24 | `assert "## PR Creation Failed" in comment` | `assert "## ❌ PR Creation Failed" in comment` |
| `tests/workflows/create_plan/test_failure_handling.py` | ~line 33 | `assert "## Planning Failed" in comment` | `assert "## ❌ Planning Failed" in comment` |

No other test in the repo asserts this literal text (confirmed by
project-wide search) — the `run_guarded` crash-net paths for `create_plan`
and `create_pr` are tested in `test_guard_net.py` /
`test_failure_handling.py`'s `TestGuardNet`-equivalent classes, and those
mock `handle_workflow_failure` itself, asserting only on `failure.category`,
never on comment text — so no change needed there.

Run these four tests red (confirm they fail against the old text) before
making the corresponding production edit, then green after.

## Commit

One commit: all six production edits + the four test edits above, plus a
full `run_pytest_check` / `run_pylint_check` / `run_mypy_check` pass.

## LLM prompt for this step

> Implement Step 1 of `pr_info/steps/summary.md` (see that file for full
> context): add a `❌` marker to all six automated failure/handoff
> comment-posting sites, per the table and test-assertion table in
> `pr_info/steps/step_1.md`. Update the four listed test assertions first,
> confirm they fail, then make the six production edits so they pass. Make
> no other functional change. Run pytest, pylint and mypy; all must pass.
> Produce exactly one commit for this step. If any of the six listed
> functions/lines no longer match what's described (e.g. the heading text
> has already changed), write one line to `pr_info/.blocked.txt` and stop.
