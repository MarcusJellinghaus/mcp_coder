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

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

### Step 1: E741 — rename `l` → `label` in `define_labels.py`

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: E741 — rename `l` → `line` across 8 test files

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: E741 — rename inner `l` → `entry` in `test_label_config.py`

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: E721 — use `is` for type-literal comparisons in `test_types.py`

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: E402 — file-level suppression in `main.py`

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Enable ruff `E`, exclude `E501`, in `pyproject.toml`

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Review full diff against `pr_info/steps/summary.md`
- [ ] Write PR summary
