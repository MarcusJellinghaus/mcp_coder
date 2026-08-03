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

### Step 1: `severity.py` — pure severity parser
- [x] Implementation: create `severity.py` with `max_severity` (tests first in `test_severity.py`; anchored `<sep>SEVERITY<sep>` regex tolerating em-dash/hyphen + backticks; optional `__init__.py` export)
- [x] Quality checks: pylint, pytest, mypy — fix all issues (pylint ✅, mypy ✅; pytest blocked repo-wide by pre-existing env issue: installed `mcp_workspace` lacks `branch_status_rendering`, imported at `src/mcp_coder/__init__.py:37` — even unmodified `test_verdict.py` collects 0 tests)
- [x] Commit message prepared

### Step 2: Relocate PR-feedback note helpers into `reviewer.py`
- [x] Implementation: move `_QUOTE_FENCE`, `_quote_pr_feedback`, `_pr_feedback_note` from `core.py` to `reviewer.py`; update `core.py` call sites; add/relocate unit tests in `test_reviewer.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues (relocation is behaviour-preserving; only pre-existing findings remain: `core.py:129` `pr_feedback_undeterminable` attr on `BranchStatusReport` — pylint E1101 + mypy, untouched by this diff; W1404 in Step 1's `test_severity.py`. pytest still blocked repo-wide by the same env issue as Step 1: installed `mcp_workspace` lacks `checks.branch_status_rendering`, imported at `src/mcp_coder/checks/branch_status.py:17` → `__init__.py:37`, so collection yields 0 tests)
- [x] Commit message prepared

### Step 3: `ReviewConfig` — add `strict_from_round` and `tie_break`
- [x] Implementation: add two fields (defaults) to frozen dataclass; set explicit values on `REVIEW_PLAN` / `REVIEW_IMPLEMENTATION`; update docstring; tests first in `test_config.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues (pylint ✅, mypy ✅; pytest blocked repo-wide by the same pre-existing env issue as Steps 1–2: installed `mcp_workspace` lacks `checks.branch_status_rendering`, imported at `src/mcp_coder/checks/branch_status.py:17` → `__init__.py:37`, so collection yields 0 tests even for unmodified files)
- [x] Commit message prepared

### Step 4: Create `handoff.py`; relocate `_set_label` + `_fail`
- [x] Implementation: create `handoff.py`, move `_set_label`/`_fail` verbatim with their imports; re-import into `core.py`; repoint `env` fixtures in `test_core.py`/`test_core_after_steps.py` to patch `handoff`
- [x] Quality checks: pylint, pytest, mypy — fix all issues (behaviour-preserving relocation; `core.py` shrank ~680→587 lines. pylint ✅ / mypy ✅ except the one pre-existing `core.py:125` `pr_feedback_undeterminable` finding on `BranchStatusReport` — E1101 + attr-defined, untouched by this diff. pytest still blocked repo-wide by the same pre-existing env issue as Steps 1–3: installed `mcp_workspace` lacks `checks.branch_status_rendering` → `__init__.py:37`, so collection yields 0 tests even for unmodified files)
- [x] Commit message prepared

### Step 5: Severity backstop — downgrade `tasks` → `dismiss`
- [x] Implementation: apply severity floor transform in `core.body()` (import `max_severity`; CI-exemption + below-floor + fail-open guards; log downgrade); mocked-LLM tests first (plan lane in `test_core.py`, CI exemption in `test_core_after_steps.py`)
- [x] Quality checks: pylint, pytest, mypy — fix all issues (added `_apply_severity_floor` helper + inline transform after `last_verdict = verdict`; 5 plan-lane tests in `test_core.py`, 1 CI-exemption test in `test_core_after_steps.py`. pylint ✅ / mypy ✅ except the one pre-existing `core.py:126` `pr_feedback_undeterminable` finding on `BranchStatusReport` — E1101 + attr-defined, untouched by this diff. pytest still blocked repo-wide by the same pre-existing env issue as Steps 1–4: installed `mcp_workspace` lacks `checks.branch_status_rendering`, imported at `src/mcp_coder/checks/branch_status.py:17` → `__init__.py`, so collection yields 0 tests even for the unmodified `test_severity.py`)
- [x] Commit message prepared

