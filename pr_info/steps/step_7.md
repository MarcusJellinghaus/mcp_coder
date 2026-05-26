# Step 7 — `DetailModal` widget

## Goal

A `ModalScreen` containing a read-only `TextArea` for tier-3 inspection of any `ContentUnit`. Supports text selection, scrolling, and clipboard copy. Closes on `Escape` / `Enter`. `Ctrl+C` overrides the app-level no-op to copy selection.

Self-contained widget; no click handler / app wiring yet (step 8).

## WHERE

- `src/mcp_coder/icoder/ui/widgets/detail_modal.py` — new file
- `tests/icoder/ui/test_detail_modal.py` — new test file

## WHAT

```python
class DetailModal(ModalScreen[None]):
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("enter",  "dismiss", "Close", priority=True),
        Binding("ctrl+c", "copy_selection", "Copy", priority=True),
    ]

    def __init__(self, unit: ContentUnit) -> None: ...
    def compose(self) -> ComposeResult: ...
    def action_copy_selection(self) -> None: ...

def build_detail_text(unit: ContentUnit) -> str:
    """Plain-text rendering for the modal body. No box characters."""
```

## HOW

- `compose()` yields a single container with a `TextArea(build_detail_text(self._unit), read_only=True, classes="detail-modal-textarea")`. Set a neutral background via CSS (`grey15`) on the container.
- `action_copy_selection()`:
  - Get the focused `TextArea`.
  - Read `text_area.selected_text` (falls back to all text when nothing selected; choose: copy selected if non-empty, else copy all).
  - Push to clipboard via the existing `mcp_coder.utils.clipboard` module.
- `build_detail_text(unit)` switches on `unit.kind`:
  - `tool`:
    ```
    Tool: {tool_name}
    
    Args:
      {key}: {value}     (one per arg; multi-line values indented)
      ...
    
    Output:
    {pretty-printed output via _render_tool_output(output, full=True)}
    
    ─────────────────────────────────────
    Status: {done|error} | Duration: {duration_ms}ms | {N} lines | {timestamp}
    ```
  - `user_input`:
    ```
    User input
    
    {full_text}
    
    ─────────────────────────────────────
    Kind: user_input | {line_count} lines | {timestamp}
    ```
  - `assistant_turn`:
    ```
    Assistant turn
    
    {full_text}
    
    ─────────────────────────────────────
    Kind: assistant_turn | {line_count} lines | {timestamp}
    ```
- No box-drawing characters in body content. The single horizontal divider above the footer is one Unicode `─` line.

## ALGORITHM (build_detail_text for tool)

```
header = f"Tool: {unit.tool_name}"
args_block = "Args:\n" + "\n".join(
    f"  {k}: {_render_value_full(v)[0]}"  # multi-line values: extra indent
    for k, v in (unit.args or {}).items()
) if unit.args else "Args: (none)"
output_lines, total, _truncated = _render_tool_output(unit.output or "", full=True)
output_block = "Output:\n" + "\n".join(output_lines) if output_lines else "Output: (none)"
status = "error" if unit.is_error else "done"
dur = f"{unit.duration_ms}ms" if unit.duration_ms is not None else "—"
footer = f"Status: {status} | Duration: {dur} | {total} lines | {unit.timestamp:%Y-%m-%d %H:%M:%S}"
return "\n\n".join([header, args_block, output_block]) + "\n\n─\n" + footer
```

(Implementer should tighten the algorithm to match the example layout in the issue exactly.)

## DATA

- `DetailModal` is initialized with a snapshot of `ContentUnit` at click-time. Modal text does NOT update if the underlying unit grows (Decision: snapshot, not live).
- `build_detail_text` is a pure function and exported for tests.

## TDD

Tests in `tests/icoder/ui/test_detail_modal.py`:

1. `test_build_detail_text_tool_has_header_args_output_footer` — build text for a tool unit; assert it contains `Tool: ...`, `Args:`, `Output:`, `Status:`, the duration, the timestamp.
2. `test_build_detail_text_tool_no_args` — empty args dict → `Args: (none)`.
3. `test_build_detail_text_tool_error_shows_error_status` — `is_error=True` → footer status `error`.
4. `test_build_detail_text_user_input` — `User input` header; full_text body; footer with `user_input` kind.
5. `test_build_detail_text_assistant_turn` — `Assistant turn` header; full_text body; footer with `assistant_turn` kind.
6. `test_build_detail_text_no_box_chars` — output must NOT contain `│`, `┌`, `└`, `├` characters (the compressed-view's box chars).
7. Pilot test `test_modal_escape_dismisses` — push modal; press Escape; modal removed.
8. Pilot test `test_modal_enter_dismisses` — push modal; press Enter; modal removed.
9. Pilot test `test_modal_ctrl_c_copy_selection_calls_clipboard` — push modal; select text via API; press Ctrl+C; assert clipboard module called with the selected text (mock the clipboard module).
10. Pilot test `test_modal_textarea_is_read_only` — push modal; query the `TextArea`; assert `.read_only is True`.

Then implement.

## Code quality gates

Pylint, pytest, mypy — all green.

## LLM Prompt

> Implement **Step 7** from `pr_info/steps/step_7.md` (DetailModal widget).
>
> Read `pr_info/steps/summary.md` first for context.
>
> Constraints:
> - New file `src/mcp_coder/icoder/ui/widgets/detail_modal.py`.
> - `ModalScreen[None]` with `TextArea(read_only=True)`.
> - `Ctrl+C` binding must have `priority=True` to override the app-level no-op.
> - `build_detail_text(unit)` is pure and exported (used directly by tests).
> - Snapshot at construction — modal does not live-update if the unit changes.
> - Reuse `_render_tool_output(output, full=True)` from `stream_renderer.py` for tool output rendering.
> - No box-drawing characters in modal body (only a single `─` divider above the footer).
> - TDD: 10 test cases first, then implement.
>
> All three quality gates green after the change.
