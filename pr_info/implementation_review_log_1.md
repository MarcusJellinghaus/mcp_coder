# review-implementation review log 1

## Round 1 — 2026-08-30
**Findings**:
I'll start by gathering context in parallel.Now let me read the core implementation files.`src/mcp_coder/icoder/permissions/approval.py:266` — medium — TOCTOU between the `_cancelled`/`_emit` guard and the registry insert: `cancel_all()` that reads `self._loop` while it is still `None` (the turn's first approval) schedules no cancellation, and a `detach()` landing in the same window clears `_pending` before the entry is inserted; either leaves the interceptor parked on a future nothing can resolve while both streaming timeouts are suspended. A re-check of `_cancelled`/`_emit` after the insert (cancelling the fresh future when it fails) closes the window.

`src/mcp_coder/llm/types.py:101` — medium — the documented `approval_request` shape uses key `"tool"`, but the only emitter (`approval.py::_payload`) writes `"tool_name"`; the `"source"` field it also emits is undocumented. This is the contract #1046 will code against.

`src/mcp_coder/icoder/permissions/approval.py:257` — low — `request_approval`'s docstring documents `source` as e.g. `"layer:project"`, while the only producer (`gateway.py::_source_label`) emits the bare layer name (`"project"`), `"frame"` or `"default"`.

`src/mcp_coder/llm/providers/langchain/__init__.py:394` — low — the `_is_node_cancelled(exc)` branch inside `_run`'s `except Exception` is unreachable: `agent.py::run_agent_stream` already converts `NodeCancelledError` to `asyncio.CancelledError` before it can escape, so the preceding `except asyncio.CancelledError` always wins.

