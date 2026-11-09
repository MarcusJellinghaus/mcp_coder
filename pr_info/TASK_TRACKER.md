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

### Step 1: Shared placeholder resolver `mcp_coder.utils.env_placeholders`
See [step_1.md](./steps/step_1.md)

- [ ] Implementation: tests in `tests/utils/test_env_placeholders.py`, then `src/mcp_coder/utils/env_placeholders.py`
- [ ] Quality checks: pylint, pytest, mypy, lint-imports, tach — fix all issues
- [ ] Commit message prepared

### Step 2: LangChain config loader uses the shared resolver
See [step_2.md](./steps/step_2.md)

- [ ] Implementation: precondition check, adjust tests in `test_langchain_agent.py`, then replace `_resolve_env_vars` in `_mcp_tools.py`
- [ ] Quality checks: pylint, pytest, mypy, lint-imports, tach — fix all issues
- [ ] Commit message prepared

### Step 3: LangChain silently ignores Claude Code-only `alwaysLoad`
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: add `test_ignores_always_load_field`, then `_IGNORED_FIELDS` in `_mcp_tools.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Verify warns only on unresolved `env` placeholders
See [step_4.md](./steps/step_4.md)

- [ ] Implementation: rewrite placeholder tests in `test_verify_mcp_orchestration.py`, then `_validate_mcp_config` in `verify_sections.py` and its call site in `verify.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Verify MCP edit smoke test in `.scratch/` with gitignore pre-check
See [step_5.md](./steps/step_5.md)

- [ ] Implementation: precondition check, tests in `test_verify_mcp_edit_smoke.py`, then shim re-export, `_run_mcp_edit_smoke_test`, `tach.toml` and `.gitignore`
- [ ] Quality checks: pylint, pytest, mypy, lint-imports, tach — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against the base branch and address findings
- [ ] PR summary prepared
