# Step 8 — Shutdown hook, integration test, spike deletion

**Depends on:** Step 7 (and therefore all earlier steps).

Closes the loop: quitting with an approval pending does not stall, and the whole path is proven
end to end through the real agent. Then the spike is consumed and deleted.

The `approval_request` branch, its interim fail-closed deny and the direct cancel channel moved
into **Step 7** — they must land in the same commit as the engine wiring, or that commit ships an
app whose first `ask`-gated call wedges the turn permanently.

---

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/icoder/ui/app.py` | **modify** — `on_unmount` hook + closed-app guard in `_stream_llm` |
| `tests/llm/providers/langchain/test_approval_integration.py` | **create** |
| `tests/icoder/test_app_pilot.py` | **modify** — shutdown case |
| `spikes/i3-1-approval/` | **delete** (8 files) |

## WHAT

```python
# icoder/ui/app.py
def on_unmount(self) -> None:
    """Cancel pending approvals so quitting never stalls on the 300s inactivity timeout."""

def _call_from_thread_if_running(self, callback, *args) -> None:
    """Run *callback* on the UI thread, or drop it when the app is shutting down."""
```

## HOW

* **Shutdown hook** — add `on_unmount` calling `self._core.cancel_pending_approvals()`.
  `_stream_llm` runs via `run_worker(..., thread=True)` and a thread blocked in `q.get` cannot be
  interrupted; nothing in `app.py` overrides `on_unmount` or `action_quit` today.
* **Closed-app guard — the other half of R9, and the part the hook alone does not give you.**
  Cancelling the futures only *starts* the unwind; the worker thread still has to finish, and its
  tail runs `call_from_thread` against an app that is already shutting down. `App._shutdown()`
  dispatches `Unmount` **after** `_close_all()` / `_close_messages()`, so by the time the unwound
  worker reaches `_stream_llm`'s `finally` — `self.call_from_thread(self._reset_busy_indicator)`
  at `ui/app.py:313`, on the `elif not _error_handled` branch, since `on_unmount` does not set
  `_cancel_event` — the message pump may be gone. `call_from_thread` schedules onto `self._loop`
  and blocks on the result; on a stopped-but-not-closed loop that callback never runs and the
  worker blocks **forever**. Textual's thread workers run in a `ThreadPoolExecutor`, whose threads
  are non-daemon and are joined by `concurrent.futures`' atexit hook, so that is a hung process,
  not a hung thread.
  Route **every** `call_from_thread` in `_stream_llm` (the `except` block, the `finally` block and
  the per-event dispatch) through one small helper that no-ops once the app is shutting down —
  e.g. an `on_unmount`-set `threading.Event` (`self._shutting_down`), checked before the call, with
  `RuntimeError` from `call_from_thread` caught and logged as the race backstop. Do not swallow
  other exceptions.
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
7. **Interim deny wording:** the deny `ToolMessage` produced by the `ui/app.py` auto-deny carries
   `_DENY_NO_UI`, **not** the gateway's `_DENY_USER` text — no user was asked.

UI (`tests/icoder/test_app_pilot.py`, `textual_integration`) — cases 8/9 of the previous draft
(the `approval_request` branch and the cancel channel) moved to Step 7:

8. **R9, the real exit path — not a proxy.** Start a turn whose tool is gated, let it reach the
   pending state (bridge reports `pending() > 0`, worker parked in `q.get`), then quit the app
   (`pilot.press("ctrl+q")` / `app.exit()`) **without** answering. Assert, under a hard test
   timeout well below the 300s inactivity value: the engine's futures are cancelled,
   `run_test()` returns (the app actually exits), and the `_stream_llm` worker thread is no longer
   alive afterwards. Asserting only that `on_unmount` called `cancel_pending_approvals()` is a
   proxy for the hook, not for R9's "the process exits without stalling", and would stay green
   while the worker blocked forever in `call_from_thread`.
9. **Closed-app guard, directly:** with `_shutting_down` set, the `_stream_llm` tail issues no
   `call_from_thread` (spy on it) and returns; a `RuntimeError` raised by `call_from_thread` in the
   race window is caught and logged rather than propagated out of the worker.

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
> In `src/mcp_coder/icoder/ui/app.py`: add an `on_unmount` hook calling
> `self._core.cancel_pending_approvals()` so quitting with an approval pending does not stall on
> the 300s inactivity timeout, and add the closed-app guard that makes the hook sufficient — route
> every `call_from_thread` in `_stream_llm` through one helper that no-ops once the app is shutting
> down (an `on_unmount`-set `threading.Event`), catching and logging `RuntimeError` for the race
> window. Without it the unwound worker still reaches
> `self.call_from_thread(self._reset_busy_indicator)` (`ui/app.py:313`) after `App._shutdown()` has
> dispatched `Unmount`, blocks on a stopped loop, and hangs the process at exit (Textual thread
> workers run on non-daemon `ThreadPoolExecutor` threads). The `approval_request` branch and the
> cancel channel are **not** part of this step — they shipped in Step 7. Do not add a modal,
> scopes, or any persist write-back — that is #1046.
>
> Write `tests/llm/providers/langchain/test_approval_integration.py` (cases 1–7 in the step, real
> agent path, reusing the Step 1 harness) and the two UI pilot cases first. Pilot case 8 must
> assert the real exit path (the app quits with an approval pending and the worker thread is gone),
> not merely that `on_unmount` called the delegator.
>
> Then, once you have confirmed that the FINDINGS §2/§3/§4/§5/§10 rationale is present in the
> production docstrings and comments added by Steps 2, 4 and 5, delete `spikes/i3-1-approval/`
> (D9 consume-and-delete handoff) and re-run the full fast suite.
>
> Use MCP tools only (`delete_directory` with `recursive=True` for the spike). Finish with
> `run_pylint_check`, `run_pytest_check` (fast selection **and** the `textual_integration` marker),
> `run_mypy_check` and `run_lint_imports_check` all green, then one commit.
