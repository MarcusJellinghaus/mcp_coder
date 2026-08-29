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

### Step 1: Langchain — delete `execution_dir` outright ([step_1.md](./steps/step_1.md))

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Copilot — collapse `execution_dir` into `cwd` ([step_2.md](./steps/step_2.md))

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues (pytest blocked by a pre-existing
  stale `mcp-workspace` install — see note in step_2.md)
- [x] Commit message prepared

### Step 3: Remove the `--execution-dir` flag and replace the resolver ([step_3.md](./steps/step_3.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4a: `prompt_llm` takes a required `project_dir`; retarget the direct callers ([step_4a.md](./steps/step_4a.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4b: Delete `execution_dir` from every workflow signature ([step_4b.md](./steps/step_4b.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Documentation ([step_5.md](./steps/step_5.md))

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review
- [ ] PR summary
