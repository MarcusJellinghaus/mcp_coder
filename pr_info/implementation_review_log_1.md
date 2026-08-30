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