Note (not a finding): the local venv cannot import `mcp_workspace.checks.branch_status_rendering`, so `src/mcp_coder/__init__.py` fails at import and I could not execute pytest or mypy here; this is a pre-existing environment break unrelated to the diff. `lint-imports` (21/21 contracts kept) and `check file-size` (750) were run and pass.
**Decisions**:
Verdict(decision='tasks', tasks=['In src/mcp_coder/icoder/permissions/approval.py around line 266, close the TOCTOU window: after inserting the pending entry into the registry, re-check `_cancelled`/`_emit` and, if either indicates the turn was cancelled or detached in the meantime, cancel/resolve the freshly created future so the interceptor cannot park on a future nothing will resolve.', 'In src/mcp_coder/llm/types.py around line 101, correct the documented `approval_request` payload shape to match the only emitter (`approval.py::_payload`): use key `"tool_name"` instead of `"tool"`, and document the `"source"` field that is also emitted.', 'In src/mcp_coder/icoder/permissions/approval.py around line 257, fix `request_approval`\'s docstring for `source` so the documented examples match what `gateway.py::_source_label` actually produces (bare layer name such as `"project"`, plus `"frame"` and `"default"`), not `"layer:project"`.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-08-30
**Findings**:
I'll gather context systematically. Starting with the knowledge base, the issue, and the plan files in parallel.I gathered the knowledge base, issue #1045 (+ epic/design refs), `pr_info/steps/*`, and computed the branch diff against `origin/main` myself. The diff contains substantial implementation (engine, seam Protocol, gateway/resolver changes, provider plumbing, UI split, wiring, tests). Verification run locally: `lint-imports` 21/21 kept, `check file-size` clean, `mypy --strict` and `pylint` show only pre-existing environment breakages (stale installed `mcp_workspace`, langchain/httpx absent) — no issues attributable to the diff; `pytest` could not run at all for the same environment reason.

`src/mcp_coder/icoder/ui/stream_view.py:87` — medium — `on_unmount` cancels pending approvals but never signals the streaming worker, so quitting during an ordinary approval-free turn leaves the non-daemon worker draining the whole turn (up to the 300s inactivity timeout) while `concurrent.futures`' atexit hook holds the process open; setting `_cancel_event` here would break the loop at the next event and reach the provider's `GeneratorExit`/`cancel.set()` path.

`src/mcp_coder/icoder/core/app_core.py:277` — low — the R16 gate reads `ApprovalEngine.cancelled`, which `on_unmount` sets on *every* quit, so a turn that completes normally while the app is shutting down silently loses both `llm_request_end` and its `store_session` record.

`src/mcp_coder/llm/providers/langchain/__init__.py:394` — low — the `_is_node_cancelled(exc)` branch inside `_run`'s `except Exception` is dead: `agent.py::run_agent_stream:484-488` already converts `NodeCancelledError` to `asyncio.CancelledError`, which the preceding `except asyncio.CancelledError` always catches (round-1 finding, not actioned).

`src/mcp_coder/icoder/permissions/approval.py:277` — low — the round-1 TOCTOU fix (re-check `_cancelled`/`is_attached()` after the registry insert and cancel the fresh future) has no test; nothing pins the behaviour it was added to guarantee.

`tests/icoder/test_permissions_approval.py:39` — low — the engine tests feed and assert `source="layer:project"`, a shape `gateway._source_label` cannot produce (it emits the bare layer name, `"frame"` or `"default"`), so the round-1 docstring correction is not backed by the tests.
**Decisions**:
Verdict(decision='tasks', tasks=["In src/mcp_coder/icoder/ui/stream_view.py around line 87, make `on_unmount` also signal the streaming worker (set `_cancel_event` alongside cancelling pending approvals) so quitting during an approval-free turn breaks the event loop promptly and reaches the provider's GeneratorExit/cancel path instead of draining the turn until the inactivity timeout.", "In src/mcp_coder/icoder/core/app_core.py around line 277, stop using `ApprovalEngine.cancelled` as the R16 gate for turn completion: distinguish 'this turn was cancelled' from 'the app is shutting down' so a turn that finishes normally during quit still emits `llm_request_end` and writes its `store_session` record.", 'Add a test in tests/icoder/test_permissions_approval.py covering the TOCTOU fix at src/mcp_coder/icoder/permissions/approval.py:277 — assert that a cancel/detach landing after the pending-entry insert results in the freshly created future being cancelled rather than left unresolved.', 'Update tests/icoder/test_permissions_approval.py (around line 39 and other occurrences) to use the source shapes `gateway._source_label` actually emits — the bare layer name (e.g. `"project"`), `"frame"`, or `"default"` — instead of `"layer:project"`, so the tests match the corrected contract.'], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-08-30
**Findings**:
I'll start by gathering context in parallel.`src/mcp_coder/icoder/permissions/approval.py:383` — medium — `cancel_all()` calls `loop.call_soon_threadsafe` with no `RuntimeError` guard, unlike `detach()` (line 213) which documents and catches exactly this hazard; `_loop` stays bound to the agent loop until `detach()` runs in the provider's `finally`, so between `asyncio.run` closing that loop and `detach()` nulling it there is a real (if narrow) window in which a Ctrl+C (`action_cancel_stream`) or a quit (`on_unmount`) raises `RuntimeError: Event loop is closed` on the Textual thread — uncaught, and in the `on_unmount` case mid-shutdown.

`src/mcp_coder/icoder/permissions/approval.py:314` — low — `request_approval`'s `finally` calls `_emit_front()` unconditionally for the surviving front entry, so if a *non-front* approval ever completes while the front is still parked (e.g. its interceptor coroutine is cancelled by langgraph rather than by `cancel_all`/`detach`, both of which are guarded), the front's `approval_request` is emitted a second time with the same `approval_id`, breaking the "exactly one in flight" guarantee I3.3 renders against.

`src/mcp_coder/llm/providers/langchain/__init__.py:394` — low — the `_is_node_cancelled(exc)` branch in `_run`'s `except Exception` is dead code: `agent.py::run_agent_stream:483-488` already converts `NodeCancelledError` to `asyncio.CancelledError`, which the preceding clause catches (reported in rounds 1 and 2, not actioned).

*Verification note (not a finding): `lint-imports` passes 21/21 and `check file-size --max-lines 750` is clean. `pytest`/`mypy`/`pylint` cannot execute in this workspace — `src/mcp_coder/__init__.py` fails to import because the installed `mcp_workspace` lacks `checks.branch_status_rendering`. That break is pre-existing and unrelated to this diff.*
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
rebase-needed
**Escalate reason**: rebase
