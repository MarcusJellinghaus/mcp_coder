# Step 6a: Workflow cores — rename params and add post_issue_comments

## References
- See `pr_info/steps/summary.md` for overall architecture and design changes

## WHERE

### Source files (3 files):
- `src/mcp_coder/workflows/implement/core.py` — rename param + add param
- `src/mcp_coder/workflows/create_pr/core.py` — rename param + add param
- `src/mcp_coder/workflows/create_plan.py` — rename param + add param

### Test files (4 files):
- `tests/workflows/implement/test_core.py`
- `tests/workflows/create_pr/test_workflow.py`
- `tests/workflows/create_pr/test_failure_handling.py`
- `tests/workflows/create_plan/test_main.py`

## WHAT

### Workflow function signature changes

**`run_implement_workflow()`:**
```python
def run_implement_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    execution_dir: Optional[Path] = None,
    update_issue_labels: bool = False,    # renamed from update_labels
    post_issue_comments: bool = False,     # NEW
) -> int:
```
- All internal calls to `handle_workflow_failure()` pass both flags
- Success-path label update uses `update_issue_labels`

**Internal wrapper `_handle_workflow_failure` (~line 160):** This wrapper accepts `update_labels` and
forwards it to the shared `handle_workflow_failure`. It MUST be renamed to `update_issue_labels` and
gain `post_issue_comments: bool = False`. There are ~10 call sites inside `run_implement_workflow`
that all pass `update_labels=update_labels` — each must be updated to pass both flags.

**`run_create_pr_workflow()`:**
```python
def run_create_pr_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    execution_dir: Optional[Path] = None,
    update_issue_labels: bool = False,    # renamed from update_labels
    post_issue_comments: bool = False,     # NEW
) -> int:
```
- All internal calls to `_handle_create_pr_failure()` pass both flags
- Success-path label update uses `update_issue_labels`

**Internal call sites in `run_create_pr_workflow`:** ~8 calls to `_handle_create_pr_failure` pass
`update_labels=update_labels` — all must be updated to `update_issue_labels` and add
`post_issue_comments`. The success-path label check (`if update_labels:`) must also be renamed.

**`run_create_plan_workflow()`:**
```python
def run_create_plan_workflow(
    issue_number: int,
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
    update_issue_labels: bool = False,    # renamed from update_labels
    post_issue_comments: bool = False,     # NEW
) -> int:
```
- Success-path label update uses `update_issue_labels`
- Note: `create_plan` doesn't currently use `handle_workflow_failure()` — `post_issue_comments` is accepted but not used internally yet (future-proofing the interface)

## HOW
- Rename `update_labels` parameter to `update_issue_labels` in all workflow function signatures
- Add `post_issue_comments: bool = False` parameter to all workflow function signatures
- Update all internal call sites to pass both flags

## ALGORITHM
No new algorithm — parameter renaming and wiring.

## DATA
- **Workflow functions:** accept and forward both flags to failure handlers and success-path label updates

## TESTS

### Update workflow tests:

In `test_core.py` (implement), `test_workflow.py` (create_pr), `test_main.py` (create_plan):
- Rename `update_labels=...` kwargs to `update_issue_labels=...`
- Add `post_issue_comments=...` where failure handling is tested
- Verify both flags reach `handle_workflow_failure` / `_handle_create_pr_failure`

In `test_failure_handling.py` (create_pr):
- Update `run_create_pr_workflow(update_labels=...)` calls to use `update_issue_labels=...`
- Update `call_kwargs["update_labels"]` assertions to use `call_kwargs["update_issue_labels"]`
- Add `post_issue_comments` parameter where failure handling is tested

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_6.md.

Implement Step 6a: rename update_labels to update_issue_labels in all workflow functions
and add post_issue_comments parameter.

1. Update tests FIRST:
   - tests/workflows/implement/test_core.py — rename update_labels → update_issue_labels, add post_issue_comments
   - tests/workflows/create_pr/test_workflow.py — same
   - tests/workflows/create_plan/test_main.py — same

2. Modify source files:
   - src/mcp_coder/workflows/implement/core.py — rename param + add param + update ~10 internal call sites
   - src/mcp_coder/workflows/create_pr/core.py — rename param + add param + update ~8 internal call sites
   - src/mcp_coder/workflows/create_plan.py — rename param + add param

3. Run all code quality checks (pylint, pytest, mypy)
4. Fix any issues until all checks pass
```

## COMMIT MESSAGE
```
feat: rename update_labels to update_issue_labels in all workflows (#661)

- Rename update_labels → update_issue_labels in all workflow functions
- Add post_issue_comments parameter to all workflow functions  
- Update internal wrappers and all call sites
- All failure handlers receive both flags
```
