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

### Step 1: Types & persistence backfill

Enums (`LivenessRule`, `SessionAction`) + frozen dataclasses (`DetectionSignals`, `LivenessVerdict`, `IssueState`, `Transition`, `Decision`, `SessionAssessment` with serializer stubs); `VSCodeClaudeSession` gains `last_active`/`last_active_rule`; `load_sessions`/`build_session` backfill; export from `__init__.py`. See [step_1.md](./steps/step_1.md).

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Liveness layer (`assess_liveness`) — pure

Create `assessment.py` with pure `assess_liveness(signals) -> LivenessVerdict`; full rule-matrix unit tests (no Windows); export. See [step_2.md](./steps/step_2.md).

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Issue-state + transition + decision + composition (`assess_session`) — pure

Add `IssueFacts`, `assess_issue_state`, `assess_transition`, `decide` (full git-status safety matrix), composer `assess_session`; finalise serializer; typed destructive-invariant test. See [step_3.md](./steps/step_3.md).

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Detection snapshot + `gather_signals` (Windows / IO boundary)

Create `detection.py` with `DetectionSnapshot`, `capture_detection_snapshot` (all 3 caches at one instant), `gather_signals` (computes `directory_empty`/`within_grace`); mocked psutil/win32 tests; export. See [step_4.md](./steps/step_4.md).

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: `_issue_facts` helper + `assess_issue_state` wiring

Extract `get_stale_sessions` eligibility block into `_issue_facts` (preserve staleness short-circuit + individual-issue API fallback), producing frozen `IssueFacts`. See [step_5.md](./steps/step_5.md).

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5b: `build_assessments` + `apply_assessments` orchestration

Read-only `build_assessments` (snapshot once, gather+assess each session) and apply-only `apply_assessments` (PID refresh + `last_active`); thin `build_active_session_set` wrapper; wire launch/status entrypoints with green-state `active_set` shim + `prior_last_active`. See [step_5b.md](./steps/step_5b.md).

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Cleanup migration

`get_stale_sessions`/`cleanup_stale_sessions` consume `assessments` (+ call site); deletion ordering fix; lock-failure veto (never `remove_session` on failed delete); `.to_be_deleted` retry loop consumes assessment. See [step_6.md](./steps/step_6.md).

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Restart migration (zombie / remove-missing)

`restart_closed_sessions` consumes `assessments` (+ call site); branch on verdict/decision (KEEP_ACTIVE/INVESTIGATE_ZOMBIE skip, REMOVE_MISSING, RESTART); branch skip-reasons stay local. See [step_7.md](./steps/step_7.md).

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: Status migration (enriched column, write-free)

`display_status_table` consumes `assessments` (+ call site); enriched `VSCode`/`Next Action` columns via shared serializer; retire `active_set` shim (keep wrapper); confirm write-free. See [step_8.md](./steps/step_8.md).

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 9: Audit trail + transition/decision logging

Create `audit.py` (global file, 50-run ring buffer, atomic write); `apply_assessments` writes one run-block when `write_audit=True`; decision/transition log lines. See [step_9.md](./steps/step_9.md).

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 10: `--explain` flag (on-demand transparency)

Add `--explain` (store_true) to vscodeclaude CLI; `render_explain` over already-built assessments via `to_explain()` (no writes); update `docs/coordinator-vscodeclaude.md` Options table. See [step_10.md](./steps/step_10.md).

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Address PR review feedback
- [ ] Write PR summary
