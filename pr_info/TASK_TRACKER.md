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
  - **BLOCKED — environment, not code.** Re-verified a third time 2026-08-19. The repo
    `.venv` is still unusable and cannot be repaired from here (no shell tool available).
    - **Green:** `ruff --preview` (clean), `lint-imports` (21/21 contracts kept — the
      "iCoder Permissions Leaf Isolation" / "Core Purity" and "LangChain Library
      Isolation" contracts confirm the gateway stays `langchain_core`-free),
      `black`/`isort` (613 files unchanged).
    - **Green on every file this branch touches:** project-wide `mypy` reports 8 errors,
      **none** in a touched file; `pylint` scoped to
      `src/mcp_coder/icoder/permissions/`,
      `src/mcp_coder/llm/providers/langchain/permission_bridge.py` and the three edited
      test files reports zero issues.
    - **Red — `pytest` cannot run at all.** The venv's install-from-GitHub packages are
      older than `src/` requires:
      - `mcp_workspace.checks/` on disk contains only `branch_status.py`,
        `branch_status_polling.py`, `file_sizes.py`, `pr_feedback.py` — **no**
        `branch_status_rendering`, which `src/mcp_coder/checks/branch_status.py:17`
        imports. That breaks `import mcp_coder` at `src/mcp_coder/__init__.py:37`, so
        **every** test module and conftest fails to collect, including the three edited
        here. (Directory listing, not just the ImportError — this rules out shadowing.)
      - Same package: no `BranchStatusReport.pr_feedback_undeterminable`, no
        `fail_on_reviews` kwarg on `format_for_*`.
      - `mcp_workspace_github` is stale too: no `PullRequestManager.add_assignees`.
      - Missing `[langchain]` extras (`langchain_core`, `langgraph`,
        `langchain_mcp_adapters`, `httpx` all `E0401`) and `mcp.server.fastmcp`.
      Those five gaps account for **all** 8 mypy errors and every pylint error. All sit
      in files outside `git diff origin/main...HEAD` — none is caused by this change.
      The missing extras also mean the `langchain_integration` marked run would skip
      rather than pass, so it proves nothing until the venv is fixed.
    - **To unblock:** reprovision the venv (`uv pip install "...[dev,langchain]"` plus
      the install-from-GitHub packages `mcp-workspace` and `mcp-workspace-github` at the
      revisions `src/` expects), then re-run all five checks — in particular
      `pytest -m langchain_integration tests/icoder/test_icoder_permission_wiring.py`,
      which must **pass**, not skip.
    - ⚠️ **Do not diagnose the venv with `get_library_source` / `find_references`.**
      Those MCP helpers resolve against the *MCP server's own* interpreter, which is
      newer and fully provisioned — it resolves both
      `mcp_workspace.checks.branch_status_rendering` and
      `langchain_core.messages.ToolMessage`, making the venv look healthy when it is
      not. Only `run_pytest_check` / `run_pylint_check` / `run_mypy_check` execute
      against the project `.venv`; trust only those when judging the environment.
    - Note: CI is unaffected — `.github/workflows/langchain-integration.yml` provisions
      its own environment and already runs `tests/icoder/test_icoder_permission_wiring.py`
      under `-m langchain_integration`, so the new test is exercised there.
- [x] Commit message prepared

## Pull Request

- [ ] PR review — verify all acceptance criteria in [summary.md](./steps/summary.md) are met
- [ ] PR summary prepared
