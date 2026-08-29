# Step 6 — Tool-unit pairing on `tool_run_id` (R18 / R1)

**Depends on:** nothing (independent; may run in parallel with Steps 1–5).

A human pause makes same-tool mis-pairing near-certain rather than rare: an ungated call finishes
while a gated call of the **same tool name** is still awaiting approval, so the positional FIFO
attaches the result to the wrong row — and the elapsed time to a third row.

---

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/llm/providers/langchain/agent.py` | **modify** — emit `tool_run_id` on both tool events |
| `src/mcp_coder/llm/formatting/render_actions.py` | **modify** — trailing optional field |
| `src/mcp_coder/llm/formatting/stream_renderer.py` | **modify** — `pop_pending_tool`, id-keyed pairing |
| `src/mcp_coder/icoder/ui/app.py` | **modify** — `_open_tool_units` becomes a single deque |
| `tests/llm/formatting/test_stream_renderer_tool_format.py` | **modify** |
| `tests/icoder/test_app_pilot.py` | **modify** — add the same-tool gated/ungated case |

## WHAT

```python
# render_actions.py — declared LAST, with a default, on BOTH dataclasses
tool_run_id: str | None = None

# stream_renderer.py — one module-level helper, shared by both call sites
def pop_pending_tool(
    pending: deque[tuple[str | None, str, Any]],   # (tool_run_id, raw_name, payload)
    run_id: str | None,
    name: str,
) -> tuple[str | None, str, Any] | None:
    """Pop by ``tool_run_id`` when both sides carry one, else the first match by name (FIFO)."""
```

## HOW

* **`agent.py`** — two one-line additions: `"tool_run_id": run_id` on the `on_tool_start` yield and
  on the `on_tool_end` yield. **Do not touch `tool_call_id`** — #1118 depends on `on_tool_end`
  carrying the model's `call_N` id, and two existing assertions
  (`test_langchain_agent_streaming.py` `== "run-1"`, `test_langchain_agent_streaming_tool_output.py`
  `== "tc-123"`) must stay green.
* **`render_actions.py`** — `tool_run_id: str | None = None` **last** on `ToolStart` and
  `ToolResult`. This is what keeps `output_log.py`'s
  `ToolStart(display_name=…, raw_name="", args=…)` call site compiling, so `output_log.py` is
  **not** modified.
* **`stream_renderer.py`** — `_pending` becomes
  `deque[tuple[str | None, str, float]]` (run_id, raw_name, monotonic start). `_pair_pending` is
  replaced by a call to `pop_pending_tool`; `cleanup_pending` carries `tool_run_id` onto each
  synthesized `ToolResult`. Keep the class docstring's "callers MUST invoke `cleanup_pending`"
  contract.
* **`ui/app.py`** — `_open_tool_units: dict[str, deque[str]]` becomes
  `deque[tuple[str | None, str, str]]` (run_id, raw_name, unit_id). Three call sites change:
  the `ToolStart` append, the `ToolResult` lookup, and `_cleanup_orphan_tools`. The FIFO-desync
  WARN log stays (it becomes "N entries left over after cleanup"). `ui/app.py` already imports
  from `llm.formatting`, so importing `pop_pending_tool` adds no new dependency edge.
* **Fallback is required, not optional:** `claude_code_cli_streaming.py` and
  `copilot_cli_streaming.py` emit neither field, and replayed pre-change logs carry neither — so
  `run_id=None` must degrade to name-FIFO exactly as today. Say so in the helper's docstring.
* Blast radius check already done: `cleanup_pending` has **one** production caller
  (`_cleanup_orphan_tools`), which has four callers (`app.py` error / cancel / `StreamDone`, and
  `replay.py`). None of their signatures change.

## ALGORITHM

```python
def pop_pending_tool(pending, run_id, name):
    if run_id:
        for i, entry in enumerate(pending):
            if entry[0] == run_id:
                del pending[i]; return entry
    for i, entry in enumerate(pending):          # fallback: first match by name, FIFO
        if entry[1] == name:
            del pending[i]; return entry
    return None
```

## DATA

* `tool_use_start` / `tool_result` events gain `"tool_run_id": <langgraph run_id>`;
  `tool_call_id` is unchanged on both.
* `ToolStart.tool_run_id` / `ToolResult.tool_run_id`: `str | None`, default `None`.
* `pop_pending_tool` returns the matched tuple or `None` (unpaired → `duration_ms is None`,
  or the existing "no open tool unit" WARN in `ui/app.py`).

## TESTS (write first)

1. **Renderer, id-keyed:** two `tool_use_start` for the **same** name with different
   `tool_run_id`s; results arrive **out of order** → each `duration_ms` is attributed to the
   correct start (assert with monkeypatched `time.monotonic` or ordering, not wall-clock values).
2. **Renderer, fallback:** events with no `tool_run_id` (the Claude/Copilot shape) pair by
   name-FIFO exactly as today — existing tests in the file stay green unchanged.
3. **Renderer, cleanup:** `cleanup_pending` returns `ToolResult`s carrying their `tool_run_id`.
4. **`agent.py`:** both tool events carry `tool_run_id == run_id`; the two existing `tool_call_id`
   assertions still pass.
5. **UI (`test_app_pilot.py`, `textual_integration`):** one turn with two calls to the **same**
   tool, results out of order → each `tool_result` updates the correct unit; the desync WARN is
   not emitted.
6. **UI orphan cleanup:** a cancelled turn with one open same-name unit still resolves the right row.

## CHECKS

`run_pylint_check`, `run_mypy_check`, `run_pytest_check` (fast selection) **plus**
`run_pytest_check(markers=["textual_integration"], extra_args=["-n","auto"])` for the pilot tests.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (§2.9) and `pr_info/steps/step_6.md`, then implement Step 6 only.
>
> Add a new `tool_run_id` field carrying the langgraph `run_id` to both the `tool_use_start` and
> `tool_result` events in `llm/providers/langchain/agent.py`, **leaving `tool_call_id` untouched**
> (#1118 depends on it and two existing assertions must stay green). Add
> `tool_run_id: str | None = None` as the **last** field of `ToolStart` and `ToolResult` in
> `render_actions.py` — with the default, `icoder/ui/widgets/output_log.py` needs no change, so do
> not modify it.
>
> Add one module-level helper `pop_pending_tool(pending, run_id, name)` in `stream_renderer.py`
> (id-keyed with a name-FIFO fallback — the fallback is required because the Claude and Copilot
> streaming paths and replayed pre-change logs carry neither field). Use it from
> `StreamEventRenderer` (whose `_pending` becomes a deque of `(run_id, raw_name, start)`) and from
> `icoder/ui/app.py`, whose `_open_tool_units` collapses from `dict[str, deque[str]]` to a single
> deque of `(run_id, raw_name, unit_id)`. Do not build a generic container class. Thread
> `tool_run_id` through `cleanup_pending`; no caller signature changes.
>
> Write the six test cases listed in the step first, including the same-tool gated/ungated
> out-of-order case at both sites.
>
> Use MCP tools only. Run the fast suite **and** the `textual_integration` marker. Finish with
> `run_pylint_check`, `run_pytest_check`, `run_mypy_check` all green, then one commit.
