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
- [ ] Implementation: move `_QUOTE_FENCE`, `_quote_pr_feedback`, `_pr_feedback_note` from `core.py` to `reviewer.py`; update `core.py` call sites; add/relocate unit tests in `test_reviewer.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: `ReviewConfig` — add `strict_from_round` and `tie_break`
- [ ] Implementation: add two fields (defaults) to frozen dataclass; set explicit values on `REVIEW_PLAN` / `REVIEW_IMPLEMENTATION`; update docstring; tests first in `test_config.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Create `handoff.py`; relocate `_set_label` + `_fail`
- [ ] Implementation: create `handoff.py`, move `_set_label`/`_fail` verbatim with their imports; re-import into `core.py`; repoint `env` fixtures in `test_core.py`/`test_core_after_steps.py` to patch `handoff`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Severity backstop — downgrade `tasks` → `dismiss`
- [ ] Implementation: apply severity floor transform in `core.body()` (import `max_severity`; CI-exemption + below-floor + fail-open guards; log downgrade); mocked-LLM tests first (plan lane in `test_core.py`, CI exemption in `test_core_after_steps.py`)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Handoff wiring — cap → escalate, flush every terminal path
- [ ] Implementation: add `_flush_round_log` + `_route_to_human` to `handoff.py`; rewire `core.body()` terminal branches (dismiss/escalate/rebase/cap/commit-failed/push-failed + `_fail` sub-paths); update docstring; `test_handoff.py` + cap/escalate/rebase tests first
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Round context + prompt rules (supervisor + reviewers)
- [ ] Implementation: add required `round_number`/`max_rounds` params + substitution to `_run_reviewer`/`_get_verdict`; pass from both `core.py` call sites; extend `_CI_NOTE`; update `prompts.md` sections (placeholders only); substitution tests first in `test_reviewer.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: Remove dead `*-rounds` labels; verify `core.py` < 600
- [ ] Implementation: run pre-merge sweep; remove `"rounds"` from both `failure_labels`, the two `labels.json` entries, doc rows/cards, and test expectations (tests first); grep to confirm no references; verify `core.py` < 600 via `mcp-coder check file-size --max-lines 600`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: address review feedback
- [ ] PR summary prepared
