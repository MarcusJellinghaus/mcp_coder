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

### Step 1: Promote `truststore` to core dependencies — [step_1.md](./steps/step_1.md)
- [ ] Implementation (move `truststore>=0.9.0` from `[langchain-base]` extra into core `[project] dependencies`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Create `mcp_coder.utils.ssl_setup` + relocate tests + import-linter contract — [step_2.md](./steps/step_2.md)
- [ ] Implementation (create `ssl_setup.py`, move test file with autouse fixture, update `.importlinter`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Wire `ensure_truststore()` into `cli/main.main()` — [step_3.md](./steps/step_3.md)
- [ ] Implementation (add inline call in `main()` + new test in `tests/cli/test_main.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Decommission langchain SSL plumbing — [step_4.md](./steps/step_4.md)
- [ ] Implementation (delete `_ssl.py`, remove 7 call sites, drop 5 test mocks, delete 2 obsolete test classes)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Refresh SSL-related documentation — [step_5.md](./steps/step_5.md)
- [ ] Implementation (replace `_SSL_HINT` in `_exceptions.py` + refresh `gemini_backend.py` doc comment)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Render `token_source` in verify command — [step_6.md](./steps/step_6.md)
- [ ] Implementation (`_format_section()` special case + 2 render tests)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review
- [ ] PR summary
