# Step 2: `mcp-coder rebase` trusts an issue-named base and checks it exists

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`. Step 1 (`detect_base_branch_with_source`, `BaseBranchSource`, `check_base_branch_on_origin`) is already in place. Write the tests first, then the code. Run pylint, pytest (unit tests, `-n auto`) and mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/workflows/rebase.py`
- `tests/workflows/rebase/test_guards.py`
- `tests/workflows/rebase/test_workflow.py`

## WHAT

```python
def _resolve_base_branch(
    project_dir: Path, base_branch_arg: str | None
) -> tuple[str | None, str | None]: ...  # signature unchanged
```

`run_rebase_workflow` gains one guard call.

## HOW

- Replace the import of `detect_base_branch` with `BaseBranchSource`, `check_base_branch_on_origin`, `detect_base_branch_with_source` from `mcp_coder.workflow_utils.base_branch`.
- In `run_rebase_workflow`, after `fetch_remote(...)` and before `_check_pr_info_absent_on_base`:
  ```python
  missing_err = check_base_branch_on_origin(project_dir, base)
  if missing_err:
      logger.error("Base-branch guard failed: %s", missing_err)
      return 2
  ```
  This applies to an explicit `--base-branch` too.
- Update the `_resolve_base_branch` docstring (issue-named bases are accepted).

## ALGORITHM

```
_resolve_base_branch(project_dir, arg):
    if arg: return (arg, None)
    detected = detect_base_branch_with_source(project_dir)
    if detected is None: return (None, "Could not detect base branch; pass --base-branch")
    branch, source = detected
    if source is ISSUE or branch in _STANDARD_BASES: return (branch, None)
    return (None, f"Base '{branch}' was detected from {source.value}, not named in the issue; "
                  "add '### Base Branch' to the issue or pass --base-branch")
```

## DATA

`(base, None)` or `(None, error)` as today. `run_rebase_workflow` returns `2` on a missing base.

## Tests (write first)

`test_guards.py::TestResolveBaseBranch` — monkeypatch `detect_base_branch_with_source` instead of `detect_base_branch`:
- explicit arg wins; detection not called (existing test, retargeted).
- `("main", DEFAULT)` → accepted.
- `("epic/x", ISSUE)` → accepted (new).
- `("develop", PR)` and `("develop", MERGE_BASE)` → rejected, error mentions `--base-branch` and `### Base Branch` (parametrized; replaces `test_non_standard_detected_errors`).
- `None` → rejected with `--base-branch`.

`test_workflow.py`:
- In the `patched` fixture, add `monkeypatch.setattr(rebase_module, "check_base_branch_on_origin", lambda _pd, _b: None)`.
- New test: the check returns an error → `_run` returns `2`, `_check_pr_info_absent_on_base` is not reached (patch it with a `MagicMock` and assert not called), no LLM call.
- Update the message in `test_non_standard_base_without_arg_returns_2` to the new wording (cosmetic).
