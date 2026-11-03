# Step 6 — fix-ci wiring

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **only** `pr_info/steps/step_6.md`.
> `workflow_steps/merge.py` (`resolve_merge_issue_number`, `run_auto_merge`,
> `finish_auto_merge`), `resolve_auto_merge` and `add_auto_merge_arg` already exist.
> Follow TDD: tests first, then code. Run format, pylint, mypy, pytest (fast unit set,
> `-n auto`); make them pass. Produce exactly one commit.

## WHERE

- `src/mcp_coder/cli/workflow_parsers.py` — call `add_auto_merge_arg(fix_ci_parser)`
- `src/mcp_coder/cli/commands/fix_ci.py` — `auto_merge = resolve_auto_merge(args, project_dir)`, pass as keyword
- `src/mcp_coder/workflows/fix_ci/core.py`
- Tests: `tests/cli/test_workflow_parsers.py`, `tests/cli/commands/test_fix_ci.py`,
  `tests/workflows/fix_ci/test_core.py`

## WHAT

```python
def run_fix_ci_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
    auto_merge: bool = False,
) -> int: ...
```

## ALGORITHM — `ci_ok` branch in `body()`

```
_refresh_if_pushed()                                  # unchanged, before the merge
if ci_ok:
    if auto_merge:
        issue_number = resolve_merge_issue_number(project_dir, branch)
        outcome = run_auto_merge(project_dir, branch)
        return finish_auto_merge(project_dir, outcome, from_label_id="fixing_ci", issue_number=issue_number,
                                 update_issue_labels=update_issue_labels, post_issue_comments=post_issue_comments)
    ...existing pr_created path unchanged...
```

## HOW

Import the three functions from `mcp_coder.workflow_steps.merge`. Update the docstring
(`Returns:` — with `auto_merge`, exit follows the merge outcome).

## Tests

- Parser accepts `--auto-merge` on `fix-ci`; command forwards it.
- `ci_ok=True, auto_merge=True`: `resolve_merge_issue_number` called before `run_auto_merge`;
  `finish_auto_merge` called with `from_label_id="fixing_ci"` and the resolved issue number;
  its return value is the exit code; `apply_final_label` not called directly.
- `auto_merge=False`: unchanged behaviour (existing tests stay green).
- `ci_ok=False`: helper not called.

## Done when

`fix-ci --auto-merge` merges after a green fix loop; flag off unchanged.
