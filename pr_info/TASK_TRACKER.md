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

### Step 1: `run_rebase_workflow` returns a structured result — [step_1.md](./steps/step_1.md)
- [x] Implementation: tests + `RebaseRunResult` returned by `run_rebase_workflow`; CLI maps to exit code
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: pytest marker filter and explicit pytest timeout — [step_2.md](./steps/step_2.md)
- [x] Implementation: tests + `markers`/`timeout_seconds` threaded to the shim; prompt placeholder
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Marker retry once per conflict stop — [step_3.md](./steps/step_3.md)
- [x] Implementation: tests + one marker-retry per conflict stop
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Least-privilege settings file shared by CLI and automated callers — [step_4.md](./steps/step_4.md)
- [x] Implementation: tests + drop `move_file`; `rebase_settings_file` context manager
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: Shared helper `rebase_with_llm_fallback` — [step_5.md](./steps/step_5.md)
- [x] Implementation: tests + `rebase_with_llm_fallback`, `llm_detail`, `git_check_ignore` re-export
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 6: Review uses the LLM fallback; hand-off shows the LLM reason — [step_6.md](./steps/step_6.md)
- [x] Implementation: tests + review wiring and `LLM rebase` field in hand-off comment
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 7: fix-conflict runs the LLM fallback — [step_7.md](./steps/step_7.md)
- [x] Implementation: tests + CLI args, workflow wiring, comment field, Jenkins templates
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 8: Label config: `status-72` and `status-74` — [step_8.md](./steps/step_8.md)
- [ ] Implementation: tests + `status-72` timeout/description, `status-74` commands
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 9: create_pr sends a still-`dirty` PR to fix-conflict — [step_9.md](./steps/step_9.md)
- [ ] Implementation: tests + still `dirty` → `merge_conflict` (status-71)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 10: implement logs the rebase outcome reason (#430) — [step_10.md](./steps/step_10.md)
- [ ] Implementation: tests + log rebase outcome reason
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 11: Documentation — [step_11.md](./steps/step_11.md)
- [ ] Implementation: update docs listed in step
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 12: Renormalize a line-ending-only dirty tree (blocked on mcp-workspace#373) — [step_12.md](./steps/step_12.md)
- [ ] Implementation: tests + line-ending-only dirt renormalized and committed in `_attempt_rebase_and_push`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: review full branch diff against base, address findings
- [ ] PR summary prepared
