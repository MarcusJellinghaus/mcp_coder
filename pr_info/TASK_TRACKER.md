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

- [x] Implementation (tests + production code)
      - All three functions added to `cli/utils.py` and to `__all__`; wired via
        `report_context_root(resolved, project_dir)` before the return on **both**
        `resolve_execution_dir` branches. `tach.toml` gained
        `{ path = "mcp_coder.prompts" }` on the `mcp_coder.cli` allowlist.
      - **Deviation from step_3.md, forced by CI:** the 16 tests live in a new
        module `tests/cli/test_utils_context_root.py`, not in `tests/cli/test_utils.py`.
        Adding them there took that file to 758 lines, over the 750-line limit that
        `.github/workflows/ci.yml:109` enforces (`mcp-coder check file-size
        --max-lines 750`). Same reasoning step_5.md already applies to `test_verify.py`.
        Nothing else changed; `test_utils.py` is back to its 542-line content.
      - One further judgement call: test 11 ("none found") patches
        `mcp_coder.cli.utils.find_context_claude_md` to return `[]`.
        `report_context_root` deliberately takes no `stop_at`, so the real walk would
        climb past `tmp_path` into directories no test controls — the same
        falsifiability the `stop_at` boundary exists to remove. The walk itself is
        covered unpatched by tests 1-7.
