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

### Step 1: Shared failure comment builder `build_failure_comment` + `_branch_head` — [step_1.md](./steps/step_1.md)

- [ ] Implementation: tests in `tests/workflow_utils/test_failure_comment.py` + builder, `FIELD_ORDER`, `CommentField`, `SHORT_SHA_LENGTH`, `_branch_head` in `failure_handling.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: `run_guarded(workflow_title=…)`, all crash nets on the builder, implement migration, `ReviewConfig.display_name` — [step_2.md](./steps/step_2.md)

- [ ] Implementation: tests + `run_guarded` `workflow_title` / tuple `build_comment`, implement `_comment_parts` / `_fail` (drop `build_url`), titles in all six nets, `display_name` on `ReviewConfig`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: create_plan deliberate failure on the builder — [step_3.md](./steps/step_3.md)

- [ ] Implementation: tests + delete `_format_failure_comment`, `_handle_workflow_failure` calls `build_failure_comment` (`## ❌ Planning Failed`), update `create_plan/__init__.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: create_pr deliberate failure on the builder — [step_4.md](./steps/step_4.md)

- [ ] Implementation: tests + delete `format_failure_comment` / `_format_failure_comment` alias, `handle_create_pr_failure` calls the builder (`## ❌ PR Creation Failed`, PR field, cleanup note)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: fix_ci deliberate failure on the builder — [step_5.md](./steps/step_5.md)

- [ ] Implementation: tests + fix_ci `_fail` calls the builder (`## ❌ CI Fix Failed`, Category / Stage / Error)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: `RebaseOutcome` + merge-tree classification; callers compile against it — [step_6.md](./steps/step_6.md)

- [ ] Implementation: tests + `RebaseOutcome`, `_uncommitted_tracked_files`, `_base_sha`, `_classify_failed_rebase` in `rebase.py`; `_after_steps` returns `(reason, outcome)`; update fix_conflict / review callers and mocks
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Review `_fail` → structured "Failed" comment — [step_7.md](./steps/step_7.md)

- [ ] Implementation: tests (autouse `_branch_head` fixture in review `conftest.py`) + `_FAIL_REASONS` table, `_fail` uses the builder (`## ❌ <Lane> Failed`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: Review `_route_to_human` → structured "Handed Off" comments + rebase table + docs — [step_8.md](./steps/step_8.md)

- [ ] Implementation: tests + `_REBASE_HANDOFF` table, `_route_to_human` new kwargs / banner / builder, four call sites in `review/core.py`, `steps.py` warning log + comment, `development-process.md` escalation sentence
- [ ] Quality checks: pylint, pytest, mypy, check_file_size (`review/core.py` < 750 lines) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the base branch and address findings
- [ ] PR summary prepared
