# Step 11 — End-to-end integration test + spike deletion

**Depends on:** Step 10 (and therefore all earlier steps). **Last step.**

Proves the whole path through the real agent, then consumes and deletes the I3.1 spike (D9).
The deletion rides here because it is only safe once every step that was supposed to carry the
`FINDINGS.md` rationale into production code has landed, and the end-to-end test is what shows
the rationale was carried correctly rather than merely quoted.

---

## WHERE

| Path | Action |
|---|---|
| `tests/llm/providers/langchain/test_approval_integration.py` | **create** |
| `spikes/i3-1-approval/` | **delete** (8 files) |

No production file is touched.

## HOW

* Reuse the Step 3 harness (`approval_harness.py`), including its rule that every
  `pytest.importorskip` and every langchain import lives **inside a function**.
* Session storage is already isolated by the directory's autouse `_tmp_home` fixture (R12) — no
  extra isolation code.
* **Spike deletion** — before deleting, confirm the load-bearing rationale from
  `FINDINGS.md` §2 (loop handle), §3 (pause over keepalives), §4 (direct cancel channel), §5
  (stale-`q`) and §10 (deny `tool_call_id`) is present in production docstrings/comments from
  Steps 4, 6 and 7. Then delete the directory with `delete_directory(recursive=True)` and re-run
  the full fast suite to confirm nothing imported it.

## ALGORITHM

```
# integration test, real agent path
build fake chat model + gated MCP-shaped tool + gateway(config with an `ask` rule) + ApprovalEngine
run _ask_agent_stream(..., approval_bridge=engine) on the consumer thread
read events until type == "approval_request"; capture approval_id
engine.resolve_pending(approval_id, ApprovalDecision("allow", "once"))   # from the test thread
assert the tool ran, the turn completed, and the model was invoked twice
```

## DATA

* The `approval_request` event reaching `_handle_stream_event` is
  `{"type","approval_id","tool_name","args","source"}` with `source` a plain string.
* It **necessarily arrives after** `tool_use_start` (the interceptor runs inside the tool coroutine
  and `on_tool_start` fires first) — assert this ordering; #1045 flags it
  as a scheduling claim that was never verified at HEAD, so verify it here. A wrong result is
  cosmetic only (a modal for a row not yet drawn) — report it, do not block on it.
* R17 stands: there is **no** correlation key between `approval_request` and the on-screen tool
  unit. Do not invent one.

## TESTS (write first)

1. **Allow:** gated call blocks, is approved, then runs; the agent continues; nothing raises.
2. **Deny:** returns a clean `ToolMessage(status="error")` carrying the real `tool_call_id`; the
   agent continues.
3. **Ungated calls are not blocked** behind a pending approval.
4. **Cancel-while-pending:** `cancel_all()` → the turn unwinds without re-planning
   (`invoke_count == 1`), `thread.is_alive() is False` after the 5s join, nothing on stderr,
   `error_holder` empty.
5. **Backstop still works:** with no approval pending, `cancel_event` / generator close still stop
   the turn.
6. **Ordering:** `approval_request` arrives after that tool's `tool_use_start`.

## CHECKS

`run_pylint_check`, `run_mypy_check`, `run_pytest_check` (fast selection) **plus**
`run_lint_imports_check`. After deleting the spike, re-run the full fast suite to confirm nothing
imported it.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (§2.3, §2.9) and `pr_info/steps/step_11.md`, then implement
> Step 11 only.
>
> Write `tests/llm/providers/langchain/test_approval_integration.py` (cases 1–6 in the step, real
> agent path, reusing the Step 3 harness — including its rule that every `pytest.importorskip` and
> every langchain import goes inside a function).
>
> Then, once you have confirmed that the FINDINGS §2/§3/§4/§5/§10 rationale is present in the
> production docstrings and comments added by Steps 4, 6 and 7, delete `spikes/i3-1-approval/`
> (D9 consume-and-delete handoff) and re-run the full fast suite.
>
> Touch no production file. Use MCP tools only (`delete_directory` with `recursive=True` for the
> spike). Finish with `run_pylint_check`, `run_pytest_check`, `run_mypy_check` and
> `run_lint_imports_check` all green, then one commit.

---

## Implementation note (written after the step landed)

### 1. Shape deviations

Two, both forced by the fixtures the step reuses:

* **Two extra fake chat models, local to the new module.** The Step 3 harness model asks for exactly
  one tool call, which cannot express test 3 (`ToolNode` only runs calls concurrently when they
  arrive in the *same* `AIMessage`) or test 5 (the backstop is only readable between
  `astream_events` iterations, so the turn must keep producing events). `_make_two_call_model()` and
  `_make_looping_model()` therefore live in the test module; `approval_harness.py` is untouched, and
  the other four cases use `make_fake_chat_model()` as specified.
* **`tool_call_id` is injected, not hard-coded.** The MCP-shaped tool takes
  `Annotated[str, InjectedToolCallId]` so the id the gateway stamps onto the deny `ToolMessage` is
  genuinely the model's `call_1`. Hard-coding it would have made test 2 — the FINDINGS §10
  regression — assert nothing: the whole point is that an *unpaired* deny wedges
  `create_react_agent` with `INVALID_CHAT_HISTORY`, which only `invoke_count == 2` can detect.

