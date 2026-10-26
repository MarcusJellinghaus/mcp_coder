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

### Step 1: Baseline + move fixtures to `conftest.py`
See [step_1.md](./steps/step_1.md)
- [x] Implementation: record baseline counts, move `icoder_app` / `make_icoder_app` to `tests/icoder/conftest.py`, fix imports
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Streaming tests → `test_app_pilot_streaming.py`
See [step_2.md](./steps/step_2.md)
- [ ] Implementation: moves 2a–2e (incl. `ErrorAfterChunksLLMService`), fix imports, add `pytestmark`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Cancel tests → `test_app_pilot_cancel.py`
See [step_3.md](./steps/step_3.md)
- [ ] Implementation: moves 3a, 3a' (`SlowLLMService`), fix imports, add `import pytest` + `pytestmark`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Content-unit tests → `test_app_pilot_content_units.py`
See [step_4.md](./steps/step_4.md)
- [ ] Implementation: moves 4a, 4a' (`_make_click_tool_unit`), 4b, 4c, fix imports, add `pytestmark`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Approval tests → `test_app_pilot_approval.py`
See [step_5.md](./steps/step_5.md)
- [ ] Implementation: moves 5a–5e, delete stale `_LONG_CMD` import, fix imports, add `pytestmark`, verify 6 shared helpers remain in base file
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Approval-persist tests → `test_app_pilot_approval_persist.py`
See [step_6.md](./steps/step_6.md)
- [ ] Implementation: moves 6a, 6b', 6b'', 6c, delete stale `_UNPARSEABLE_TOOL` import, fix imports, add `pytestmark`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Shutdown tests → `test_app_pilot_shutdown.py`
See [step_7.md](./steps/step_7.md)
- [ ] Implementation: moves 7a, 7a' (`_ApprovalPendingLLMService`), 7b (`_QUIT_TIMEOUT`), delete stale `_QUIT_TIMEOUT` import, fix imports, add `pytestmark`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: Banner cleanup, allowlist removal, final verification
See [step_8.md](./steps/step_8.md)
- [ ] Implementation: delete the 11 stale banners, remove `tests/icoder/test_app_pilot.py` from `.large-files-allowlist`, run full verification
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: compact diff against base branch shows only moves, import changes, `pytestmark` lines, deleted banners and the allowlist line
- [ ] PR summary prepared
