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

### Step 1: Move `TestStripClaudeFooters` to `test_commit_operations_parsing.py`
See [step_1.md](./steps/step_1.md)

- [x] Implementation: record collect-only counts, `move_symbol` `TestStripClaudeFooters` (dry run, then apply), fix imports, remove `tests/workflow_utils/test_commit_operations.py` from `.large-files-allowlist`, verify counts (40 → 19 + 21)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Move `TestParseLLMCommitResponse` from `test_commit.py` to `test_commit_operations_parsing.py`
See [step_2.md](./steps/step_2.md)

- [x] Implementation: check precondition, record counts, `move_symbol` `TestParseLLMCommitResponse` (dry run, then apply), fix imports, verify counts (`test_commit.py` 44 → 40, parsing 21 → 25)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Move `generate_commit_message_with_llm` classes to `test_commit_operations_default_args.py`
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: record counts, `move_symbol` `TestGenerateCommitMessageWithLLM` + `TestGenerateCommitMessageWithLLMExtended` from `test_commit.py` (dry run, then apply), fix imports, verify counts (`test_commit.py` 40 → 30, default_args 10)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Move push tests from `test_commit.py` to `test_commit_push.py`
See [step_4.md](./steps/step_4.md)

- [ ] Implementation: record counts, `move_symbol` `MODULE` then `TestPushAfterCommit` + `TestCommitAutoPush` (dry run, then apply), verify order/no cross-imports, fix imports, remove `tests/cli/commands/test_commit.py` from `.large-files-allowlist`, update `vulture_whitelist.py:136` comment, verify end-state counts (18/12/19/25/10 = 84)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: verify compact diff shows only moves, import lines, allowlist and whitelist changes; all checks pass
- [ ] PR summary prepared
