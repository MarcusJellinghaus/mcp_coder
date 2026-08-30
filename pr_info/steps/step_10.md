# Step 10 — Shutdown hook + closed-app guard (R9)

**Depends on:** Step 9 (and therefore all earlier steps).

Quitting the app with an approval pending must not stall and must not hang the process. Two halves:
cancel the futures, and stop the unwinding worker from blocking on a dead message pump.

The `approval_request` branch, its interim fail-closed deny and the direct cancel channel shipped
in **Step 9** — they had to land in the same commit as the engine wiring, or that commit would
ship an app whose first `ask`-gated call wedges the turn permanently.

---

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/icoder/ui/stream_view.py` | **modify** — `on_unmount` hook + closed-app guard in `_stream_llm` |
| `tests/icoder/test_app_pilot.py` | **modify** — shutdown cases |

Both members go on `StreamViewApp` (Step 2), which already owns `_stream_llm` and the `_core`
annotation. `ui/app.py` is not touched.

## WHAT

```python
# icoder/ui/stream_view.py
def on_unmount(self) -> None:
    """Cancel pending approvals so quitting never stalls on the 300s inactivity timeout."""

def _call_from_thread_if_running(self, callback, *args) -> None:
    """Run *callback* on the UI thread, or drop it when the app is shutting down."""
```

## HOW

* **Shutdown hook** — add `on_unmount` calling `self._core.cancel_pending_approvals()`.
  `_stream_llm` runs via `run_worker(..., thread=True)` and a thread blocked in `q.get` cannot be
  interrupted; nothing overrides `on_unmount` or `action_quit` today.
* **Closed-app guard — the other half of R9, and the part the hook alone does not give you.**
  Cancelling the futures only *starts* the unwind; the worker thread still has to finish, and its
  tail runs `call_from_thread` against an app that is already shutting down. `App._shutdown()`
  dispatches `Unmount` **after** `_close_all()` / `_close_messages()`, so by the time the unwound
  worker reaches `_stream_llm`'s `finally` — `self.call_from_thread(self._reset_busy_indicator)`
  on the `elif not _error_handled` branch, since `on_unmount` does not set
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

## DATA

* `self._shutting_down: threading.Event`, initialised alongside `_cancel_event` in
  `StreamViewApp.__init__`, set exactly once by `on_unmount`, never cleared.
* No stream-event shape changes.

## TESTS (write first)

UI (`tests/icoder/test_app_pilot.py`, `textual_integration`):

1. **R9, the real exit path — not a proxy.** Start a turn whose tool is gated, let it reach the
   pending state (bridge reports `pending() > 0`, worker parked in `q.get`), then quit the app
   (`pilot.press("ctrl+q")` / `app.exit()`) **without** answering. Assert, under a hard test
   timeout well below the 300s inactivity value: the engine's futures are cancelled,
   `run_test()` returns (the app actually exits), and the `_stream_llm` worker thread is no longer
   alive afterwards. Asserting only that `on_unmount` called `cancel_pending_approvals()` is a
   proxy for the hook, not for R9's "the process exits without stalling", and would stay green
   while the worker blocked forever in `call_from_thread`.

   **Reaching the pending state — required, because Step 9's interim auto-deny would otherwise
   answer instantly.** `_handle_stream_event`'s `approval_request` branch resolves every request
   synchronously via `self._core.resolve_pending(...)` (`step_9.md`, §2.11), so a plain turn
   leaves nothing pending — which is exactly why Step 9 can defer the shutdown hook, and exactly
   why this test needs an explicit way to hold the approval open. Use the delegator as the patch
   point: **monkeypatch `AppCore.resolve_pending` to a no-op for this test only.** The UI branch
   still runs unchanged (event dispatched, `TODO(#1046)` path taken), but nothing answers, so the
   engine keeps the future registered and `pending()` stays `> 0` for the quit. Do **not** patch
   `_handle_stream_event` itself — that would bypass the very branch whose interaction with
   shutdown is under test.

   Build the turn from: a real `ApprovalEngine` injected into the pilot's `AppCore` (Step 9
   wiring) and a fake LLM service whose `stream` runs `request_approval` on a background
   thread + `asyncio.run` loop and yields the emitted `approval_request` — i.e. the Step 3
   harness's consumer shape, without langgraph. That reproduces the two-loop topology R9 is
   about (worker thread parked, future on another loop) without needing a real agent.

   Add a `TODO(#1046)` next to the monkeypatch: once I3.3 replaces the auto-deny with a modal, a
   pending approval is the *natural* state while the modal is open, and the patch point is
   deleted rather than replaced.
2. **Closed-app guard, directly:** with `_shutting_down` set, the `_stream_llm` tail issues no
   `call_from_thread` (spy on it) and returns; a `RuntimeError` raised by `call_from_thread` in the
   race window is caught and logged rather than propagated out of the worker.

## CHECKS

`run_pylint_check`, `run_mypy_check`, `run_pytest_check` (fast selection) **plus**
`run_pytest_check(markers=["textual_integration"], extra_args=["-n","auto"])`, **plus**
`run_lint_imports_check`, **plus the file-size gate** (`check_file_size(max_lines=750)` must not
list `icoder/ui/stream_view.py`) — all green.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (§2.3, §2.11) and `pr_info/steps/step_10.md`, then implement
> Step 10 only.
>
> In `src/mcp_coder/icoder/ui/stream_view.py`: add an `on_unmount` hook calling
> `self._core.cancel_pending_approvals()` so quitting with an approval pending does not stall on
> the 300s inactivity timeout, and add the closed-app guard that makes the hook sufficient — route
> every `call_from_thread` in `_stream_llm` through one helper that no-ops once the app is shutting
> down (an `on_unmount`-set `threading.Event`), catching and logging `RuntimeError` for the race
> window. Without it the unwound worker still reaches
> `self.call_from_thread(self._reset_busy_indicator)` in `_stream_llm`'s `finally` after
> `App._shutdown()` has
> dispatched `Unmount`, blocks on a stopped loop, and hangs the process at exit (Textual thread
> workers run on non-daemon `ThreadPoolExecutor` threads). The `approval_request` branch and the
> cancel channel are **not** part of this step — they shipped in Step 9. Do not add a modal,
> scopes, or any persist write-back — that is #1046.
>
> Write the two pilot cases first. Case 1 must assert the real exit path (the app quits with an
> approval pending and the worker thread is gone), not merely that `on_unmount` called the
> delegator. To reach the pending state, monkeypatch
> `AppCore.resolve_pending` to a no-op for that test — Step 9's interim auto-deny answers every
> `approval_request` synchronously, so without that patch point nothing is ever pending at quit
> time and the test cannot exercise R9 at all. Leave the `_handle_stream_event` branch itself
> unpatched, and mark the patch `TODO(#1046)` (the modal makes the pending state natural).
>
> Use MCP tools only. Finish with `run_pylint_check`, `run_pytest_check` (fast selection **and**
> the `textual_integration` marker), `run_mypy_check`, `run_lint_imports_check` and
> `check_file_size(max_lines=750)` all green, then one commit.
