# Step 10 — Wire phase B into create-pr (two guards, final label, exit 0)

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_10.md` exactly.
> Write the tests first, then change `run_create_pr_workflow`.
> Run pylint, pytest (fast unit set, `-n auto`) and mypy; all must pass. Format the code and make exactly one commit.

## WHERE
- `src/mcp_coder/workflows/create_pr/core.py` — `run_create_pr_workflow`
- `tests/workflows/create_pr/test_workflow.py`
- `tests/workflows/create_pr/test_failure_handling.py`, `tests/workflows/test_create_pr_integration.py`
  (`TestWorkflowMainFunction`) — patch the new call

## WHAT
```python
def run_create_pr_workflow(...) -> int:   # signature unchanged
    cached_issue_number = validate_branch_issue_linkage(project_dir)

    def phase_a() -> int: ...   # today's body(), minus the label update at the end
    def phase_b() -> int: ...   # new

    rc = run_guarded(phase_a, ..., general_category="pr_creating_failed", issue_number=cached_issue_number)
    if rc != 0:
        return rc
    return run_guarded(phase_b, ..., general_category="pr_created", issue_number=cached_issue_number)
```
`issue_number` for the second call is read after phase A returned, so a value found by `_resolve_issue_from_pr` is used.

## ALGORITHM (phase_b)
```
branch = get_current_branch_name(project_dir)   # None -> log error, label = "pr_created"
label = run_post_creation(project_dir, branch)
if update_issue_labels and cached_issue_number:
    update_workflow_label(IssueManager(project_dir), from_label_id="pr_creating", to_label_id=label, validated_issue_number=cached_issue_number)
else: logger.log(OUTPUT, "Post-creation outcome: %s (label not updated)", label)
log completion; return 0
```

## HOW
- Remove the old "Update GitHub issue label" block from phase A (pr_creating → pr_created). Phase A now ends after the
  closing-references fallback with `return 0`; keep the "completed with warnings" log in phase B.
- Move the `IssueManager` import to module top level (it was a local import) so tests can patch it.
- Label-update failures stay non-blocking (log, still return 0), as today.
- `workflow_title` stays `"PR Creation"` for both guards.
- Update the docstring "Returns"/"Note" sections: exit 0 for every handled phase B outcome (10/74/81);
  phase A crash → `pr_creating_failed`; phase B crash → comment + `pr_created`.
- Rewrite the stale comment above `cached_issue_number` ("Cache branch-issue linkage BEFORE PR creation"): linkage still
  usually resolves after creation via open closing PRs; `None` only when the branch lacks the issue prefix, the PR has
  no closing reference, or the lookup fails — the closing-references fallback covers the first case.
- Phase B always runs, also with `update_issue_labels=False`.
- Keep `phase_b` a thin closure (branch lookup, `run_post_creation`, label/log); all decision logic stays in
  `post_creation.py`. Removing the old label block should leave `core.py` roughly flat; confirm with
  `check_file_size(max_lines=750)` — if it is over, move code into `create_pr/pre_creation.py` / `post_creation.py`,
  never into an allowlist entry.

## Tests (write first)
Patch `run_post_creation`, `update_workflow_label`, `IssueManager` at `mcp_coder.workflows.create_pr.core.*`, plus the
existing phase A patches.
- `run_post_creation` → `"pr_created"` / `"pr_merge_conflict"` / `"failing_ci"`: exit 0, `update_workflow_label`
  called with `("pr_creating", <label>)` and the issue number.
- `update_issue_labels=False` → `run_post_creation` called, `update_workflow_label` not called, exit 0.
- Phase A failure (e.g. prerequisites) → exit 1, `run_post_creation` not called.
- Phase A raises → `handle_workflow_failure` category `pr_creating_failed`; phase B not run.
- `run_post_creation` raises → netted with category `pr_created`, exit 1 (run_guarded's netted return) and a crash comment.
  Patch `mcp_coder.workflow_utils.failure_handling.handle_workflow_failure` and assert `failure.category == "pr_created"`.
- Linkage returns `None`, `_resolve_issue_from_pr` returns 9 → final label and phase B crash label both use issue 9.
- Update `test_workflow_complete_success` and similar tests to patch `run_post_creation`.
- Patch `mcp_coder.workflows.create_pr.core.run_post_creation` in every test that calls `run_create_pr_workflow` in
  `tests/workflows/create_pr/test_failure_handling.py` and in `TestWorkflowMainFunction`
  (`tests/workflows/test_create_pr_integration.py`), next to the step 7 `_rebase_if_needed` patch. No real
  `PullRequestManager`, mergeable poll or CI poll may run. The success test there (~line 422) expects exit 0 with
  `run_post_creation` returning `"pr_created"`.

## DATA
Exit code `int`.
