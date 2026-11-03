# Step 5 — `auto_merge` flag resolution + create-pr wiring

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **only** `pr_info/steps/step_5.md`.
> Steps 2–4 are done: `run_post_creation` returns an exit code, and
> `workflow_steps/merge.py` provides `is_real_green`, `run_auto_merge`, `finish_auto_merge`.
> Follow TDD: tests first, then code. Keep new logic out of `create_pr/core.py`.
> Run format, pylint, mypy, lint-imports, pytest (fast unit set, `-n auto`) and
> `check_file_size`; make them pass. Produce exactly one commit.

## WHERE

- `src/mcp_coder/utils/user_config.py` — `"auto_merge": FieldDef(bool)` right after `auto_review_implementation`
- `src/mcp_coder/cli/utils.py` — `resolve_auto_merge` (+ `__all__`)
- `src/mcp_coder/cli/workflow_parsers.py` — `add_auto_merge_arg`, used by `add_create_pr_parser`
- `src/mcp_coder/cli/commands/create_pr.py` — pass `auto_merge=`
- `src/mcp_coder/workflows/create_pr/core.py` — `run_create_pr_workflow(..., auto_merge: bool = False)`; `phase_b` forwards it plus `post_issue_comments`
- `src/mcp_coder/workflows/create_pr/post_creation.py`
- Tests: `tests/cli/test_workflow_parsers.py`, `tests/cli/test_utils.py`
  (where `resolve_issue_interaction_flags` is tested; add the `resolve_auto_merge` tests there), `tests/cli/commands/test_create_pr.py`,
  `tests/workflows/create_pr/test_post_creation.py`; schema test in `tests/utils/` if one lists repo keys

## WHAT

```python
# cli/utils.py
def resolve_auto_merge(args: argparse.Namespace, project_dir: Path) -> bool:
    """CLI --auto-merge/--no-auto-merge if given, else config auto_merge, else False."""
    cli_value: bool | None = getattr(args, "auto_merge", None)
    return cli_value if cli_value is not None else get_repo_flag(project_dir, "auto_merge")

# workflow_parsers.py
def add_auto_merge_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--auto-merge", action=argparse.BooleanOptionalAction, default=None,
        help="Squash-merge the PR once CI is green on HEAD (default: from config, else off)")

# post_creation.py
def run_post_creation(project_dir, branch, provider, mcp_config=None, settings_file=None, *,
                      issue_number: int | None, update_issue_labels: bool,
                      post_issue_comments: bool = False, auto_merge: bool = False) -> int: ...
def _check_mergeability_and_ci(project_dir, branch, head_before) -> tuple[str, str | None]: ...
```

## ALGORITHM — `run_post_creation`

```
head_before = get_latest_commit_sha(project_dir)
label, verified_sha = _check_mergeability_and_ci(project_dir, branch, head_before)
if HEAD moved: refresh_pr_description(...)           # unchanged, before the merge
if auto_merge and label == "pr_created" and verified_sha:
    outcome = run_auto_merge(project_dir, branch, verified_sha=verified_sha)
    return finish_auto_merge(project_dir, outcome, from_label_id="pr_creating", issue_number=issue_number,
                             update_issue_labels=update_issue_labels, post_issue_comments=post_issue_comments)
if auto_merge and label == "pr_created" and not verified_sha:
    logger.warning("Auto-merge skipped: CI not verified green on HEAD; keeping pr-created")
return apply_post_creation_label(project_dir, label, issue_number=..., update_issue_labels=...)
```

`_check_mergeability_and_ci`: every early return becomes `(label, None)`; the final part:
```
ci_status, ci_ok = _poll_for_ci_completion(ci_manager, branch, expected_sha=expected_sha)
if ci_status is not None and not ci_ok: return "failing_ci", None
return "pr_created", (expected_sha if is_real_green(ci_status, ci_ok, expected_sha) else None)
```

## HOW

- `get_repo_flag` is imported in `cli/utils.py` from `mcp_coder.utils.repo_config`.
- `cli/commands/create_pr.py`: `auto_merge = resolve_auto_merge(args, project_dir)`; pass it
  as keyword to `run_create_pr_workflow`.
- In `core.py` only the parameter, its docstring line and the forwarding change (≈ 5 lines).

## Tests

- Parser: `create-pr --auto-merge` → True, `--no-auto-merge` → False, absent → None.
- `resolve_auto_merge`: CLI True/False wins over config; None → `get_repo_flag` value
  (patch `mcp_coder.cli.utils.get_repo_flag`).
- `test_create_pr.py`: `auto_merge` is forwarded.
- `test_post_creation.py`: real green + `auto_merge=True` → `run_auto_merge` called with
  `verified_sha`, after `refresh_pr_description` (order mock), result of `finish_auto_merge`
  returned; `auto_merge=False` → helper not called; soft pass / green with mismatching
  `commit_sha` → helper not called, `pr_created`; soft pass + `auto_merge=True` → the
  "Auto-merge skipped" warning is logged (`caplog`) and `pr_created` is applied; `failing_ci` / `pr_merge_conflict` →
  helper not called.

## Done when

`create-pr --auto-merge` merges on a real green; with the flag off behaviour is that of step 2.
