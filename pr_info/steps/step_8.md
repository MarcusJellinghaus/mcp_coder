# Step 8 — UI branch, cancel channel, shutdown hook, integration test, spike deletion

**Depends on:** Step 7 (and therefore all earlier steps).

Closes the loop: the event reaches the UI, the UI can cancel a pending approval, quitting does not
stall, and the whole path is proven end to end through the real agent. Then the spike is consumed
and deleted.

---

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/icoder/ui/app.py` | **modify** — `approval_request` branch, cancel channel, `on_unmount` |
| `tests/llm/providers/langchain/test_approval_integration.py` | **create** |
| `tests/icoder/test_app_pilot.py` | **modify** — UI branch + cancel + shutdown cases |
| `spikes/i3-1-approval/` | **delete** (8 files) |

## WHAT

```python
# icoder/ui/app.py
def _handle_stream_event(self, event, *, replay_mode=False) -> None:
    if event.get("type") == "approval_request":
        ...                      # early return, mirroring the permission_warning precedent
        return

def action_cancel_stream(self) -> None:
    """Cancel the stream AND any pending approval (the direct UI→engine channel)."""

def on_unmount(self) -> None:
    """Cancel pending approvals so quitting never stalls on the 300s inactivity timeout."""
```

## HOW

* **`approval_request` branch** — copy the shape of the existing `permission_warning` early return
  at the top of `_handle_stream_event`. Until I3.3/#1046 lands, resolve immediately and
  fail-closed:

  ```python
  approval_id = str(event.get("approval_id", ""))
  # I3.3/#1046 replaces this with the modal (ModalScreen[ApprovalDecision]).
  # Until then, fail closed: a live `ask` rule would otherwise wedge the turn.
  self._core.resolve_pending(approval_id, ApprovalDecision("deny", "once"))
  return
  ```

  Mark it with a `TODO(#1046)`. Importing `ApprovalDecision` from `icoder.permissions.approval`
  into `icoder.ui` is legal (the leaf contract forbids the *reverse* direction).
* **Cancel channel** — `action_cancel_stream` keeps `self._cancel_event.set()` **and** adds
  `self._core.cancel_pending_approvals()`. Comment why (FINDINGS §4): all three generic paths are
  gated on an event arriving from the generator and a blocked interceptor emits none;
  `GeneratorExit` is provably *unreachable*, not merely inert. They stay wired as the
  post-resolution backstop.
* **Shutdown hook** — add `on_unmount` calling the same `cancel_pending_approvals()`. `_stream_llm`
  runs via `run_worker(..., thread=True)` and a thread blocked in `q.get` cannot be interrupted;
  nothing in `app.py` overrides `on_unmount` or `action_quit` today.
* **Do not** add a modal, scopes, or any persist write-back — that is #1046.
* **Spike deletion** — before deleting, confirm the load-bearing rationale from
  `FINDINGS.md` §2 (loop handle), §3 (pause over keepalives), §4 (direct cancel channel), §5
  (stale-`q`) and §10 (deny `tool_call_id`) is present in production docstrings/comments from
  Steps 2, 4 and 5. Then delete the directory with `delete_directory(recursive=True)`.

## ALGORITHM

```
# integration test, real agent path
build FakeChatModel + gated MCP-shaped tool + gateway(config with an `ask` rule) + ApprovalEngine
run _ask_agent_stream(..., approval_bridge=engine) on the consumer thread
read events until type == "approval_request"; capture approval_id
engine.resolve_pending(approval_id, ApprovalDecision("allow", "once"))   # from the test thread
assert the tool ran, the turn completed, and the model was invoked twice
```

## DATA

* The `approval_request` event reaching `_handle_stream_event` is
  `{"type","approval_id","tool_name","args","source"}` with `source` a plain string.
* It **necessarily arrives after** `tool_use_start` (the interceptor runs inside the tool coroutine
  and `on_tool_start` fires first) — assert this ordering in the integration test; #1045 flags it
  as a scheduling claim that was never verified at HEAD, so verify it here. A wrong result is
  cosmetic only (a modal for a row not yet drawn) — report it, do not block on it.
* R17 stands: there is **no** correlation key between `approval_request` and the on-screen tool
  unit. Do not invent one.

## TESTS (write first)

Integration (`tests/llm/providers/langchain/test_approval_integration.py`, real langgraph via
`pytest.importorskip`, session storage already isolated by the directory's autouse `_tmp_home`
fixture — R12):

1. **Allow:** gated call blocks, is approved, then runs; the agent continues; nothing raises.
2. **Deny:** returns a clean `ToolMessage(status="error")` carrying the real `tool_call_id`; the
   agent continues.
3. **Ungated calls are not blocked** behind a pending approval.
4. **Cancel-while-pending:** `cancel_all()` → the turn unwinds without re-planning
   (`model.invoke_count == 1`), `thread.is_alive() is False` after the 5s join, nothing on stderr,
   `error_holder` empty.
5. **Backstop still works:** with no approval pending, `cancel_event` / generator close still stop
   the turn.
6. **Ordering:** `approval_request` arrives after that tool's `tool_use_start`.

UI (`tests/icoder/test_app_pilot.py`, `textual_integration`):

7. An `approval_request` event routes to `resolve_pending` and renders nothing; `ResponseAssembler`
   and the event log are unaffected.
8. `action_cancel_stream` calls `cancel_pending_approvals()` **and** sets `_cancel_event`.
9. Unmounting the app calls `cancel_pending_approvals()`.

## CHECKS

`run_pylint_check`, `run_mypy_check`, `run_pytest_check` (fast selection) **plus**
`run_pytest_check(markers=["textual_integration"], extra_args=["-n","auto"])`, **plus**
`run_lint_imports_check`. After deleting the spike, re-run the full fast suite to confirm nothing
imported it.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (§2.3, §2.11) and `pr_info/steps/step_8.md`, then implement
> Step 8 only.
>
> In `src/mcp_coder/icoder/ui/app.py`: add an `approval_request` early-return branch to
> `_handle_stream_event` (mirroring the existing `permission_warning` precedent) that, until
> I3.3/#1046 lands, resolves the approval immediately with `ApprovalDecision("deny", "once")` via
> `self._core.resolve_pending` — mark it `TODO(#1046)`. Make `action_cancel_stream` also call
> `self._core.cancel_pending_approvals()`, and add an `on_unmount` hook that does the same so
> quitting with an approval pending does not stall on the 300s inactivity timeout. Comment why the
> direct channel is required: all three generic cancel paths are inert while an interceptor is
> blocked, and `GeneratorExit` is unreachable, not merely inert. Do not add a modal, scopes, or any
> persist write-back — that is #1046.
>
> Write `tests/llm/providers/langchain/test_approval_integration.py` (cases 1–6 in the step, real
> agent path, reusing the Step 1 harness) and the three UI pilot cases first.
>
> Then, once you have confirmed that the FINDINGS §2/§3/§4/§5/§10 rationale is present in the
> production docstrings and comments added by Steps 2, 4 and 5, delete `spikes/i3-1-approval/`
> (D9 consume-and-delete handoff) and re-run the full fast suite.
>
> Use MCP tools only (`delete_directory` with `recursive=True` for the spike). Finish with
> `run_pylint_check`, `run_pytest_check` (fast selection **and** the `textual_integration` marker),
> `run_mypy_check` and `run_lint_imports_check` all green, then one commit.
