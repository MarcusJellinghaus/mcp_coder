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

### Step 1: Config layer — add `find_repo_section_by_url()` ([detail](./steps/step_1.md))
- [x] Implementation: tests + production code in `user_config.py`
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: CLI parsers — replace `--update-labels` with granular flags ([detail](./steps/step_2.md))
- [x] Implementation: tests + `BooleanOptionalAction` flags in `parsers.py`
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: CLI utils — add `resolve_issue_interaction_flags()` ([detail](./steps/step_3.md))
- [x] Implementation: tests + production code in `cli/utils.py`
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Failure handling + workflow cores — split into two flags ([detail](./steps/step_4.md))
- [ ] Implementation: tests + rename params, add `post_issue_comments` gating across 5 source files
- [ ] Quality checks pass: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: CLI commands — use `resolve_issue_interaction_flags()` ([detail](./steps/step_5.md))
- [ ] Implementation: tests + wire up shared helper in 3 CLI commands
- [ ] Quality checks pass: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Coordinator — extend config + remove template flags ([detail](./steps/step_6.md))
- [ ] Implementation: tests + extend `load_repo_config()`, remove `--update-labels` from templates
- [ ] Quality checks pass: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Default config template + documentation ([detail](./steps/step_7.md))
- [ ] Implementation: tests + update config template and docs
- [ ] Quality checks pass: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: all steps complete, all checks green
- [ ] PR summary prepared
