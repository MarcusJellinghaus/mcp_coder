# Design Decisions (Round 1 Plan Review)

Decisions made during the Round 1 plan review for issue #820. Each item records what was asked and what the user decided.

## 1. CLI rendered format aligns with iCoder

**Question:** How should `formatters.py` `print_stream_event()` render `ToolStart` once the old `inline_args` / `block_args` fields are removed?

**Decision:** Align CLI with iCoder. The rendered branch calls `format_tool_start(action, full=False)` and emits the same output, including the `├──` separator. Single unified rendering path across CLI and iCoder.

## 2. CLI text format uses `_render_value_compact` inline

**Question:** What replaces `_format_tool_args` in the `formatters.py` text branch?

**Decision:** Delete `_format_tool_args`. Inline compact rendering directly in `formatters.py` text format:
```python
args_str = ", ".join(f"{k}={_render_value_compact(v)}" for k, v in (args or {}).items())
```
`_render_value_compact` becomes a module-private helper that `formatters.py` imports from `stream_renderer`.

## 3. Step 3 scope expanded to include `formatters.py` + `test_formatters.py`

**Question:** Can Step 3 land without touching `formatters.py`?

**Decision:** No. `formatters.py` is a second consumer of the renamed `ToolStart` fields and of `_format_tool_args`. Step 3 must update it together with the dataclass change, otherwise CI fails (mypy, pylint, and existing test_formatters tests). Step 3's file list and WHAT section now include `formatters.py` and `test_formatters.py`.

## 4. Step 4 (delete `testdata/`) stays as its own commit

**Question:** Should Step 4 (delete `testdata/`) be merged into Step 3?

**Decision:** No. Clean separation; cleanup gets its own commit. Step 4 unchanged.

## 5. Dict rendering preserves insertion order

**Question:** Should `_render_output_value` for dicts sort keys?

**Decision:** No. Dict keys are rendered in Python insertion order (Python 3.7+ guarantee). `test_json_dict_multiline_string` depends on this. Step 1 now states this explicitly.

## 6. Scalar dict values are emitted via `json.dumps`

**Question:** When a dict value is a scalar in `_render_output_value`, are strings quoted?

**Decision:** Yes. Emit `{key}: {json.dumps(value)}` — so strings become `key: "quoted"`, numbers `key: 42`, booleans `key: true`. Matches the reference `render_nice.py._render_dict`.

## 7. `_render_tool_output` default `full=False` flows through `render()`

**Question:** Does `render()` in `stream_renderer.py` need to pass `full` explicitly?

**Decision:** No. `_render_tool_output()` is called from `render()` with `full=False` implicit (default from Step 2). Step 3 notes this so implementers don't add an explicit parameter.

## 8. Additional block-order test in Step 3

**Question:** Do we need explicit coverage that block-mode args preserve insertion order?

**Decision:** Yes. Added `test_block_preserves_arg_order` to `TestFormatToolStart`: 3 long args with distinct keys (e.g., `zebra`, `apple`, `middle`, each forced long enough to trigger block format); assert block lines appear in input insertion order, not alphabetical.

## 9. ToolResult footer subsection removed from Step 3

**Question:** The "app.py — ToolResult footer update" subsection had identical Before/After blocks — keep it?

**Decision:** Remove. The step_3 tasklist already says "ToolResult rendering stays the same". Replaced the subsection with a single sentence: "No changes to ToolResult rendering or footer format."