The "MCP-shaped tool" is the step's own word for the seam: `convert_mcp_tool_to_langchain_tool`
needs a live MCP server, so the tools call `gateway.interceptor` from their own coroutine with the
four attributes it reads (`server_name`, `name`, `args`, `runtime.tool_call_id`). Everything
downstream of that call is production code.

### 2. Test-case mapping

| Step case | Test |
|---|---|
| 1 allow | `test_allow_runs_the_gated_call_and_the_turn_completes` |
| 2 deny | `test_deny_returns_a_paired_error_tool_message_and_the_agent_continues` |
| 3 ungated not blocked | `test_ungated_call_runs_while_a_gated_one_is_pending` |
| 4 cancel-while-pending | `test_cancel_while_pending_unwinds_the_turn_without_replanning` |
| 5 backstop | `test_generator_close_still_stops_a_turn_with_no_approval_pending` |
| 6 ordering | `test_approval_request_arrives_after_that_tools_tool_use_start` |

Case 4's "`thread.is_alive() is False`" is asserted on the **agent** thread, captured by the tool
coroutine itself (`_ToolLog.agent_thread`) — `_ask_agent_stream` never exposes the thread it joins,
and the consumer thread is the test's own. Same technique as Step 10's note.

Case 5 also asserts `gen.close()` returned in under 5s: without the backstop the close would burn
the provider's whole `join(timeout=5)` budget and still return, so the elapsed time is what
discriminates.

### 3. Spike deletion (D9)

`spikes/i3-1-approval/` (8 files) deleted with `delete_directory(recursive=True)` after confirming
the load-bearing FINDINGS rationale is in production code:

| FINDINGS | Carried into |
|---|---|
| §2 loop handle inside the coroutine | `ApprovalEngine` docstring, "Why the loop handle is taken inside the coroutine" |
| §3 pause, not keepalives | `_ask_agent_stream`'s timestamped-window comment ("keepalives would arm it rather than reset it … and would also reach the session .jsonl and the replay path") |
| §4 direct cancel channel | `ApprovalEngine` docstring "Why the direct UI cancel channel exists"; `action_cancel_stream`; `gateway.interceptor`'s "`CancelledError` must PROPAGATE" comment |
| §5 stale-`q` / attach-detach in `try`/`finally` | `_ask_agent_stream` ("the engine must never stay attached to a dead turn"); `detach()`'s "Why detach() clears the registry"; `ask_langchain_stream`'s no-op-on-the-text-branch docstring |
| §10 deny `tool_call_id` | `gateway.interceptor` reads `request.runtime.tool_call_id`; `build_deny_tool_message`'s docstring no longer repeats the false "ToolNode overwrites it" claim |

A repo-wide search for `i3-1-approval` / `spikes/` afterwards returns hits only in this plan's own
files, so nothing imported it (it was never on `testpaths` either).

### 4. The one claim this step could not verify locally

Case 6's ordering assertion is exactly the scheduling claim #1045 flagged as never verified, and
**it is still unverified**: no langchain distribution is installed in this venv (this directory's
conftest injects a `MagicMock` for `langchain_core`), so all six tests skip here — the same gap
Step 3's probe hit and never closed. Reading `langchain_core.tracers.memory_stream._SendStream`
shows the tracer's `on_tool_start` is delivered with `call_soon_threadsafe`, i.e. the consumer only
sees it once the loop runs that callback, so the outcome depends on how many loop turns
`AsyncCallbackManager.on_tool_start` costs before the tool coroutine reaches the interceptor. The
assertion is written as the step specifies, with a failure message that names the exact cause. Per
the step's own instruction, a wrong result there is **cosmetic** (a modal for a row not yet drawn,
and R17 already says the two events share no correlation key) — report it, do not block on it.

### 5. Local environment caveats (all pre-existing, none caused by this step)

1. The stale installed `mcp_workspace` still breaks pytest collection repo-wide; every run below
   used `PYTHONPATH=C:\Users\Marcus\Documents\GitHub\mcp-workspace\src`.
2. No langchain/langgraph in this venv — see §4; the six new tests skip locally.
3. `tests/llm` has four pre-existing failures unrelated to this step: three
   `tests/llm/providers/copilot/test_copilot_integration.py` cases (the external `copilot` CLI exits
   non-zero on this box) and `test_langchain_exceptions.py::test_connection_errors_contains_httpx_connect_error`
   (`httpx` absent, so conftest's `MagicMock` stands in) — the last one is the failure Step 9
   already recorded.
4. `pytest-textual-snapshot` is still not installed, and whole-suite runs still exceed the 300s tool
   timeout, so verification used per-directory runs.

### 6. Checks

* `run_pylint_check(["tests/llm/providers/langchain/test_approval_integration.py"])` — clean. (The
  whole-directory run reports only pre-existing `E0401 Unable to import 'langchain_core.messages'`
  in other files, i.e. caveat 2.)
* `run_mypy_check(["tests/llm/providers/langchain"])` — clean.
* `run_ruff_check` on the new file — clean.
* `run_format_code` — isort clean, black reformatted the new file (applied).
* `run_pytest_check` fast selection, `tests/llm` — the four pre-existing failures of caveat 3, the
  six new tests skipped (caveat 2), nothing else.
* `run_pytest_check` fast selection, `tests/icoder` minus `textual_integration` — **673 passed**.
* `run_lint_imports_check` — **21 kept, 0 broken**.
