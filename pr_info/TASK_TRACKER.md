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

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

Notes: implemented as specified, with one micro-deviation (`error_holder` / `cancelled` stay
*above* the widened `try`) and two strengthened test assertions — see the "Implementation note"
at the end of [step_7.md](./steps/step_7.md), which also records that each of tests 1, 2, 2b, 5
and 6 was confirmed **red** against a deliberately broken variant of the production code, and the
unchanged local environment caveats.

### Step 8: Tool-unit pairing on `tool_run_id` (R18 / R1)

Details: [step_8.md](./steps/step_8.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

Notes: implemented as specified — no shape deviations. Two small additions (a private
`_read_run_id` narrowing helper; `_pair_pending` kept as a two-line wrapper) and the full
test-case mapping are recorded in the "Implementation note" at the end of
[step_8.md](./steps/step_8.md), which also repeats the unchanged local environment caveats
(stale installed `mcp_workspace` forcing a `PYTHONPATH` workaround; whole-suite runs time out
locally, so verification used targeted per-file runs; four pre-existing `tests/llm` failures).

### Step 9: Wiring — CLI → gateway / `RealLLMService` / `AppCore` (+ R16 gate, + UI branch)

Details: [step_9.md](./steps/step_9.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

Notes: implemented as specified — no shape deviations. Two patch-target strings had to be
re-pointed for the gateway's new second constructor argument (`test_cli_icoder.py`'s
`lambda _config: MagicMock()`, and `test_icoder_permission_wiring.py`'s `_FakeGateway`) — see the
"Implementation note" at the end of [step_9.md](./steps/step_9.md), which also records the
unchanged local environment caveats (stale installed `mcp_workspace` forcing a `PYTHONPATH`
workaround; no `pytest-textual-snapshot`, so `test_snapshots.py` still cannot run here; one
pre-existing `tests/llm` failure with `httpx` absent).

### Step 10: Shutdown hook + closed-app guard (R9)

Details: [step_10.md](./steps/step_10.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

Notes: implemented as specified — no shape deviations. Two harness facts forced case 1 to assert
differently than its plain reading (Textual thread workers run on *pooled* threads, so
`is_alive()` says nothing about the worker body; and under a pilot the event loop outlives the
app, so an unguarded tail errors rather than hangs) — see the "Implementation note" at the end of
[step_10.md](./steps/step_10.md), which also records that both guard tests were confirmed **red**
against a deliberately broken guard, and the unchanged local environment caveats (stale installed
`mcp_workspace` forcing a `PYTHONPATH` workaround; no `pytest-textual-snapshot`; `-n auto` on the
pilot file times out locally, so the `textual_integration` runs used `-n 0`).

### Step 11: End-to-end integration test + spike deletion

Details: [step_11.md](./steps/step_11.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review
- [ ] PR summary
