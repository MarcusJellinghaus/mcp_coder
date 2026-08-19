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

### Step 1: Carry the real `tool_call_id` through both deny branches

Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
  - Tests first (red): `tests/llm/providers/langchain/test_permission_bridge.py` (3-arg calls, id assertion, false docstring claim removed), `tests/icoder/test_permissions_gateway.py` (`_request` gains `runtime`, deny-bridge stub widened to 3 args, 3 new tests), new `langchain_integration` graph-state test appended to `tests/icoder/test_icoder_permission_wiring.py`
  - Production (green): `build_deny_tool_message` gains required `tool_call_id: str`; `gateway.interceptor` sources it via `getattr` chaining from `request.runtime.tool_call_id` with `""` fallback (no `langchain_core`/`langgraph`/`langchain_mcp_adapters` import)
  - Call-site + CI: one-line update in `spikes/i3-1-approval/tier_c.py` (leave `FINDINGS.md` untouched); add `tests/icoder/test_icoder_permission_wiring.py` to `.github/workflows/langchain-integration.yml`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
  - Also: `run_ruff_check(["--preview"])` and `run_lint_imports_check` (gateway stays `langchain_core`-free)
  - Marked run `markers=["langchain_integration"]` on `tests/icoder/test_icoder_permission_wiring.py` must **pass**, not skip
  - Run `./tools/format_all.sh` before committing

  **BLOCKED — environment, not code.** Verified from scratch seven times, most recently
  2026-08-19; every run reproduces the findings below identically. The step's code is
  already committed as `3374a7c` ("Carry the real tool_call_id through both permission
  deny branches") with a clean working tree. The project `.venv` is unusable and cannot
  be repaired from these sessions (no shell tool available).

  - **Green — everything that can run, passes:**
    - `run_ruff_check(["--preview"])`: clean.
    - `run_lint_imports_check`: 21/21 contracts kept — "iCoder Permissions Leaf
      Isolation", "iCoder Permissions Core Purity" and "LangChain Library Isolation"
      together confirm `gateway.py` stays `langchain_core`-free.
    - `black`/`isort`: 613 files unchanged.
    - `run_pylint_check` scoped to the five touched files (`gateway.py`,
      `permission_bridge.py`, the three edited test modules): no issues.
    - `run_mypy_check`: 8 errors project-wide, **none** in a file this branch touches.
  - **Red — `pytest` cannot run at all.** The venv's install-from-GitHub packages are
    older than `src/` requires:
    - `mcp_workspace.checks` has no `branch_status_rendering`, which
      `src/mcp_coder/checks/branch_status.py:17` imports. That breaks `import mcp_coder`
      at `src/mcp_coder/__init__.py:37`, so **every** test module and conftest fails to
      collect — including the three edited here, and including
      `tests/icoder/conftest.py`, so the marked run never even reaches marker selection.
    - Same package: no `BranchStatusReport.pr_feedback_undeterminable`, no
      `fail_on_reviews` kwarg on `format_for_*`.
    - `mcp_workspace_github` is stale too: no `PullRequestManager.add_assignees`.
    - The `[langchain]` extras are absent — `pylint` reports `E0401` for
      `langchain_core`, `langgraph`, `langchain_mcp_adapters` and `httpx` — as is
      `mcp.server.fastmcp`. So even with collection fixed, the `langchain_integration`
      run would *skip*, not pass, and would prove nothing.

    Those gaps account for **all** 8 mypy errors and every pylint error, and all sit in
    files outside `git diff origin/main...HEAD`. None is caused by this change.
  - **To unblock:** reprovision the venv. `pyproject.toml:348-349` pins `mcp-workspace`
    and `mcp-tools-py` via `[tool.uv.sources]` git URLs, so the stale clones need a
    forced refresh, not a plain install — e.g.
    `uv pip install --refresh -e ".[dev,langchain]"` (add `mcp-workspace-github` the
    same way). Then re-run all five checks — in particular
    `pytest -m langchain_integration tests/icoder/test_icoder_permission_wiring.py`,
    which must **pass**, not skip.
  - ⚠️ **Do not diagnose the venv with `get_library_source` / `find_references`.** Those
    MCP helpers resolve against the *MCP server's own* interpreter, which is newer and
    fully provisioned — it resolves both
    `mcp_workspace.checks.branch_status_rendering` and
    `langchain_core.messages.ToolMessage`, making the venv look healthy when it is not.
    Only `run_pytest_check` / `run_pylint_check` / `run_mypy_check` execute against the
    project `.venv`; trust only those when judging the environment.
  - Note: CI is unaffected — `.github/workflows/langchain-integration.yml` provisions its
    own environment and already runs `tests/icoder/test_icoder_permission_wiring.py`
    under `-m langchain_integration`, so the new test is exercised there.
- [x] Commit message prepared

## Pull Request

- [ ] PR review — verify all acceptance criteria in [summary.md](./steps/summary.md) are met
- [ ] PR summary prepared
