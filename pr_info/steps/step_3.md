# Step 3 — `format_tool_oneline()` pure function

## Goal

Add a single pure formatter that renders a tool invocation as a tier-1 one-line summary. Reused by `OutputLog._render_unit_atomic` (step 6) and exercised end-to-end via `/display oneline` (step 10).

## WHERE

- `src/mcp_coder/llm/formatting/stream_renderer.py` — add `format_tool_oneline()`
- `tests/llm/formatting/test_stream_renderer.py` — new test class / functions

## WHAT

```python
def format_tool_oneline(
    start: ToolStart,
    result: ToolResult | None,
    duration_ms: int | None,
) -> str:
    """One-line tier-1 summary for a tool invocation.

    Examples:
        ⚙ read_file("src/main.py") → done (12 lines, 120ms)
        ⚙ read_file("src/main.py") → running…
        ⚙ Bash("git status") → error
        ⚙ Bash() → done (3 lines, 50ms)
    """
```

## HOW

- Status (in priority order): `result is None` → `running…`; `result.is_error` → `error`; else `done`.
- Selected key arg = the **first** entry of `start.args` (insertion order). Value rendered via `_render_value_compact()` (existing). Truncate the rendered value to ~40 chars with an `…` suffix if longer.
- When `args` is empty: render as `Bash()` (no inner content).
- Metric suffix only when `result is not None and not is_error`: `(N lines, Dms)` where `N = result.total_lines` and `D = duration_ms`. If `duration_ms is None`, suffix is `(N lines)`.
- Tool name comes from `start.display_name` (already shortened via `_format_tool_name`).

## ALGORITHM

```
status   = "running…" if result is None else ("error" if result.is_error else "done")
arg_part = ""
if args:
    key, value = first(args.items())
    rendered = _render_value_compact(value)
    if len(rendered) > 40: rendered = rendered[:37] + "…"
    arg_part = f"{rendered}"  # value-only inside the parentheses
oneline  = f"⚙ {display_name}({arg_part}) → {status}"
if result and not result.is_error:
    if duration_ms is not None:
        oneline += f" ({result.total_lines} lines, {duration_ms}ms)"
    else:
        oneline += f" ({result.total_lines} lines)"
return oneline
```

## DATA

- Returns `str` (single line, no trailing newline).
- Pure function. No state.

## TDD

Tests in `tests/llm/formatting/test_stream_renderer.py`:

1. `test_oneline_done_with_duration` — `ToolStart`, `ToolResult(is_error=False, total_lines=12)`, `duration_ms=120` → expected string contains `→ done (12 lines, 120ms)`
2. `test_oneline_running` — `result=None` → `→ running…`, no metric suffix
3. `test_oneline_error` — `is_error=True` → `→ error`, no metric suffix
4. `test_oneline_no_args` — `args={}` → `⚙ name() → …`
5. `test_oneline_truncates_long_arg_value` — first arg value is 100 chars → rendered value capped at 40 chars with `…`
6. `test_oneline_uses_first_arg_only` — args has 3 keys → only the first value appears
7. `test_oneline_duration_none_done` — done with `duration_ms=None` → `(N lines)` without ms

Then implement.

## Code quality gates

Pylint, pytest, mypy — all green.

## LLM Prompt

> Implement **Step 3** from `pr_info/steps/step_3.md` (`format_tool_oneline` pure function).
>
> Read `pr_info/steps/summary.md` first for context.
>
> Constraints:
> - One new pure function in `stream_renderer.py`. No state, no renderer changes.
> - Reuse `_render_value_compact()` for arg rendering.
> - First arg by insertion order; value-only (no `key=`) inside `()`.
> - TDD: add the 7 test cases first, then implement.
>
> All three quality gates green after the change.
