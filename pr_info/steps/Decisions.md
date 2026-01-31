# Decisions from Plan Review Discussion

## Decision 1: Code Reuse from `gh_tool.py`
**Choice:** Extract & Reuse

Extract the detection helpers (`_detect_from_pr()`, `_detect_from_issue()`, `_detect_default_branch()`) from `gh_tool.py` into `base_branch.py`, then have both `gh_tool.py` and `branch_status.py` import from there.

**Rationale:** Single source of truth, avoids code duplication.

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
