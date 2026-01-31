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

### Step 1: Tests for `gh-tool get-base-branch` Command
- [x] All detection priority scenarios tested (PR → Issue → Default) - [step_1.md](./steps/step_1.md)
- [x] All exit codes tested (0, 1, 2)
- [x] Output format tested (stdout only, no extra text)
- [x] CLI integration tested (command registered, help works)
- [x] Exit codes in --help epilog tested
- [x] Edge cases tested (detached HEAD, no issue number in branch)

### Step 2: Implement `gh-tool get-base-branch` Command
- [x] Command registered under `mcp-coder gh-tool get-base-branch` - [step_2.md](./steps/step_2.md)
- [x] Detection priority: PR → Issue → Default
- [x] Exit codes: 0 (success), 1 (no detection), 2 (error)
- [x] Exit codes documented in `--help` epilog
- [x] Output: branch name only to stdout
- [x] All tests from Step 1 pass
- [x] Follows existing code patterns (resolve_project_dir, logging)

### Step 3: Update Slash Commands for Dynamic Base Branch
- [x] `implementation_review.md` uses dynamic base branch for diff - [step_3.md](./steps/step_3.md)
- [x] `rebase.md` uses dynamic base branch for rebase
- [x] `check_branch_status.md` text updated (no hardcoded "main")
- [x] All markdown formatting preserved
- [x] Commands remain functional with same allowed-tools

### Step 4: Update Documentation
- [x] `docs/cli-reference.md` has new `gh-tool get-base-branch` section - [step_4.md](./steps/step_4.md)
- [x] `docs/cli-reference.md` command list updated
- [x] `docs/cli-reference.md` "onto main" text fixed
- [x] `docs/configuration/claude-code.md` `/rebase` description updated
- [x] `docs/processes-prompts/claude_cheat_sheet.md` `/rebase` description updated
- [x] All markdown formatting valid
- [x] No remaining hardcoded "onto main" references in rebase contexts

## Pull Request
