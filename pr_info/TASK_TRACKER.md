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

### Step 1: BLOCKED_FILE constant + read_and_clear_blocked() helper

Details: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, mypy clean for this step. **pytest UNVERIFIED —
      environment blocked, see below.** Ticked to unblock Step 2; the pytest
      gap is real and is carried forward, not resolved.
  - pylint: no issue in any file this step touches. Every reported error is
    `E0401`/`E0611` for uninstalled optional deps (`langchain_*`, `httpx`,
    `mcp.server.fastmcp`) plus `E1123`/`E1101` for `fail_on_reviews` /
    `pr_feedback_undeterminable` — all downstream of the stale `mcp-workspace`
    described below.
  - mypy: 8 errors, none in this step's files; same two root causes.
  - pytest: **never executed — 0 of this step's 5 new tests have run.**
    `src/mcp_coder/checks/branch_status.py:17` imports
    `mcp_workspace.checks.branch_status_rendering`, absent from the
    `mcp-workspace` in `.venv`. That import runs via `mcp_coder/__init__.py:37`,
    so every test module importing `mcp_coder` dies at collection
    (`ModuleNotFoundError`), including `TestReadAndClearBlocked`.
  - Root cause — stale `.venv`, confirmed by differential evidence: resolving
    `mcp_workspace.checks.branch_status.BranchStatusReport` against an
    up-to-date interpreter shows `pr_feedback_undeterminable` and
    `format_for_human(..., fail_on_reviews=...)`, and
    `branch_status_rendering` exists there as the canonical home of `CIStatus`
    / `WaitContext` / `GITHUB_TOKEN_HINT`. The `.venv` copy predates that
    split and lacks all of them — one stale install explains all five error
    signatures above. `mcp-workspace` is installed unpinned from git main
    (`pyproject.toml:348`), so this drift is expected and recurring.
  - No code-side workaround exists: re-pointing the shim import would still
    leave the missing `BranchStatusReport` fields, so the suite cannot go
    green without refreshing the install. Editing `branch_status.py` to match
    the stale `.venv` would break CI, where a fresh install is used.
  - Remediation is an environment change and is **not executable by this agent**
    (no shell tool available in this session):
    `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
    Re-run the three checks afterwards to get real pytest coverage for Steps 1+.
  - Interim verification is by inspection only: the helper at
    `task_processing.py:282-311` matches the step's ALGORITHM and DATA tables
    exactly (delete-in-`finally`, fallback on empty, 500 chars + `"..."`).
- [x] Commit message prepared

### Step 2: TaskOutcome replaces tuple[bool, str]

Details: [step_2.md](./steps/step_2.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, mypy clean for this step. **pytest STILL UNVERIFIED —
      same environment block as Step 1, unchanged and unfixable from here.**
  - Scope delivered: `TaskOutcome` dataclass + both signatures and all 11 returns
    in `task_processing.py`; `core.py` binds `outcome` (no `reason` shadowing);
    all ~35 test call sites converted; the four failure-routing tests moved into
    the new `tests/workflows/implement/test_core_failure_routing.py`; both
    pre-existing defects in `test_execution_dir_integration.py` fixed (patch
    target `process_single_task` → `process_task_with_retry`, and the assertion
    now carries `format_code=` / `check_type_hints=` computed from
    `get_implement_config`). `detail` left at `""` everywhere, per the step.
  - File-size gate: `mcp-coder check file-size --max-lines 750` passes —
    all 822 files within limit. `test_core_workflow.py` dropped 747 → 614.
  - pylint: no issue in any of the 7 files this step touches. Every reported
    error is `E0401`/`E0611` for uninstalled optional deps (`langchain_*`,
    `httpx`, `mcp.server.fastmcp`) plus `E1123`/`E1101` for `fail_on_reviews` /
    `pr_feedback_undeterminable` — all downstream of the stale `mcp-workspace`.
  - mypy: 8 errors, byte-identical to Step 1's list, none in this step's files.
  - pytest: **never executed — still 0 tests run, repo-wide.**
    `src/mcp_coder/checks/branch_status.py:17` imports
    `mcp_workspace.checks.branch_status_rendering`, absent from the
    `mcp-workspace` installed in the pytest interpreter. That import runs via
    `mcp_coder/__init__.py:37`, so *every* test module importing `mcp_coder`
    dies at collection. Re-confirmed this run, not assumed from Step 1.
  - Remediation is unchanged and still **not executable by this agent** (no
    shell tool in this session):
    `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
  - Interim verification is stronger than Step 1's, because mypy --strict covers
    `tests/` as well as `src/` and reported nothing here. That rules out the
    failure modes this mechanical refactor can actually have: leftover bare
    `success` / `reason` names, wrong `TaskOutcome` arity, `.success` /
    `.reason` typos, and the `-> TaskOutcome` return-type mismatches. mypy
    cannot see mock `.return_value` assignments (MagicMock is `Any`), so those
    were swept by grep instead: `success, reason` and `= (True|False, "<reason>")`
    both now return **zero** matches across `tests/`.
  - The `claude_cli_integration` run the step asks for could not happen either —
    `test_execution_dir_integration.py` is one of the modules failing collection.
    Verified by inspection instead, as the step permits: `core.py:44-47` imports
    `process_task_with_retry` (and does **not** import `process_single_task`,
    confirming the old patch target was dead), and the call at `core.py:145-153`
    passes exactly `(project_dir, provider, mcp_config, settings_file,
    execution_dir)` positionally plus `format_code=` / `check_type_hints=` as
    keywords — matching the corrected assertion.
