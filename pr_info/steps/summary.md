# Summary: fix(icoder): tool result output invisible due to Markdown rendering

**Issue:** #778

## Problem

In iCoder, tool result output (e.g. from `list_directory`) is invisible. The `ToolStart` header (`┌ workspace > list_directory()`) appears, but actual tool output lines are not displayed. Only the LLM's text summary is visible.

**Root cause:** `app.py:237-238` wraps tool output in `Markdown()`. The body contains box-drawing characters (`│`, `└`) which Rich's Markdown parser interprets as table syntax, mangling or hiding the content entirely.

## Architectural / Design Changes

- **Rendering path simplified**: The `ToolResult` branch in `_handle_stream_event` previously had two rendering paths — `Markdown()` (default) and `append_text()` (`format_tools=False`). After this fix, both paths use `append_text()` with `STYLE_TOOL_OUTPUT` styling. This eliminates the only usage of `rich.markdown.Markdown` in `app.py`.
- **`format_tools` flag scope narrowed (UI only)**: The flag no longer switches the UI rendering method. It continues to control JSON field filtering and truncation in `StreamEventRenderer._render_tool_output()` — that logic is untouched.
- **No new abstractions or modules**: This is a targeted bug fix, not a refactor.

## Files Modified

| File | Action | Description |
|------|--------|-------------|
| `src/mcp_coder/icoder/ui/app.py` | **Modify** | Remove `Markdown()` rendering for tool results; remove unused import |
| `tests/icoder/test_app_pilot.py` | **Modify** | Update `test_tool_result_renders_markdown_by_default` — rename and fix assertions for plain text rendering |
| `tests/icoder/ui/test_app.py` | **Create** | End-to-end pipeline tests for tool output visibility |

## Files NOT Modified (unchanged)

- `src/mcp_coder/llm/formatting/stream_renderer.py` — truncation/filtering logic untouched
- `src/mcp_coder/llm/formatting/render_actions.py` — data structures unchanged
- `src/mcp_coder/icoder/ui/widgets/output_log.py` — `append_text` / `_recorded` unchanged
- `tests/icoder/ui/__init__.py` — already exists, empty

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Write pipeline tests in `tests/icoder/ui/test_app.py` (will fail due to Markdown bug) + fix `app.py` + update existing test | Single commit: tests + fix |

## Decisions

| # | Topic | Decision | Rationale |
|---|-------|----------|-----------|
| 1 | Markdown rendering | Remove entirely for tool results | Box-drawing chars mangled by Rich's Markdown parser |
| 2 | Truncation limits | Keep as-is (head 10 / tail 5) | Bug is invisible output, not amount shown |
| 3 | `format_tools` flag | Keep on both `ICoderApp` and `StreamEventRenderer` | Still controls JSON filtering/truncation in renderer |
| 4 | `--no-format-tools` CLI flag | Keep | Useful for debugging raw tool output |
| 5 | Test approach | Direct `_handle_stream_event` calls in mounted app | Deterministic, no worker thread timing; same pattern as existing `test_app_pilot.py` |
| 6 | Test file location | `tests/icoder/ui/test_app.py` | Match src structure per issue requirement |
| 7 | Single step | Tests + fix in one step | Change is small and tightly coupled — splitting would be artificial |
