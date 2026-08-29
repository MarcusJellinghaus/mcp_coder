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

### Step 1: `require_langchain_history()` in the storage layer

Details: [step_1.md](./steps/step_1.md)

- [x] Implementation: add the two tests to `TestLangchainSessionStorage` in `tests/llm/storage/test_session_storage.py`, then add `require_langchain_history()` to `src/mcp_coder/llm/storage/session_storage.py` and its name to `__all__`
- [x] Quality checks: pylint, pytest, mypy — fix all issues (pylint + mypy clean; pytest blocked repo-wide by a pre-existing `ModuleNotFoundError: mcp_workspace.checks.branch_status_rendering` from `src/mcp_coder/checks/branch_status.py:17` — the venv's `mcp_workspace` is stale, unrelated to this change)
- [x] Commit message prepared

### Step 2: Guard both langchain entry points (+ docs)

Details: [step_2.md](./steps/step_2.md)

- [x] Implementation: add `_resolve_session_id()` in `src/mcp_coder/llm/providers/langchain/__init__.py` and swap both call sites (2a/2b); add the opt-in `skip_langchain_history_guard` fixture and apply it, plus the `store_langchain_history` seed in `test_langchain_integration.py` (2c); add `tests/llm/providers/test_langchain_session_guard.py` (2d) and the CLI exit-code test in `tests/cli/commands/test_prompt.py` (2e); update the three docs (2f)
- [x] Quality checks: pylint, pytest, mypy — fix all issues (pylint + mypy report nothing in the touched files; all remaining findings are the pre-existing stale-`mcp_workspace` install and uninstalled optional deps. The venv's `mcp_workspace` still lacks `checks.branch_status_rendering`, which blocks every pytest run, so the suite was run with `PYTHONPATH` pointing at the local mcp-workspace source: the 5 new tests pass, `tests/llm/providers/langchain/`, `tests/llm/storage/`, `tests/llm/test_interface.py` and `tests/cli/commands/test_prompt.py` are green. Remaining failures are unrelated and pre-existing: 3 copilot CLI integration tests and `test_connection_errors_contains_httpx_connect_error` (httpx not installed). The `:229` integration seed is marker-excluded here and was verified by inspection.)
- [x] Commit message prepared

## Pull Request

- [ ] PR review: verify acceptance items in [summary.md](./steps/summary.md) are met
- [ ] PR summary prepared
