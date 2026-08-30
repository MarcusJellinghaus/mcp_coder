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
