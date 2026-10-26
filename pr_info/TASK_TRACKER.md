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

### Step 1: Move shared stream-mock helpers into `conftest.py`

See [step_1.md](./steps/step_1.md)

- [x] Implementation: move `_MockStreamResult` and `_make_stream_gen` to `conftest.py` via `move_symbol` (dry run first) and normalize imports; collected test counts match baseline
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Move `TestAskClaudeCodeCliStream` to `test_claude_code_cli_streaming.py`

See [step_2.md](./steps/step_2.md)

- [ ] Implementation: move `TestAskClaudeCodeCliStream` to the new file via `move_symbol` (dry run first), normalize imports in both files, remove the `.large-files-allowlist` entry; collected counts 30 + 9, directory total matches baseline
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff and confirm it contains only moves, import changes and the allowlist removal
- [ ] PR summary prepared, stating whether the `claude_cli_integration` tests were run or skipped and why
