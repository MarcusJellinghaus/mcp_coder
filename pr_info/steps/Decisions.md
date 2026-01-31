# Decisions from Plan Review Discussion

## Decision 1: Code Reuse from `gh_tool.py`
**Choice:** Extract & Reuse

Extract the detection helpers (`_detect_from_pr()`, `_detect_from_issue()`, `_detect_default_branch()`) from `gh_tool.py` into `base_branch.py` as **private functions**. Only `detect_base_branch()` is the public API.

`gh_tool.py` becomes a thin wrapper that calls `detect_base_branch()` and maps results to exit codes:
- Result is branch name → print it, exit 0
- Result is "unknown" → exit 1  
- Exception → exit 2

**Rationale:** Clean code first - detection logic in one place (DRY), CLI command only handles CLI concerns.

---

## Decision 2: Unknown Base Branch Display Format
**Choice:** Plain text

Display unknown as plain text: `Base Branch: unknown`

---

## Decision 3: Test File Location
**Choice:** Move tests

Move detection-related tests from `test_gh_tool.py` to `test_base_branch.py`, keeping only CLI-specific tests in the original file.

---

## Decision 4: Issue Data Parameter
**Choice:** Add `current_branch` parameter

Function signature becomes:
```python
def detect_base_branch(
    project_dir: Path,
    current_branch: Optional[str] = None,
    issue_data: Optional[IssueData] = None,
) -> str:
```

**Rationale:** Avoids redundant git call when branch is already known by caller.

---

## Decision 5: Refactoring `_get_rebase_target_branch()`
**Choice:** Use full detection

Use full detection (including issue-based) for `_get_rebase_target_branch()` in `implement/core.py`.

**Rationale:** More accurate rebasing by respecting issue's `### Base Branch` section.

---

## Decision 6: `_collect_github_label()` Signature
**Choice:** Replace `branch_name` with `issue_data`

Simplify the function signature by replacing the `branch_name` parameter with `issue_data`:
```python
def _collect_github_label(
    project_dir: Path,
    issue_data: Optional[IssueData] = None,
) -> str:
```

**Rationale:** Cleaner - if we have `issue_data`, we already have the labels; no need for `branch_name` separately.

---

## Decision 7: `_get_rebase_target_branch()` Optimization
**Choice:** Accept as-is (no optimization)

Keep the simple implementation that doesn't pass `issue_data`:
```python
def _get_rebase_target_branch(project_dir: Path) -> Optional[str]:
    result = detect_base_branch(project_dir)
    return None if result == "unknown" else result
```

**Rationale:** One extra API call is acceptable for simplicity; this function is only called once per workflow execution.

---

## Decision 8: Test Coverage for Issue Data Reuse
**Choice:** Skip explicit test

Do not add an explicit test verifying that `issue_data` is reused (no duplicate API call).

**Rationale:** The behavior is implicitly covered by existing test structure.
