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

### Step 1: `issue_analyse_supervisor` — per-issue analysis log
See [step_1.md](./steps/step_1.md)

- [x] Implementation: per-issue log name `pr_info/issue_analysis_log_<issue>.md`, `list_directory` existence check, no glob delete, Finalize deletes only that file (verify searches + deployed-prose/skill tests)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Review supervisors — create the log in the step that picks `{n}`
See [step_2.md](./steps/step_2.md)

- [x] Implementation: merge Setup steps 3 and 4 in `plan_review_supervisor` and `implementation_review_supervisor`, with "already exists → next number" rule (verify searches + deployed-prose/skill tests)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Deployed agents and `issue_update` — delete only own `.scratch/` files
See [step_3.md](./steps/step_3.md)

- [x] Implementation: cleanup sentence in `code-engineer`, `issue-analyst`, `plan-engineer`; `issue_update` body file `.scratch/issue_body_<issue>.md` and own-files-only cleanup (verify searches + deployed-prose/skill tests)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: `.claude/CLAUDE.md` — ownership rule, manual cleanup, probe name, Jenkins run folder
See [step_4.md](./steps/step_4.md)

- [x] Implementation: extend "No session scratchpad" line, probe `.scratch/test_probe_<issue or topic>.py` deleted with `delete_this_file`, Jenkins lines use `.scratch/jenkins_logs_<issue or topic>_<date>/` (verify searches + deployed-prose/skill tests)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: Jenkins process docs — run folder, delete only it
See [step_5.md](./steps/step_5.md)

- [x] Implementation: run folder in `tools/jenkins_status_check.md` and `tools/jenkins_issue_analysis.md` for `--outdir`, `--logdir`, single-build output and subagent findings; Decision 6 re-check over `.claude/**` (verify searches + deployed-prose/skill tests)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the summary and fix findings
- [ ] PR summary prepared
