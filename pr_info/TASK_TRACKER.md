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

- [x] [Step 1: `implementation_approve` skill gates on `Ready to merge`](./steps/step_1.md) — not blocked
- [x] [Step 2: Linked-branch state feeds `_exit_code`](./steps/step_2.md) — unblocked: mcp-workspace `main` now exports `LinkedBranchStatus` and `linked_branch_blocks` (observed 2026-10-18). Upstream added a seventh member `LINKED_VIA_PR` (non-blocking); covered by an extra mapping row.

## Pull Request
