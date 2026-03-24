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

### Step 1: Add `install_hint` to LangChain verification results

Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation: tests in `test_langchain_verification.py` + production code in `verification.py`
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(verify): add install hints to langchain verification results`

### Step 2: Add `install_hint` to Claude CLI verification

Detail: [step_2.md](./steps/step_2.md)

- [x] Implementation: test in `test_claude_cli_verification.py` + production code in `claude_cli_verification.py`
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit: `feat(verify): add install hint to claude CLI verification`

### Step 3: Conditional Claude display, inline hints, and install summary

Detail: [step_3.md](./steps/step_3.md)

- [ ] Implementation: tests in `test_verify_format_section.py` and `test_verify_orchestration.py` + production code in `verify.py`
- [ ] Quality checks pass: pylint, pytest, mypy — fix all issues
- [ ] Commit: `feat(verify): contextual display and install summary in verify command`

## Pull Request

- [ ] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
