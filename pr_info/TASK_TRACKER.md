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

### Step 1: Annotate `MLflowLogger.__init__` return type ([details](./steps/step_1.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Shared scripted `BaseChatModel` test double ([details](./steps/step_2.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Shared import-fallback command stub ([details](./steps/step_3.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Annotate the icoder mock/stub-callable sites ([details](./steps/step_4.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Annotate `make_copilot_jsonl_output` usages ([details](./steps/step_5.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Annotate `_RaisingAsyncIter.__init__` ([details](./steps/step_6.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Enable ruff `ANN` (excluding `ANN401`) ([details](./steps/step_7.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Review full diff against all steps
- [ ] Write PR summary
