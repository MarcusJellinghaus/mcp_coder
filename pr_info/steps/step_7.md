# Step 7 — fix-conflict wiring

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **only** `pr_info/steps/step_7.md`.
> `workflow_steps/merge.py`, `resolve_auto_merge` and `add_auto_merge_arg` already exist;
> `74` already exits 1 (step 2). Follow TDD: tests first, then code. Run format, pylint,
> mypy, pytest (fast unit set, `-n auto`); make them pass. Produce exactly one commit.

## WHERE

- `src/mcp_coder/cli/workflow_parsers.py` — `add_auto_merge_arg(fix_conflict_parser)`;
  update its docstring ("project-dir and --auto-merge, no LLM args")
- `src/mcp_coder/cli/commands/fix_conflict.py`
- `src/mcp_coder/workflows/fix_conflict/core.py`
- Tests: `tests/cli/test_workflow_parsers.py`, `tests/cli/commands/test_fix_conflict.py`,
  `tests/workflows/fix_conflict/test_core.py`

## WHAT

```python
def run_fix_conflict_workflow(project_dir: Path, auto_merge: bool = False) -> int: ...
```

`execute_fix_conflict`: after resolving `project_dir`,
`auto_merge = resolve_auto_merge(args, project_dir)` (import from `..utils`), then
`return run_fix_conflict_workflow(project_dir, auto_merge=auto_merge)`.

## ALGORITHM — success path in `body()`

```
if verdict: _fail(...); return 1                     # unchanged (step 2)
if state == "unknown": log as today
if auto_merge:
    issue_number = resolve_merge_issue_number(project_dir, branch)
    outcome = run_auto_merge(project_dir, branch)     # its CI poll is the wait this command lacked
    return finish_auto_merge(project_dir, outcome, from_label_id="fixing_merge_conflict",
                             issue_number=issue_number, update_issue_labels=True, post_issue_comments=True)
return apply_final_label(project_dir, "fixing_merge_conflict", "pr_created")
```

## HOW

Import from `mcp_coder.workflow_steps.merge`. Update the `run_fix_conflict_workflow`
docstring with the auto-merge outcomes.

## Tests

- Parser accepts `--auto-merge` on `fix-conflict`; `execute_fix_conflict` resolves and forwards
  it (existing test asserting `run_fix_conflict_workflow(project_dir)` is updated).
- Success path + `auto_merge=True`: helper chain called with
  `from_label_id="fixing_merge_conflict"`, `update_issue_labels=True`,
  `post_issue_comments=True`; exit code is `finish_auto_merge`'s return value.
- Verdict path + `auto_merge=True`: helper not called, exit 1.
- `auto_merge=False`: unchanged.

## Done when

`fix-conflict --auto-merge` waits for CI on the rebased HEAD and merges; flag off unchanged.