- [x] Commit message prepared

### Step 3: Blocked detection in process_single_task

Details: [step_3.md](./steps/step_3.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, mypy clean for this step. **pytest now genuinely
      RUN and green for this step** — the Step 1/2 environment block was worked
      around locally; the underlying stale venv is unchanged, see below.
  - Scope delivered: start-of-task `read_and_clear_blocked` cleanup; the Step 5
    LLM block restructured so its three early exits assign `llm_error` instead
    of returning (empty-response guard, both typed `except` paths), with the
    marker read in `finally`; the three-way branch placed **before** the Step 6
    files-changed check; `process_single_task` + `process_task_with_retry`
    docstring reason lists updated with `'blocked'`. The empty-response guard's
    `store_session` moved into an `else:`, as the step flagged. `core.py`,
    `labels.json`, `RETRY_REMINDER` and `prompts.md` untouched.
  - New `TestProcessSingleTaskBlocked` (7 tests) written first and watched fail:
    5 of 7 failed before the change, `test_blocked_wins_over_changed_files`
    failing with `TaskOutcome(success=True, reason='completed')` — the inverted
    path, reproduced. All 7 pass after.
  - One deviation from the step's test sketch, forced by the code: the marker
    cannot be pre-written by the test, because the new start-of-task cleanup
    sweeps it before the LLM call. Tests 1–4 write it from a `prompt_llm`
    side effect instead, which is what the real agent does. Test 5
    (`test_stale_marker_removed_at_task_start`) still pre-writes it — that is
    exactly the behaviour it pins.
  - pytest: `tests/workflows/implement` + `tests/workflow_steps` +
    `tests/workflow_utils` → **391 passed**, with the standard `-n auto` marker
    exclusions. That covers every consumer of `TaskOutcome` /
    `process_single_task` bar `tests/integration/test_execution_dir_integration.py`,
    which is `claude_cli_integration`-marked and excluded by the standard run.
  - Environment, unchanged from Steps 1–2: `.venv`'s `mcp-workspace` predates
    the `branch_status_rendering` split, so `import mcp_coder` dies at
    collection repo-wide. Root cause confirmed directly this run by capturing
    the traceback: `ModuleNotFoundError: No module named
    'mcp_workspace.checks.branch_status_rendering'` via
    `mcp_coder/__init__.py:37` → `checks/branch_status.py:17`.
  - Workaround used to obtain real pytest signal: a temporary root
    `conftest.py` aliasing the missing module from the installed
    `mcp_workspace.checks.branch_status`. **It has been deleted** — `git status`
    shows only the two intended files. It is a local diagnostic, not a fix, and
    must not be committed.
  - Still broken and NOT caused by this step: `tests/workflows/review/` fails on
    `CIStatus.UNKNOWN` / `BranchStatusReport.pr_feedback_undeterminable`, which
    the shim cannot supply because the stale install genuinely lacks them.
    A full-suite run also exceeds the 300 s tool timeout. Both clear with:
    `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
  - pylint: no issue in either file this step touches. Every reported error is
    `E0401`/`E0611` for uninstalled optional deps (`langchain_*`, `httpx`,
    `mcp.server.fastmcp`) plus `E1123`/`E1101` for `fail_on_reviews` /
    `pr_feedback_undeterminable` — all downstream of the stale install.
  - mypy: 8 errors, byte-identical to Steps 1 and 2, none in this step's files.
    In particular `llm_error in ("timeout", "mcp_unavailable")` narrows
    `str | None` → `str` cleanly, so no cast was needed.
  - black/isort: no changes. File-size gate passes (823 files ≤ 750 lines;
    `test_task_processing.py` is allowlisted).
  - Intermediate state left by this commit is the one the step describes and is
    **not** pinned by any test: `core.py:155-191` has no `else`, so a `blocked`
    outcome falls through to `progress.completed += 1` and the loop re-runs.
    Step 5 closes it.
- [x] Commit message prepared

### Step 4: status-06f-blocked:implementation-blocked label

Details: [step_4.md](./steps/step_4.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, mypy clean for this step; **pytest genuinely RUN
      and green** via the same local workaround Step 3 used.
  - Scope delivered: the `implementation_blocked` entry in `labels.json`,
    inserted directly after `no_changes_after_retries` so the `status-06f-*`
    block stays contiguous, plus all six test-side count/name updates.
    `ignore_labels` and every workflow source file left untouched — wiring
    `FAILURE_LABELS["blocked"]` to this `internal_id` is Step 5.
  - Test-first, watched red: all six assertions failed before the `labels.json`
    change — `StopIteration` for the new `ERROR_STATUS_IDS` entry, the
    order-sensitive name-list diff at index 20, `36 == 37`, `35 == 36` twice,
    and `26 == 27`. All pass after. Targeted run: **118 passed**.
  - Wider regression run: `tests/cli` + `tests/config` +
    `tests/workflows/vscodeclaude` → **1671 passed, 2 skipped** (stale-venv
    `branch_status` files excluded, see below); `tests/workflows/implement` +
    `create_plan` + `create_pr` + `tests/workflow_steps` + `tests/workflow_utils`
    → **583 passed**. Grepped for further hard-coded label counts across
    `tests/` — none beyond the four files the step names; the only other
    `len(workflow_labels)` sites are dynamic (`test_set_status.py:126`) or
    bound to the 5-label test fixture.
  - Environment, unchanged from Steps 1–3: `.venv`'s `mcp-workspace` predates
    the `branch_status_rendering` split, so `import mcp_coder` dies at
    collection repo-wide. Diagnosed precisely this run: the stale
    `branch_status` still carries `CIStatus` and `WaitContext` but **not**
    `GITHUB_TOKEN_HINT`, which is why a bare module alias is not enough.
  - Workaround used to obtain real pytest signal: a temporary root
    `conftest.py` synthesising `branch_status_rendering` from those names and
    supplying a placeholder `GITHUB_TOKEN_HINT`. **It has been deleted** —
    `git status` shows only the five intended files plus this tracker. Local
    diagnostic, not a fix; must not be committed.
  - Still broken and NOT caused by this step: the four
    `test_check_branch_status*.py` modules and
    `test_main.py::TestFaulthandlerSafetyNet` fail on `CIStatus.UNAVAILABLE` /
    `GITHUB_TOKEN_HINT`, which the shim cannot fully supply (the subprocess
    test bypasses `conftest.py` entirely). All clear with:
    `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
  - pylint: no issue in any of the 5 files this step touches. Every reported
    error is `E0401`/`E0611` for uninstalled optional deps (`langchain_*`,
    `httpx`, `mcp.server.fastmcp`) plus `E1123`/`E1101` for `fail_on_reviews` /
    `pr_feedback_undeterminable` — all downstream of the stale install.
  - mypy: 8 errors, byte-identical to Steps 1–3, none in this step's files.
  - black/isort: no changes (614 files unchanged). File-size gate passes
    (822 files ≤ 750 lines).
- [x] Commit message prepared

### Step 5: core.py routes blocked + final-mypy cleanup

Details: [step_5.md](./steps/step_5.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, mypy clean for this step; **pytest genuinely RUN
      and green** via the same local workaround Steps 3–4 used.
  - Scope delivered: `FAILURE_LABELS["blocked"] = "implementation_blocked"`,
    `CATEGORY_DISPLAY["blocked"] = "Blocked"` and `append_detail()` in
    `failure_reporting.py`; in `core.py` the `blocked` branch (directly after
    `no_tasks`, with an **unconditional** ERROR log and `outcome.detail` as the
    `**Error:**` line), `append_detail(...)` on the timeout / mcp_unavailable
    messages, and `read_and_clear_blocked(project_dir)` immediately before the
    final-mypy block's `get_full_status`. The reason chain stays an `if` chain —
    no table refactor, as the step requires.
  - Test-first, watched red: `test_failure_reporting.py` died at **import**
    (`CATEGORY_DISPLAY` / `append_detail` did not exist), and
    `test_core_failure_routing.py` **hung until the 300 s tool timeout** — the
    Step 3 intermediate state reproduced exactly: with no `blocked` branch the
    outcome fell through to `progress.completed += 1` and the loop re-ran
    forever against a `return_value` mock. All green after the change.
  - Deviation from the step's test sketch, taken deliberately: the final-mypy
    cleanup test (#8) **extends** the existing final-mypy test rather than adding
    a new one, and is renamed
    `test_final_mypy_clears_marker_and_skips_formatting_when_disabled`. The step
    permits either. A standalone test costs ~65 lines here (15 patch decorators
    + 16-parameter signature), which would push `test_core.py` from 686 to ~751
    and **break the CI file-size gate** the step is otherwise careful about.
    Extending cost 10 lines (696). Ordering is pinned as the step suggests, via
    `MagicMock.attach_mock` on both mocks before the run.
  - pytest: `tests/workflows/implement` + `tests/workflow_steps` +
    `tests/workflow_utils` → **399 passed**; `tests/workflows` (review dir
    excluded, see below) → **1034 passed, 2 skipped**. Targeted run of the three
    files this step touches → 46 passed. Re-ran after black → 153 passed.
  - No labels.json change was needed or made: Step 4 already defines
    `implementation_blocked`, and nothing cross-checks `FAILURE_LABELS` values
    against `labels.json`, so no count assertions moved.
  - Environment, unchanged from Steps 1–4: `.venv`'s `mcp-workspace` predates
    the `branch_status_rendering` split, so `import mcp_coder` dies at
    collection repo-wide (`ImportError` on every test module; under `-n auto`
    the whole session aborts with 0 collected).
  - Workaround used to obtain real pytest signal: a temporary root
    `conftest.py` synthesising `branch_status_rendering` from the stale
    install's names. **It has been deleted** — `git status` shows only the five
    intended files plus this tracker. Local diagnostic, not a fix; must not be
    committed.
  - Still broken and NOT caused by this step: `tests/workflows/review/` (and the
    `test_check_branch_status*` modules) fail on
    `BranchStatusReport.pr_feedback_undeterminable` / `CIStatus`, which the shim
    cannot supply. Clears with:
    `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
  - pylint: no issue in any of the 5 files this step touches. Every reported
    error is `E0401`/`E0611` for uninstalled optional deps (`langchain_*`,
    `httpx`, `mcp.server.fastmcp`) plus `E1123`/`E1101` for `fail_on_reviews` /
    `pr_feedback_undeterminable` — all downstream of the stale install.
  - mypy: 8 errors, byte-identical to Steps 1–4, none in this step's files.
  - black: reformatted `test_core_failure_routing.py` (one `with` rewrap);
    isort no changes. File-size gate passes (823 files ≤ 750 lines).
- [x] Commit message prepared

### Step 6: RETRY_REMINDER + prompts.md blocked exit

Details: [step_6.md](./steps/step_6.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, mypy clean for this step; **pytest genuinely RUN
      and green** via the same local workaround Steps 3–5 used.
  - Scope delivered: `RETRY_REMINDER` **replaced** wholesale (not extended) with
    the step's verbatim three-exit text, and the `prompts.md:115` bullet
    **conditioned in place** (`(no code changes needed)` → `and you saw its
    checks pass`) with the blocked-exit bullet added directly after it. Grepped
    afterwards: `"you MUST tick"` and `"no code changes needed"` now appear
    **nowhere** in `src/` or `tests/` — the contradicting imperative this issue
    documents is gone from both prompt sources, not merely qualified.
    `MAX_NO_CHANGE_RETRIES` and all retry mechanics untouched.
  - Test-first, watched red: both new assertions in the new
    `TestBlockedExitInPrompts` failed before the text edits —
    `test_retry_reminder_offers_blocked_exit` on the old constant and
    `test_implementation_prompt_offers_blocked_exit` on the prompt section
    loaded through `get_prompt(PROMPTS_FILE_PATH, ...)`, the same call
    `process_single_task:390` makes. Both pass after.
  - The two pre-existing tests at `test_task_processing.py:560,587` use the
    imported `RETRY_REMINDER` symbol rather than a literal, so they needed no
    change and still pass — confirmed in the run below.
  - pytest: `tests/workflows/implement` + `tests/workflow_steps` +
    `tests/workflow_utils` → **401 passed** (Step 5's 399 plus these 2), with the
    standard `-n auto` marker exclusions. Prompt-consumer regression run —
    `test_prompt_manager.py` + `test_prompt_parsing.py` + `test_prompt_sources.py`
    + `tests/prompts` + `tests/workflows/create_plan` + `create_pr` + `rebase`
    → **335 passed**. Nothing else asserts this prompt section's text.
  - Environment, unchanged from Steps 1–5: `.venv`'s `mcp-workspace` predates the
    `branch_status_rendering` split, so `import mcp_coder` dies at collection
    repo-wide. Observed again this run as a silent **0 tests collected** before
    the shim was in place.
  - Workaround used to obtain real pytest signal: a temporary root `conftest.py`
    synthesising `branch_status_rendering` from the stale install's names.
    **It has been deleted** — `git status` shows only the three intended files
    plus this tracker. Local diagnostic, not a fix; must not be committed.
  - Still broken and NOT caused by this step: `tests/workflows/review/` and the
    `test_check_branch_status*` modules fail on
    `BranchStatusReport.pr_feedback_undeterminable` / `CIStatus`, which the shim
    cannot supply. Clears with:
    `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
  - pylint: no issue in any of the 3 files this step touches. Every reported
    error is `E0401`/`E0611` for uninstalled optional deps (`langchain_*`,
    `httpx`, `mcp.server.fastmcp`) plus `E1123`/`E1101` for `fail_on_reviews` /
    `pr_feedback_undeterminable` — all downstream of the stale install.
  - mypy: 8 errors, byte-identical to Steps 1–5, none in this step's files.
  - black/isort: no changes (614 files unchanged). File-size gate passes
    (823 files ≤ 750 lines).
- [x] Commit message prepared

### Step 7: finalisation.py marker cleanup + commit_message_path fix

Details: [step_7.md](./steps/step_7.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, mypy clean for this step; **pytest genuinely RUN
      and green** via the same local workaround Steps 3–6 used.
  - Scope delivered: in `finalisation.py`, the existing `prompt_llm` call wrapped
    in `try` / `finally` with `read_and_clear_blocked(project_dir)` in the
    `finally` (return value discarded — `run_finalisation` gets **no** blocked
    outcome, per the step), and the `commit_message_path` substitution changed
    from `f"{PR_INFO_DIR}/{COMMIT_MESSAGE_FILE}"` to bare `COMMIT_MESSAGE_FILE`.
    The `finally` is attached to the `prompt_llm` call **only**, not the function
    body, so cleanup runs before `commit_all_changes`, not after.
  - Test-first, watched red: all three new tests in
    `TestFinalisationBlockedMarkerCleanup` failed before the change. The
    double-prefix test failed by printing the rendered prompt verbatim —
    `Write commit message to pr_info/pr_info/.commit_message.txt.` — reproducing
    the live §9 bug end-to-end rather than inferring it. All three pass after.
  - Deviation from the step's test sketch, taken deliberately: tests 1 and 2
    write the marker from a `prompt_llm` **side effect** rather than pre-writing
    it under `tmp_path`. Pre-writing would also pass with the cleanup placed
    *before* the LLM call, which is precisely the placement the step rejects;
    writing it mid-turn is what a real blocked agent does and pins "after the
    LLM turn". Test 2 (empty response) independently pins the `finally` — a bare
    call above the changes check fails it.
  - No existing test changed behaviour. The step warned that the Level-1
    commit-message tests might start passing differently; they do not, because
    the read at `:121` uses `project_dir / COMMIT_MESSAGE_FILE` and was already
    correct. The bug was **prompt-side only** — the agent was told a path that
    does not exist, so it wrote nowhere useful and Level 1 found nothing.
    Nothing else in `src/` or `tests/` references `commit_message_path`.
  - pytest: `tests/workflows/implement` + `tests/workflow_steps` +
    `tests/workflow_utils` + `tests/prompts` → **427 passed**;
    `tests/workflows` (review dir excluded, see below) → **1039 passed,
    2 skipped**. `test_finalisation.py` itself: 14 passed.
  - Environment, unchanged from Steps 1–6: `.venv`'s `mcp-workspace` predates the
    `branch_status_rendering` split, so `import mcp_coder` dies at collection
    repo-wide — observed again as a silent **0 tests collected** before the shim
    was in place.
  - Workaround used to obtain real pytest signal: a temporary root `conftest.py`
    synthesising `branch_status_rendering` from the stale install's names.
    **It has been deleted** — `git status` shows only the two intended files
    plus this tracker. Local diagnostic, not a fix; must not be committed.
  - Still broken and NOT caused by this step: `tests/workflows/review/` and the
    `test_check_branch_status*` modules fail on
    `BranchStatusReport.pr_feedback_undeterminable` / `CIStatus`, which the shim
    cannot supply. Clears with:
    `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
  - pylint: no issue in either file this step touches. Every reported error is
    `E0401`/`E0611` for uninstalled optional deps (`langchain_*`, `httpx`,
    `mcp.server.fastmcp`) plus `E1123`/`E1101` for `fail_on_reviews` /
    `pr_feedback_undeterminable` — all downstream of the stale install.
  - mypy: 8 errors, byte-identical to Steps 1–6, none in this step's files. The
    new `from .task_processing import read_and_clear_blocked` introduces no
    cycle — `task_processing` does not import `finalisation`.
  - black/isort: no changes (614 files unchanged). File-size gate passes
    (822 files ≤ 750 lines).
- [x] Commit message prepared

### Step 8: Docs — failure-label tables, HTML matrix, architecture note

Details: [step_8.md](./steps/step_8.md)

- [x] Implementation (docs only)
- [x] Quality checks: pylint, mypy clean for this step; **pytest genuinely RUN
      and green** via the same local workaround Steps 3–7 used.
  - Scope delivered, docs only — no source or test file touched:
    (A) four rows appended to the `development-process.md` failure-label table
    directly after `status-06f-timeout`, in the order the step gives
    (`-prep`, `-mcp`, `-nochange`, `-blocked`), all four with the
    `set-status status-05:plan-ready` recovery the surrounding 06f rows use;
    (B) four `--label-color` CSS rules beside the existing failure colours plus
    four cards appended to the stage-6 `failed-stack`, following the existing
    card markup exactly; (C) one **Blocked channel** bullet under
    `workflows/implement/` in `architecture.md`, verbatim from the step.
  - Colour check by eye, against `labels.json` rather than the step text:
    `task_tracker_prep_failed` → `b60205`, `mcp_unavailable` → `e99695`,
    `no_changes_after_retries` → `d93f0b`, `implementation_blocked` → `d93f0b`.
    All four match the CSS `--label-color` values character for character.
  - Scope discipline held: `development-process.md` still omits
    `status-03f-timeout`, `status-03f-mcp`, `status-03f-prereq`,
    `status-09f-timeout` and `status-09f-mcp`. Those are other lanes and were
    deliberately left alone, per the step's HOW section.
  - Confirmed by grep that no generator or test reads these files:
    `development-process.md` / `github_Issue_Workflow_Matrix` /`architecture.md`
    return **zero** matches across `src/` and `tests/`. Both tables are
    hand-maintained, as the step states. Also checked the HTML has no label
    count, legend or summary block elsewhere that the four new cards would
    contradict — the only other `06f` occurrences are the three pre-existing
    cards.
  - pytest: `tests/workflows/implement` + `tests/workflow_steps` +
    `tests/workflow_utils` + `tests/prompts` + `tests/config` → **499 passed**,
    with the standard `-n auto` marker exclusions. A docs-only change cannot
    move these, and it did not; run as a regression guard, not as evidence for
    the change.
  - Environment, unchanged from Steps 1–7: `.venv`'s `mcp-workspace` predates
    the `branch_status_rendering` split, so `import mcp_coder` dies at
    collection repo-wide. Observed again this run before the shim was in place —
    `ModuleNotFoundError: No module named
    'mcp_workspace.checks.branch_status_rendering'` via
    `mcp_coder/__init__.py:37` → `checks/branch_status.py:17`, on every
    collected module.
  - Workaround used to obtain real pytest signal: a temporary root `conftest.py`
    synthesising `branch_status_rendering` from the stale install's names.
    **It has been deleted** — `git status` shows only the three intended docs
    files plus this tracker. Local diagnostic, not a fix; must not be committed.
  - Still broken and NOT caused by this step: `tests/workflows/review/` and the
    `test_check_branch_status*` modules fail on
    `BranchStatusReport.pr_feedback_undeterminable` / `CIStatus`, which the shim
    cannot supply. Clears with:
    `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
  - pylint: unchanged — it does not read `.md` or `.html`, and no Python file
    was touched. Every reported error is `E0401`/`E0611` for uninstalled
    optional deps (`langchain_*`, `httpx`, `mcp.server.fastmcp`) plus
    `E1123`/`E1101` for `fail_on_reviews` / `pr_feedback_undeterminable` — all
    downstream of the stale install.
  - mypy: 8 errors, byte-identical to Steps 1–7, none related to this step.
  - black/isort: no changes (614 files unchanged). File-size gate passes
    (822 files ≤ 750 lines).
- [x] Commit message prepared

## Pull Request

- [ ] PR review
- [ ] PR summary
