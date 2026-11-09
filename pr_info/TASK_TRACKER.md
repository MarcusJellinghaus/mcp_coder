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

### Step 1: Remove dead check wrappers from the shim
See [step_1.md](./steps/step_1.md)

- [x] Implementation: trim `mcp_tools_py.py` to `resolve_steps` re-export, reduce `tests/test_mcp_tools_py.py`, delete `tests/test_mcp_tools_py_integration.py`, remove `checker_integration` marker from `pyproject.toml` and `has_mypy_errors` from `vulture_whitelist.py`
- [x] Quality checks: pylint, pytest, mypy (plus format, vulture) — fix all issues
- [x] Commit message prepared

### Step 2: Fix stale docs and tach comments
See [step_2.md](./steps/step_2.md)

- [ ] Implementation: comment-only edits in `tach.toml`, fix shim sentence in `docs/architecture/enforcement.md`, remove Issue #011 and #008 from `docs/tests/issues.md`
- [ ] Quality checks: pylint, pytest, mypy (plus tach) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against base branch
- [ ] PR summary prepared
