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

### Step 1: `init` deploys `python.md` only for the `mcp-tools-py` toolkit — [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code): rename `PYTHON_TOOLKIT`, add `_is_python_toolkit` / `skip_python` / reminder in `init.py`, `TestInitToolkit`, docs
- [x] Quality checks (format, pylint, pytest, mypy) — fix all issues
- [x] Commit message prepared

### Step 2: Toolkit-neutral prose in every deployed `.claude/` file — [step_2.md](./steps/step_2.md)

- [ ] Implementation (tests + production code): `test_init_deployed_neutral.py`, retarget `test_prompt.py`, neutralise skill/agent/knowledge-base bodies, extend `python.md`, sync `prompts.md` rebase row
- [ ] Quality checks (format, pylint, pytest, mypy) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review all changes against `pr_info/steps/summary.md`
- [ ] PR summary prepared
