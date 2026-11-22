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

### Step 1: Shared `LLMAuthError` type
See [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, lint-imports, format, file size) — fix all issues
- [x] Commit message prepared

### Step 2: Pure failure-message builder (`build_cli_failure`)
See [step_2.md](./steps/step_2.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, format, file size) — fix all issues
- [x] Commit message prepared

### Step 3: Streaming core — error event from the `result` message, no double print, fixture
See [step_3.md](./steps/step_3.md)

- [x] Implementation (fixture + tests + production code)
- [x] Quality checks (pylint, pytest, mypy, format, file size) — fix all issues
- [x] Commit message prepared

### Step 4: `ask_claude_code_cli` raises `LLMAuthError`; clamp the return code
See [step_4.md](./steps/step_4.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, format, file size) — fix all issues
- [x] Commit message prepared

### Step 5: Display — `prompt.py` and verify use `summarize_exception`
See [step_5.md](./steps/step_5.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, format, file size) — fix all issues
- [x] Commit message prepared

### Step 6: `llm_failure_reason` → `auth`; create-plan `.get`; review "Auth" category
See [step_6.md](./steps/step_6.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, format, file size) — fix all issues
- [x] Commit message prepared

### Step 7: Implement — auth at the task call, fix turn and final check
See [step_7.md](./steps/step_7.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, format, file size) — fix all issues
- [x] Commit message prepared

### Step 8: Implement — auth at finalisation and the CI step
See [step_8.md](./steps/step_8.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, format, file size) — fix all issues
- [x] Commit message prepared

### Step 9: Shared CI step re-raises auth; fix-ci catches it; review CI gate
See [step_9.md](./steps/step_9.md)

- [x] Implementation (tests + production code)
- [x] Quality checks (pylint, pytest, mypy, format, file size — `ci.py` ≤ 750 lines) — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the base branch and address findings
- [ ] PR summary prepared
