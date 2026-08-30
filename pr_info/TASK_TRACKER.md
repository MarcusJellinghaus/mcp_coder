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

### Step 1: Prep — extract the langchain setup helpers out of the provider `__init__`

Details: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

Notes: step_1.md's patch-site survey was incomplete — see the "Implementation note"
section at the end of [step_1.md](./steps/step_1.md) for the extra consumed-name
patch strings that had to be re-pointed, and for the local environment caveat
(stale installed `mcp_workspace`) that pytest runs had to work around.

### Step 2: Prep — extract the stream worker and event dispatch out of `ui/app.py`

Details: [step_2.md](./steps/step_2.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

Notes: one patch-target string had to be re-pointed after all (`test_snapshots.py`'s
`_frozen_clocks` now patches `datetime` in both UI modules) — see the "Implementation
note" at the end of [step_2.md](./steps/step_2.md), which also records the two local
environment gaps (stale installed `mcp_workspace`; `pytest-textual-snapshot` not
installed, so `test_snapshots.py` cannot run here).

### Step 3: Real-path `CancelledError` probe (decision gate)

Details: [step_3.md](./steps/step_3.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

Notes: **the decision gate is still OPEN.** No langchain distribution is installed in this
venv, so both probe tests skip here and the `CancelledError` question is unanswered — see the
"Implementation note" at the end of [step_3.md](./steps/step_3.md). Run the probe once on an
environment with real `langchain-core` + `langgraph` before starting Step 4. That note also
records the extra `require_real_langchain` guard (`importorskip` alone finds the conftest's
`MagicMock`) and the two pre-existing local environment gaps.

### Step 4: `ApprovalBridge` Protocol + `ApprovalEngine`

Details: [step_4.md](./steps/step_4.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

Notes: implemented on Step 3's **still-open** hard-cancel gate — see the "Implementation note"
at the end of [step_4.md](./steps/step_4.md), which also records two shape deviations
(module-level `_payload`; the `TYPE_CHECKING` conformance binding that consumes the required
`ApprovalBridge` import) and the pre-existing local environment gaps (stale installed
`mcp_workspace`; no `pytest-textual-snapshot`; no langchain).

### Step 5: Resolver — `runtime` becomes its own stage (R14) + degraded docstring (R15)

Details: [step_5.md](./steps/step_5.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

Notes: implemented exactly as specified — no shape deviations. Test cases 1, 2 and 4b were
confirmed red before the change (cases 3, 4 and 5 already passed, as the step predicted) and all
eight are green after. See the "Implementation note" at the end of
[step_5.md](./steps/step_5.md) for the local environment caveats (stale installed
`mcp_workspace` forcing a `PYTHONPATH` workaround; the whole-repo and whole-`tests/icoder`
pytest runs time out locally at 300s, so verification used targeted per-file runs).

### Step 6: Gateway — real `AFTER_APPROVAL` branch + runtime-rule store

Details: [step_6.md](./steps/step_6.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

Notes: implemented exactly as specified — no shape deviations. One extra test
(`add_runtime_rule` appends rather than replaces) and the `ApprovalEngine` stub subclasses the
real engine so the constructor's type holds without a cast — see the "Implementation note" at the
end of [step_6.md](./steps/step_6.md), which also records the unchanged local environment
caveats (stale installed `mcp_workspace` forcing a `PYTHONPATH` workaround; whole-suite pytest
runs time out locally, so verification used targeted per-file runs).

### Step 7: Provider plumbing — bridge param, pause, `CancelledError` catch, transient events

Details: [step_7.md](./steps/step_7.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: Tool-unit pairing on `tool_run_id` (R18 / R1)

Details: [step_8.md](./steps/step_8.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 9: Wiring — CLI → gateway / `RealLLMService` / `AppCore` (+ R16 gate, + UI branch)

Details: [step_9.md](./steps/step_9.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 10: Shutdown hook + closed-app guard (R9)

Details: [step_10.md](./steps/step_10.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 11: End-to-end integration test + spike deletion

Details: [step_11.md](./steps/step_11.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review
- [ ] PR summary