- [x] Quality checks: pylint, pytest, mypy — **pytest still blocked on the
      environment blocker diagnosed in Step 1; unchanged and untouched by this step**
      - Clean: pylint and mypy report **no findings at all** on the three files this
        step touches (`cli/utils.py`, `tests/cli/test_utils.py`,
        `tests/cli/test_utils_context_root.py`). `lint-imports` 21/21 kept (695 files,
        3563 dependencies analysed — the new `cli/utils.py` → `prompts.prompt_loader`
        import keeps "Layered Architecture"). `black`/`isort` clean (616 files).
        `mcp-coder check file-size --max-lines 750`: all 823 files within limit.
      - **`tach` could not be run**: not installed in the venv, so
        `run_tach_check` returns "tach is not available". The `tach.toml` line is
        therefore added but **unverified** — step_3.md's instruction to drop it if tach
        reports the dependency was already permitted could not be executed. Re-run
        `tach check` once the venv is repaired and remove the entry if redundant.
        (`import-linter` does cover the same import and keeps it.)
      - **pytest never ran the new tests.** Whole-suite collection still aborts:
        `ModuleNotFoundError: No module named 'mcp_workspace.checks.branch_status_rendering'`
        raised from `src/mcp_coder/checks/branch_status.py:17` via
        `src/mcp_coder/__init__.py:37`, so `import mcp_coder` fails and every test module
        errors at import. All 16 new tests are unproven in this environment, as is
        step_3.md's "Expected impact on existing tests" analysis — in particular that
        `test_commit.py`, `test_prompt.py`, `test_prompt_streaming.py` and the icoder
        tests survive the resolver now doing a real filesystem walk and emitting OUTPUT
        records. **Check `test_prompt_streaming.py`'s `capsys` assertions first** when
        the suite can run: a break there would invalidate the decision to wire the
        report into the resolver (summary.md §3), per step_3.md.
      - Root cause unchanged from Steps 1-2: the venv's `mcp-workspace` predates
        upstream `a1f0eac`. Same cause behind the 4 mypy errors and the pylint E1123 in
        `cli/commands/check_branch_status.py` and
        `tests/cli/commands/test_check_branch_status_exit_code.py` — pre-existing, from
        merged commit `bce0f22`, not from this step.
      - Fix (needs a shell; no MCP tool can install packages):
        `pip install --force-reinstall "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
        then `pip install -e ".[dev]"` (which also brings back `tach`), then re-run the
        checks. This session had no shell tool, so it could not apply the fix.
      - Carry-over for Steps 4-7: repair the venv first; the same blocker applies.
- [x] Commit message prepared

### Step 4: Nine call sites default to `project_dir`

Detail: [step_4.md](./steps/step_4.md) — **the behaviour change** + help text + 14 test updates + two `cwd == project_dir` tests. Depends on Steps 2 and 3.

- [x] Implementation (tests + production code)
      - All nine call sites pass `project_dir=`. Five one-line edits
        (`create_plan.py`, `create_pr.py`, `implement.py`, `rebase.py`,
        `review.py`), three statement reorders (`commit.py`, `prompt.py`,
        `icoder.py`), and the `check_branch_status.py` hoist out of the `--fix`
        block. `_EXECUTION_DIR_HELP` updated, keeping the substring
        "where Claude subprocess runs" that `test_canonical_help` asserts on.
      - TDD order followed: all 14 mocked call-argument assertions were updated
        before the call sites changed. Grepped `tests/` for `assert_called` on
        every `resolve_execution_dir` mock — `test_rebase.py` (`:73`, `:107`,
        `:122`) and `test_check_branch_status.py` (`:167`, `:226`) patch it but
        assert nothing about its arguments, so the list of 14 was in fact
        complete. No further sites found.
      - Both acceptance tests written, each `monkeypatch.chdir`-ing outside the
        project directory first: `test_default_execution_dir_uses_project_dir`
        (`tests/cli/commands/test_prompt.py`, CLI-free, runs under the standard
        marker exclusions) and `test_prompt_command_defaults_cwd_to_project_dir`
        (`tests/integration/test_execution_dir_integration.py`, asserts
        `options.cwd`, behind `require_claude_cli`).
      - Three further focused tests: the `commit.py` reorder test, the
        `--fix 0` + bad `--execution-dir` → exit 2 test pinning the hoist, and
        the updated verbatim `_EXECUTION_DIR_HELP` assertion.
      - **Deviation from step_4.md, forced by an existing name:** the commit
        reorder test went into the **existing** `TestCommitAutoExecutionDir`
        class (`test_commit.py:786`) rather than a new class of that name —
        pylint E0102 caught the collision. It uses the literal patch paths that
        class already uses, since `MODULE` is defined below it (`:938`).
      - Comments added at the four `test_commit.py` tests and at
        `test_check_branch_status.py:104` recording that they pass only because
        Step 2's `project_dir` default is not existence-validated. The ten
        `test_check_branch_status.py` tests the hoist newly exposes were left
        unpatched as step_4.md directs. Stale names fixed at both
        `test_prompt.py` (`test_default_execution_dir_uses_cwd` →
        `test_no_project_dir_falls_back_to_cwd`) and
        `test_execution_dir_integration.py`
        (`..._none_execution_dir_uses_none_as_cwd` →
        `test_prompt_command_no_project_dir_falls_back_to_cwd`), each with a
        docstring saying it documents the no-`project_dir` fallback.
- [x] Quality checks: pylint, pytest, mypy — **pytest still blocked on the
      environment blocker diagnosed in Step 1; unchanged and untouched by this step**
      - Clean: pylint and mypy report **no findings at all** on the twelve files
        this step touches. `lint-imports` 21/21 kept (695 files, 3563
        dependencies). `black`/`isort` clean (616 files).
        `check file-size --max-lines 750`: all 823 files within limit.
      - One real finding was raised and fixed during the step: pylint E0102
        `class already defined line 786` in `test_commit.py` — see the class
        collision noted above. Re-run is clean.
      - **pytest never ran the new tests.** Whole-suite collection still aborts:
        `ModuleNotFoundError: No module named 'mcp_workspace.checks.branch_status_rendering'`
        raised from `src/mcp_coder/checks/branch_status.py:17` via
        `src/mcp_coder/__init__.py:37`, so `import mcp_coder` fails and every
        test module errors at import. **This is the behaviour-changing commit
        and step_4.md asks for an unfiltered run; neither the filtered nor the
        unfiltered run executed a single test.** Specifically unproven:
        - the two acceptance tests, including test (a), which step_4.md requires
          to be green before the step is complete;
        - the "red before, green after" TDD confirmation — the assertions were
          updated first, but the red state could not be observed;
        - step_4.md's "Resolver-impact analysis", i.e. that the ten
          `test_check_branch_status.py` tests at `:104`, `:143`, `:279`, `:312`,
          `:355`, `:419`, `:458`, `:496`, `:531`, `:571` survive the hoist. If
          one fails, check assumption 2 (Step 2's non-validation) first.
      - Root cause unchanged from Steps 1-3: the venv's `mcp-workspace` predates
        upstream `a1f0eac`. Same cause behind all 9 remaining mypy errors and
        all 55 pylint occurrences — every one in an unrelated file,
        pre-existing on `main`.
      - Fix (needs a shell; no MCP tool can install packages):
        `pip install --force-reinstall "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
        then `pip install -e ".[dev]"`, then re-run the checks — **including one
        unfiltered `-n auto` run**, which is what executes test (b). This
        session had no shell tool, so it could not apply the fix.
      - Carry-over for Steps 5-7: repair the venv first; the same blocker applies.
- [x] Commit message prepared

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
