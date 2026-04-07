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

### Step 1: LLMTimeoutError + implement latent bug fix
- [x] Implementation: add `LLMTimeoutError` to `llm/interface.py`, normalize timeouts in `prompt_llm()`, update `implement/task_processing.py` to catch it, add/update tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Add failure labels + refactor create_plan.py → package
- [x] Implementation: add 2 labels to `labels.json`, create `create_plan/` package (`__init__.py`, `core.py`, `constants.py`, `prerequisites.py`), delete old `create_plan.py`, update all test patch paths
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Failure handling helpers + orchestration wiring + CLI help
- [ ] Implementation: add `_format_failure_comment()` and `_handle_workflow_failure()` to `core.py`, wire into `run_create_plan_workflow()` and `run_planning_prompts()`, promote commit/push to hard errors, update CLI help text, add/update tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps implemented correctly
- [ ] PR summary prepared
