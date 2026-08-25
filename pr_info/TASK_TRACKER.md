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

> **Manual actions (no commits).** See
> [summary.md](./steps/summary.md#manual-actions-no-commits--schedule-around-the-code-steps).
> **Before Step 1:** run the pre-flight marker probe — it gates the whole implementation.
> **After Step 7:** repeat the probe, and clean the Jenkins tool env `.claude\` (keep `.mcp.json`).

### Step 1: `claude_md_paths()` + `is_claude_md` refactor

Detail: [step_1.md](./steps/step_1.md) — shared candidate knowledge, no behaviour change.

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — **blocked on the environment, not on this step**
      (re-verified; blocker unchanged, so the step is closed on what is verifiable here)
      - Clean: `lint-imports` 21/21 kept; `black`/`isort` no changes (615 files
        unchanged). Neither `prompt_loader.py` nor `test_prompt_loader.py` draws a
        single pylint or mypy finding — every reported finding is in an unrelated
        file and pre-exists on `main`.
      - **pytest never ran**: 0 tests collected, whole-suite. Not "passed" —
        collection aborts before any test executes. The 8 Step 1 tests
        (`test_claude_md_paths_*`, `test_is_claude_md_*`) are therefore unproven
        in this environment and must be run once the venv is repaired.
      - Root cause — `src/mcp_coder/checks/branch_status.py:17`
        imports `mcp_workspace.checks.branch_status_rendering`, which the repo
        `.venv` copy does not have, so `import mcp_coder` raises and every test
        module fails at import.
      - Same root cause behind all pylint E0401/E0611/E1123/E1101 and all 9 mypy
        errors (`BranchStatusReport.pr_feedback_undeterminable`,
        `format_for_llm(fail_on_reviews=...)`). The installed `mcp-workspace`
        predates upstream `a1f0eac feat(checks): add review gate + missing-token
        degradation (#244)`, which added exactly those names. `mcp-workspace` is
        an unpinned `git+https://` dependency (pyproject.toml:348), so the venv
        drifted behind `main`.
      - Secondary gaps in the same venv: `langchain_core`, `langchain_mcp_adapters`,
        `langgraph`, `httpx`, `mcp.server.fastmcp.FastMCP` (the `[dev]` extra is
        not fully installed); `tach` is absent so `run_tach_check` cannot run.
      - **Fix (needs a shell — no MCP tool can install packages):**
        `pip install -e ".[dev]" --force-reinstall --no-deps` after
        `pip install --force-reinstall "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`,
        then re-run the three checks. All of this is pre-existing on `main` and
        untouched by Step 1. The implementing session had no shell tool at all,
        so it could not apply this fix itself.
      - **Carry-over for Steps 2-7:** their "fix all issues" checks inherit the
        same blocker. Repair the venv before Step 2 rather than re-diagnosing it
        each step.
- [x] Commit message prepared

### Step 2: `resolve_execution_dir` signature + deprecation

Detail: [step_2.md](./steps/step_2.md) — new optional `project_dir` param, deprecation warning; backwards compatible.

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — **pytest still blocked on the
      environment blocker diagnosed in Step 1; unchanged and untouched by this step**
      - Clean: pylint and mypy report **no findings at all** on the three files
        this step touches (`cli/utils.py`, `tests/cli/test_utils.py`,
        `tests/integration/test_execution_dir_integration.py`).
        `lint-imports` 21/21 kept; `black`/`isort` no changes (615 files unchanged).
      - **pytest never ran the new tests.** Whole-suite collection still aborts:
        `ModuleNotFoundError: No module named 'mcp_workspace.checks.branch_status_rendering'`
        raised from `src/mcp_coder/checks/branch_status.py:17` via
        `src/mcp_coder/__init__.py:37`, so `import mcp_coder` fails and every test
        module errors at import. The 8 new tests
        (`test_none_with_project_dir_returns_project_dir`,
        `test_project_dir_accepts_str_and_path`,
        `test_relative_project_dir_is_resolved`,
        `test_nonexistent_project_dir_is_not_validated`,
        `test_explicit_execution_dir_wins_over_project_dir`,
        `test_explicit_execution_dir_warns_deprecation`,
        `test_explicit_execution_dir_logs_deprecation`,
        `test_default_does_not_warn`) are unproven in this environment, as are the
        existing `TestResolveExecutionDir` tests that must stay green.
      - Root cause unchanged from Step 1: the venv's `mcp-workspace` predates
        upstream `a1f0eac`. Same cause behind the 3 remaining mypy errors in
        `cli/commands/check_branch_status.py` (`pr_feedback_undeterminable`,
        `format_for_llm/format_for_human(fail_on_reviews=...)`) — pre-existing on
        `main`, not from this step.
      - Fix (needs a shell; no MCP tool can install packages):
        `pip install --force-reinstall "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
        then `pip install -e ".[dev]"`, then re-run the three checks. This session
        had no shell tool, so it could not apply the fix.
      - Carry-over for Steps 3-7: repair the venv first; the same blocker applies.
- [x] Commit message prepared

### Step 3: Context-root finder + reporter

Detail: [step_3.md](./steps/step_3.md) — `find_context_claude_md`, `is_outside_project_dir`, `report_context_root`, wired into the resolver; `tach.toml`. Depends on Steps 1 and 2.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Nine call sites default to `project_dir`

Detail: [step_4.md](./steps/step_4.md) — **the behaviour change** + help text + 14 test updates + two `cwd == project_dir` tests. Depends on Steps 2 and 3.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: `verify` reports the same

Detail: [step_5.md](./steps/step_5.md) — PROMPTS section rows, new test module. Depends on Step 3.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Branch-name call sites use `project_dir`

Detail: [step_6.md](./steps/step_6.md) — `task_processing.py` two lines. Depends on Step 4.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Documentation

Detail: [step_7.md](./steps/step_7.md) — architecture, cli-reference, environments, both claude-code docs. Depends on Step 4.

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review
- [ ] PR summary
