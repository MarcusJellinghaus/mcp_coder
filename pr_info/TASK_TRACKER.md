# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Create conftest.py + two smaller test files
[Detail](./steps/step_1.md)

Create shared `conftest.py` and extract `TestExtractPrsByStates`, `TestSearchBranchesByPattern` into their own files.

- [x] Implementation: create `conftest.py`, `test_extract_prs_by_states.py`, `test_search_branches_by_pattern.py` with verbatim code moves and adjusted imports
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `refactor: extract conftest and smaller test classes from test_branch_resolution`

### Step 2: Create test_get_branch_with_pr_fallback.py and delete original
[Detail](./steps/step_2.md)

Extract `TestGetBranchWithPRFallback` into its own file, then delete `test_branch_resolution.py`.

- [ ] Implementation: create `test_get_branch_with_pr_fallback.py` with verbatim code move, delete `test_branch_resolution.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `refactor: complete split of test_branch_resolution.py (#539)`

## Pull Request

- [ ] Review all changes across both steps for correctness
- [ ] Write PR summary describing the refactoring
