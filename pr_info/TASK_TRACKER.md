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

### Step 1: Move shared helpers into `conftest.py`

Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code): move `_build_assessment` and `mock_status_checks` into `conftest.py`; update `test_status_display.py` to import `_build_assessment`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Extract `TestStatusAssessmentConsumer`

Detail: [step_2.md](./steps/step_2.md)

- [x] Implementation (tests + production code): create `test_status_display_assessment_consumer.py`; remove class from original
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Extract `TestClosedIssuePrefixDisplay`

Detail: [step_3.md](./steps/step_3.md)

- [x] Implementation (tests + production code): create `test_status_display_closed_prefix.py`; remove class from original
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Extract the delete-action classes

Detail: [step_4.md](./steps/step_4.md)

- [x] Implementation (tests + production code): create `test_status_display_delete_actions.py` with the three delete-action classes; remove them from original
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: Extract `TestDisplayStatusTableBranchIndicators`

Detail: [step_5.md](./steps/step_5.md)

- [x] Implementation (tests + production code): create `test_status_display_branch_indicators.py`; remove class from original
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 6: Extract `TestZombieSessionDisplay`

Detail: [step_6.md](./steps/step_6.md)

- [x] Implementation (tests + production code): create `test_status_display_zombie.py`; remove class from original
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 7: Extract `TestScenarioACrossModule`, drop allowlist entry, final verify

Detail: [step_7.md](./steps/step_7.md)

- [x] Implementation (tests + production code): create `test_status_display_scenario.py`; remove class from original; remove `test_status_display.py` entry from `.large-files-allowlist`; verify `check_file_size` and `compact-diff`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] Review full branch diff via `compact-diff` — confirm only import changes and new/deleted file headers appear
- [ ] Write PR summary
