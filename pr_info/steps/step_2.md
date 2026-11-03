# Step 2 — `74` exits 1 everywhere; phase B final label moves into `post_creation.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **only** `pr_info/steps/step_2.md`.
> Follow TDD: flip / add the tests first, then change the code.
> No auto-merge logic in this step. Run format, pylint, mypy, pytest (fast unit set,
> `-n auto`) and make them pass. Produce exactly one commit.

## WHERE

- `src/mcp_coder/workflows/create_pr/post_creation.py`
- `src/mcp_coder/workflows/create_pr/core.py` (`phase_b`, `run_create_pr_workflow` docstring)
- `src/mcp_coder/workflows/fix_conflict/core.py`
- Tests: `tests/workflows/create_pr/test_post_creation.py`,
  `tests/workflows/create_pr/test_workflow_labels.py`,
  `tests/workflows/fix_conflict/test_core.py`

## WHAT

```python
# post_creation.py
def run_post_creation(
    project_dir: Path,
    branch: str,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    *,
    issue_number: int | None,
    update_issue_labels: bool,
) -> int: ...

def apply_post_creation_label(
    project_dir: Path,
    label: str,
    *,
    issue_number: int | None,
    update_issue_labels: bool,
) -> int: ...
```

`run_post_creation` computes the label exactly as today, then returns
`apply_post_creation_label(...)`.

## ALGORITHM — `apply_post_creation_label`

```
rc = 0
if update_issue_labels and issue_number:
    rc = apply_final_label(project_dir, "pr_creating", label, issue_number)   # log "✓ Issue label updated" on 0
else:
    warn "Skipping label update: branch was not linked to an issue" if update_issue_labels
    log "Post-creation outcome: <label> (label not updated)"
log completion line as today (error / "with warnings" / "successfully")
return rc or (1 if label == "pr_merge_conflict" else 0)
```

This is the existing `phase_b` body moved verbatim, plus the last line.

## HOW

- `core.py` `phase_b` becomes:
  ```python
  branch = get_current_branch_name(project_dir)
  if branch is None:
      logger.error("Could not determine current branch; skipping PR checks")
      return apply_post_creation_label(project_dir, "pr_created", issue_number=cached_issue_number, update_issue_labels=update_issue_labels)
  return run_post_creation(project_dir, branch, provider, mcp_config, settings_file, issue_number=cached_issue_number, update_issue_labels=update_issue_labels)
  ```
  Remove the now-unused `apply_final_label` import from `core.py` if nothing else uses it.
  Update the `run_create_pr_workflow` docstring: exit 1 also when phase B ends on `74`.
- `fix_conflict/core.py`: in `body()`, `if verdict: _fail(...); return 1`. Update the
  `run_fix_conflict_workflow` docstring ("0 on status-10, 1 on status-74 …").
- Tests that patch `apply_final_label` for phase B must now patch it at
  `mcp_coder.workflows.create_pr.post_creation.apply_final_label`.
- `test_post_creation.py`: `run_post_creation` now returns an int. Keep the label assertions by
  patching `apply_post_creation_label` (or `apply_final_label`) and asserting the label it
  received; add tests: `pr_merge_conflict` → 1, `failing_ci` / `pr_created` → 0,
  label write failure → 1, `update_issue_labels=False` + `pr_merge_conflict` → 1.
- `test_workflow_labels.py` / `fix_conflict/test_core.py`: flip the `74` exit-code asserts 0 → 1.

## DATA

Return value: exit code `int` (0 / 1).

## Done when

create-pr and fix-conflict exit 1 on `74` regardless of `update_issue_labels`; all other
outcomes unchanged; `core.py` is shorter than before.
