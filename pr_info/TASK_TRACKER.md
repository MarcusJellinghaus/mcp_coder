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

### Step 1: Pair `EventLog` with a plain-text `.txt` sidecar

Details: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code): add six TDD tests in `tests/icoder/test_event_log.py`, then implement `_chat_path_for`, `_try_open_chat`, `_chat_file`, `write_chat`, `current_chat_path`, paired rotation, and paired close in `src/mcp_coder/icoder/core/event_log.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared (`iCoder: pair EventLog with plain-text chat sidecar (#982)`)

### Step 2: Add `mirror` callback to `OutputLog`

Details: [step_2.md](./steps/step_2.md)

- [ ] Implementation (tests + production code): add four TDD tests in `tests/icoder/ui/test_output_log.py`, then add `mirror` parameter and the three `self._mirror(...)` call sites in `src/mcp_coder/icoder/ui/widgets/output_log.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared (`iCoder: add mirror callback to OutputLog (#982)`)

### Step 3: Wire the mirror in `ICoderApp`, prove end-to-end, document

Details: [step_3.md](./steps/step_3.md)

- [ ] Implementation (tests + production code + docs): add `test_chat_txt_mirrors_visible_conversation` in `tests/icoder/test_app_pilot.py`, wire `mirror=self._core.event_log.write_chat` in `ICoderApp.compose()` in `src/mcp_coder/icoder/ui/app.py`, append the "Log files" note to `docs/icoder/icoder.md`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared (`iCoder: mirror conversation to plain-text chat log (#982)`)

## Pull Request

- [ ] PR review (self-review diff, verify all step commits are clean and scoped, confirm CI is green)
- [ ] PR summary (write description referencing issue #982, summarize the three commits and end-to-end behavior)
