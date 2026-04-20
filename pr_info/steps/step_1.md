# Step 1: Create tests for corrected merge-base parent detection

> **Context**: See `pr_info/steps/summary.md` for the full issue summary.

## Goal

Create the test file for `detect_parent_branch_via_merge_base` with tests that validate the **corrected** algorithm (measuring `merge_base → current_HEAD` instead of `merge_base → candidate_HEAD`). Tests will initially fail against the current buggy code — that's expected for TDD.

## WHERE

- **Create**: `tests/utils/git_operations/__init__.py` (empty package init)
- **Create**: `tests/utils/git_operations/test_parent_branch_detection.py`

## WHAT

Tests use `unittest.mock` to patch `_safe_repo_context`, `is_git_repository`, and `get_default_branch_name`. Each test builds mock repo objects with controlled `merge_base()` and `iter_commits()` return values.

### Test classes and cases

**`TestMergeBaseDirectionFix`** — core bug fix validation:
- `test_selects_main_over_dormant_feature_branch` — The issue's exact scenario: branch created from `main`, dormant feature branch has closer candidate-HEAD distance but farther current-HEAD distance. Must select `main`.
- `test_selects_feature_branch_for_stacked_pr` — Stacked PR: branch created from feature branch. Feature branch has closer merge-base to current HEAD than `main`. Must select the feature branch.

**`TestDefaultBranchTiebreaker`**:
- `test_prefers_default_branch_on_equal_distance` — Two candidates with equal `merge_base → current_HEAD` distance. Default branch wins.

**`TestThresholdFiltering`**:
- `test_excludes_candidates_beyond_threshold` — Candidate with distance > threshold is excluded, returns `None`.
- `test_includes_candidate_at_threshold` — Candidate with distance == threshold is included.

**`TestEdgeCases`**:
- `test_returns_none_for_non_git_repo` — `is_git_repository` returns False → returns None.
- `test_returns_none_when_no_candidates_pass` — All candidates exceed threshold → returns None.
- `test_skips_current_branch` — Current branch is not considered as candidate.
- `test_distance_zero_collects_all_candidates` — Two candidates at distance=0, default branch wins (no early exit).

## HOW

Import `detect_parent_branch_via_merge_base` and `MERGE_BASE_DISTANCE_THRESHOLD` from `mcp_coder.utils.git_operations.parent_branch_detection`. Patch at the module level:
- `mcp_coder.utils.git_operations.parent_branch_detection.is_git_repository`
- `mcp_coder.utils.git_operations.parent_branch_detection._safe_repo_context`
- `mcp_coder.utils.git_operations.parent_branch_detection.get_default_branch_name` (will exist after step 2 adds the import)

## ALGORITHM (mock setup pattern)

```python
# For each test:
# 1. Create mock branch objects with .name and .commit attributes
# 2. Configure repo.heads to return branch list
# 3. Configure repo.merge_base() to return specific commit per candidate
# 4. Configure repo.iter_commits("merge_base..current_HEAD") to return N items
#    (this is the NEW direction — tests assert against new behavior)
# 5. Call detect_parent_branch_via_merge_base(project_dir, current_branch)
# 6. Assert the correct branch name is returned
```

## DATA

- Input: `project_dir: Path`, `current_branch: str`, `distance_threshold: int`
- Output: `Optional[str]` — branch name or None
- `MERGE_BASE_DISTANCE_THRESHOLD` = 20 (unchanged)

## Commit message

```
test: add tests for corrected merge-base parent detection (#803)
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Create tests/utils/git_operations/__init__.py (empty) and
tests/utils/git_operations/test_parent_branch_detection.py with the test
classes described in step_1.md.

The tests validate the CORRECTED algorithm direction (merge_base → current_HEAD).
Since step 2 will add a `get_default_branch_name` import to the source module,
the tests should patch it at the source module path:
`mcp_coder.utils.git_operations.parent_branch_detection.get_default_branch_name`

Use unittest.mock to create mock repo objects. Follow the existing test style
in tests/utils/test_git_utils.py (class-based, type hints on all methods).

Do NOT patch at `mcp_coder.utils.git_operations.branch_queries` — patch at the
module where it will be used.

After creating the files, run pylint, mypy, and pytest (unit tests only).
The tests are expected to FAIL at this point since the source code fix hasn't
been applied yet — that's correct TDD.
```
