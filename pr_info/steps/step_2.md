# Step 2: Move branch naming tests and update allowlist

> **Context:** See [summary.md](summary.md) for overall goal. This step moves the
> `TestBranchNameGeneration` test class to a dedicated test file and removes the allowlist entry.

## LLM Prompt

```
Implement Step 2 of issue #538 (see pr_info/steps/summary.md and pr_info/steps/step_2.md).

Move the `TestBranchNameGeneration` class from `test_issue_branch_manager.py` to a new
`test_branch_naming.py`. Update imports in the new file to point to the package.
Remove `branch_manager.py` from `.large-files-allowlist` (only if line count < 750).
Run all quality checks (pylint, pytest, mypy) after changes.
Commit with message: "refactor: move branch naming tests to test_branch_naming.py (#538)"
```

## WHERE

- **Source:** `tests/utils/github_operations/test_issue_branch_manager.py`
- **Destination:** `tests/utils/github_operations/test_branch_naming.py` (new)
- **Update:** `.large-files-allowlist`

## WHAT

Move `TestBranchNameGeneration` class (~200 lines) containing all `generate_branch_name_from_issue` tests.

The class stays exactly as-is. The new file needs:

```python
"""Unit tests for branch naming utilities."""

from mcp_coder.utils.github_operations.issues import (
    generate_branch_name_from_issue,
)

class TestBranchNameGeneration:
    # ... all test methods moved verbatim ...
```

## HOW

1. Create `tests/utils/github_operations/test_branch_naming.py` with the `TestBranchNameGeneration`
   class moved from `test_issue_branch_manager.py`. Include only the imports needed by that class.
2. Remove `TestBranchNameGeneration` from `test_issue_branch_manager.py`.
3. Remove unused imports from `test_issue_branch_manager.py` (if `generate_branch_name_from_issue`
   is no longer referenced there, drop it from the import).
4. Check `branch_manager.py` line count. If < 750, remove its entry from `.large-files-allowlist`.
5. Run format, pylint, mypy, pytest.

## DATA

- `test_branch_naming.py` imports: `pytest`, `generate_branch_name_from_issue` from the package
- `test_issue_branch_manager.py` may still import `BranchCreationResult` (used by `TestCreateRemoteBranchForIssue`) — keep that import if needed
- No `BranchCreationResult` import needed in `test_branch_naming.py` (the test class doesn't test it)

## Verification

- All tests pass (same test count, just split across two files)
- `mcp-coder check file-size --max-lines 750` passes without allowlist entry for `branch_manager.py`
- No logic changes — only file moves and import adjustments
