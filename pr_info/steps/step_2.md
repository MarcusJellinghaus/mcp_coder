# Step 2 — Prep: extract the stream worker and event dispatch out of `ui/app.py`

**Depends on:** nothing. **Behaviour-neutral — pure move, no new feature.**

`src/mcp_coder/icoder/ui/app.py` is **740** lines against the same `--max-lines 750` CI gate, and
Steps 8, 9 and 10 add roughly +50 lines to it. Not allowlisted, and not to be allowlisted (#353).
This step moves the block those steps actually edit, so the headroom lands where the additions do.

---

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/icoder/ui/stream_view.py` | **create** — the moved block |
| `src/mcp_coder/icoder/ui/app.py` | **modify** — delete the block, inherit it |

## WHAT

One contiguous run of `ICoderApp` — everything from `_stream_llm` through `_show_error` — moves
into a base class:

```
_stream_llm              _append_blank_line       _flush_buffer        _new_unit_id
_finalize_turn           _cleanup_orphan_tools    _handle_stream_event
_reset_busy_indicator    _append_cancelled_marker _show_error
```

with the per-turn state they own: `_renderer`, `_text_buffer`, `_current_turn_id`,
`_current_turn_text`, `_open_tool_units`, `_unit_counter`, `_cancel_event`.

```python
# icoder/ui/stream_view.py
class StreamViewApp(App[None]):
    """Stream worker + stream-event rendering half of ``ICoderApp``."""

# icoder/ui/app.py
class ICoderApp(StreamViewApp):
    ...
```

## HOW

* **A base class, not a mixin and not free functions.** Every one of those members is reached
  by name from outside: `ui/replay.py` calls `app._new_unit_id`, `app._handle_stream_event`,
  `app._flush_buffer`, `app._finalize_turn`, `app._cleanup_orphan_tools`,
  `app._append_cancelled_marker`, `app._append_blank_line`, and the pilot tests reach several
  more. A base class keeps all of those call sites **byte-identical** — `replay.py` is not
  touched, no test is touched, and there are no delegator stubs eating the headroom back.
  A bare mixin would have to re-declare the attributes it touches for `mypy --strict`; deriving
  from `App[None]` avoids that, and Textual sees ordinary single inheritance.
* **State moves with the behaviour.** `StreamViewApp.__init__` takes `**kwargs`, calls
  `super().__init__(**kwargs)`, and initialises the seven attributes above (`_renderer` needs
  `format_tools`, so pass it through). `ICoderApp.__init__` keeps `_core` and everything else and
  calls `super().__init__(format_tools=format_tools, **kwargs)`.
* `StreamViewApp` reads `self._core`, which `ICoderApp` sets. Declare it on the base as a bare
  annotation (`_core: AppCore`, no assignment) so `mypy --strict` type-checks the base without a
  runtime effect.
* `CSS` and `BINDINGS` stay on `ICoderApp`.
* Move the imports the block needs (`deque`, `datetime`, the `render_actions` dataclasses,
  `StreamEventRenderer` / `format_tool_start`, `StreamEvent`, `ContentUnit` / `OutputLog`,
  `BusyIndicator`, `Static`, `STYLE_TOOL_OUTPUT` / `STYLE_CANCELLED`) and delete the ones
  `app.py` no longer uses. Keep the two style constants importable from `ui/app.py` if anything
  outside reads them there — check before deleting.
* **Do not** rename anything, change a signature, or reorder methods. A reviewer must be able to
  diff the two halves and see a move.

## DATA

No behaviour, no public API change. `app.py` lands at roughly **510** lines and `stream_view.py`
at roughly **260**, so both stay well under 600 after Steps 8–10.

## TESTS

**None new.** `tests/icoder/test_app_pilot.py`, `tests/icoder/ui/test_app_branch_info.py` and the
replay tests must pass unchanged. If a test needs an edit, the move was not pure — revert and
rethink.

## CHECKS

`run_pylint_check`, `run_mypy_check`, `run_pytest_check` (fast selection) **plus**
`run_pytest_check(markers=["textual_integration"], extra_args=["-n","auto"])`,
`run_lint_imports_check`, **and the file-size gate** (`check_file_size(max_lines=750)` must not
list `icoder/ui/app.py`) — all green.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (§4 and §5) and `pr_info/steps/step_2.md`, then implement Step 2
> only.
>
> Create `src/mcp_coder/icoder/ui/stream_view.py` holding `class StreamViewApp(App[None])`, and
> move `_stream_llm`, `_append_blank_line`, `_flush_buffer`, `_new_unit_id`, `_finalize_turn`,
> `_cleanup_orphan_tools`, `_handle_stream_event`, `_reset_busy_indicator`,
> `_append_cancelled_marker` and `_show_error` into it **verbatim**, together with the per-turn
> state they own (`_renderer`, `_text_buffer`, `_current_turn_id`, `_current_turn_text`,
> `_open_tool_units`, `_unit_counter`, `_cancel_event`). Make `ICoderApp` inherit from it.
>
> Use a base class, not delegating stubs: `ui/replay.py` and the pilot tests reach these members
> by name and must stay byte-identical, and stubs would eat the headroom this step exists to
> create. Declare `_core: AppCore` as a bare annotation on the base for `mypy --strict`.
>
> This is a pure move: no rename, no signature change, no new tests, no behaviour change. The
> point is the CI file-size gate (`--max-lines 750`): the file is at 740 and Steps 8–10 add ~50.
> Do **not** add it to `.large-files-allowlist`.
>
> Use MCP tools only. Run the fast suite **and** the `textual_integration` marker. Finish with
> `run_pylint_check`, `run_pytest_check`, `run_mypy_check`, `run_lint_imports_check` and
> `check_file_size(max_lines=750)` all green, then one commit.
