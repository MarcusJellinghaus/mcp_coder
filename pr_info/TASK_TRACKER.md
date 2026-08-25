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

> **Manual actions (no commits).** See
> [summary.md](./steps/summary.md#manual-actions-no-commits--schedule-around-the-code-steps).
> **Before Step 1:** run the pre-flight marker probe — it gates the whole implementation.
> **After Step 7:** repeat the probe, and clean the Jenkins tool env `.claude\` (keep `.mcp.json`).

### Step 1: `claude_md_paths()` + `is_claude_md` refactor

Detail: [step_1.md](./steps/step_1.md) — shared candidate knowledge, no behaviour change.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: `resolve_execution_dir` signature + deprecation

Detail: [step_2.md](./steps/step_2.md) — new optional `project_dir` param, deprecation warning; backwards compatible.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Context-root finder + reporter

Detail: [step_3.md](./steps/step_3.md) — `find_context_claude_md`, `is_outside_project_dir`, `report_context_root`, wired into the resolver; `tach.toml`. Depends on Steps 1 and 2.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Nine call sites default to `project_dir`

Detail: [step_4.md](./steps/step_4.md) — **the behaviour change** + help text + 14 test updates + two `cwd == project_dir` tests. Depends on Steps 2 and 3.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: `verify` reports the same

Detail: [step_5.md](./steps/step_5.md) — PROMPTS section rows, new test module. Depends on Step 3.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Branch-name call sites use `project_dir`

Detail: [step_6.md](./steps/step_6.md) — `task_processing.py` two lines. Depends on Step 4.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Documentation

Detail: [step_7.md](./steps/step_7.md) — architecture, cli-reference, environments, both claude-code docs. Depends on Step 4.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review
- [ ] PR summary
