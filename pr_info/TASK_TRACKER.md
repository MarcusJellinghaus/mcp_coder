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
  - **BLOCKED — environment, not code.** Re-verified; the workspace `.venv` is still
    unusable and cannot be repaired from here (no shell tool available).
    - **Passing:** `ruff --preview` (clean), `lint-imports` (21/21 contracts kept —
      the "iCoder Permissions Leaf Isolation"/"Core Purity" and "LangChain Library
      Isolation" contracts confirm the gateway stays `langchain_core`-free),
      `black`/`isort` (613 files unchanged).
    - **Scoped to the files this change touches, both pass:** `pylint` and `mypy` over
      `src/mcp_coder/icoder/permissions/` + `src/mcp_coder/llm/providers/langchain/permission_bridge.py`
      report zero issues.
    - **Cannot be evaluated project-wide:** the repo `.venv` has an *older*
      `mcp-workspace` than `src/` requires — no `mcp_workspace.checks.branch_status_rendering`
      (imported by `src/mcp_coder/checks/branch_status.py:17`), no
      `BranchStatusReport.pr_feedback_undeterminable`, no `fail_on_reviews` kwarg on
      `format_for_*`. That breaks `import mcp_coder` at `src/mcp_coder/__init__.py:37`
      and therefore **all** pytest collection, including the three test files edited
      here. The same 3 attr/call mismatches plus `mcp.server.fastmcp` account for all
      8 mypy errors and every pylint error outside the langchain extras — all in files
      this change does not touch.
    - The venv is also missing the `[langchain]` extras (`langchain_core`, `langgraph`,
      `langchain_mcp_adapters` and `httpx` all `E0401`), so the `langchain_integration`
      marked run would skip rather than pass.
    - **To unblock:** reprovision the venv (`uv pip install "...[dev,langchain]"` plus
      the `install-from-github` packages), then re-run all five checks — in particular
      `pytest -m langchain_integration tests/icoder/test_icoder_permission_wiring.py`,
      which must pass rather than skip.
- [x] Commit message prepared

## Pull Request

- [ ] PR review — verify all acceptance criteria in [summary.md](./steps/summary.md) are met
- [ ] PR summary prepared