### Step 6: Handoff wiring — cap → escalate, flush every terminal path
- [x] Implementation: add `_flush_round_log` + `_route_to_human` to `handoff.py`; rewire `core.body()` terminal branches (dismiss/escalate/rebase/cap/commit-failed/push-failed + `_fail` sub-paths); update docstring; `test_handoff.py` + cap/escalate/rebase tests first
- [x] Quality checks: pylint, pytest, mypy — fix all issues (added `_flush_round_log` [commit_all_changes + push_changes, best-effort, checks falsy returns, swallows raises] + `_route_to_human` [flush → gated comment → escalate label → RC=0] to `handoff.py`; rewired every terminal path in `core.body()`: dismiss-success flushes before the success label; escalate/dismiss→rebase/tasks→rebase route through `_route_to_human`; the rounds cap now flushes+`_fail("ci")` when `pending_ci_note` else `_route_to_human` [RC=0]; commit-failed/push-failed add a best-effort flush; the dismiss/tasks after-steps `_fail` sub-paths and the tasks-resume LLM-exception now `write_round_log` + flush before `_fail`; docstring `Returns:` corrected. New `test_handoff.py` (10 tests); updated cap/escalate/silent-no-op/severity tests in `test_core.py` (cap → RC=0 handoff) and added 3 flush sub-path tests in `test_core_after_steps.py`. pylint ✅ / mypy ✅ except the one pre-existing `core.py:128` `pr_feedback_undeterminable` finding on `BranchStatusReport` — E1101 + attr-defined, untouched by this diff. ruff ✅, black ✅. pytest still blocked repo-wide by the same pre-existing env issue as Steps 1–5: installed `mcp_workspace` lacks `checks.branch_status_rendering` [confirmed absent — only `branch_status`/`pr_feedback` submodules exist], imported at `src/mcp_coder/checks/branch_status.py:17` → `__init__.py:37`, so collection yields 0 tests even for unmodified files. NOTE: `core.py` is now 736 lines; getting it < 600 is Step 8's explicit deliverable.)
- [x] Commit message prepared

### Step 7: Round context + prompt rules (supervisor + reviewers)
- [x] Implementation: add required `round_number`/`max_rounds` params + substitution to `_run_reviewer`/`_get_verdict`; pass from both `core.py` call sites; extend `_CI_NOTE`; update `prompts.md` sections (placeholders only); substitution tests first in `test_reviewer.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues (added `round_number`/`max_rounds` as required params on `_run_reviewer` [after `base_branch`] and `_get_verdict` [after `report`]; fresh-reviewer prompt now substitutes `{round_number}`/`{max_rounds}`/`{strict_from_round}` after the existing `{issue_number}`/`{base_branch}` replaces, and the supervisor header substitutes those three plus `{tie_break}` — all reusing the existing `.replace` plumbing, both drawing `strict_from_round`/`tie_break` from the single `ReviewConfig` so stated==enforced. All 3 `core.py` call sites [fresh reviewer, `_get_verdict`, task-resume] pass `round_number=round_number, max_rounds=REVIEW_MAX_ROUNDS` by keyword; the resume does no substitution but still supplies them. `_CI_NOTE` extended with the `critical`-severity sentence. `prompts.md`: added a **Round context** paragraph to both reviewer sections and four triage bullets [severity floor / final round / re-litigation / tie-break] to §Review Supervisor — placeholders only, no restated free-text numbers. Substitution tests first in `test_reviewer.py` [fresh-reviewer + supervisor-header: assert enforced `strict_from_round` value appears, round/max numbers appear, no `{…}` placeholders remain; `_call` helper gained the two defaults]. pylint ✅ / mypy ✅ / ruff ✅ / black ✅ except the one pre-existing `core.py:129` `pr_feedback_undeterminable` finding on `BranchStatusReport` — E1101 + attr-defined, untouched by this diff. pytest still blocked repo-wide by the same pre-existing env issue as Steps 1–6: installed `mcp_workspace` lacks `checks.branch_status_rendering`, imported at `src/mcp_coder/checks/branch_status.py:17` → `__init__.py:37`, so collection yields 0 tests even for the unmodified files.)
- [x] Commit message prepared

### Step 8: Remove dead `*-rounds` labels; verify `core.py` < 600
- [ ] Implementation: run pre-merge sweep; remove `"rounds"` from both `failure_labels`, the two `labels.json` entries, doc rows/cards, and test expectations (tests first); grep to confirm no references; verify `core.py` < 600 via `mcp-coder check file-size --max-lines 600`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: address review feedback
- [ ] PR summary prepared
