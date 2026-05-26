# Step 3 — `format_tool_oneline()` pure function

## Goal

Add a single pure formatter that renders a tool invocation as a tier-1 one-line summary. Reused by `OutputLog._render_unit_atomic` (step 6) and exercised end-to-end via `/display oneline` (step 10).

Signature uses **explicit fields** (mirrors R2-03's decision for `format_tool_compressed` and R5-01 for this function) so callers in `_render_unit_atomic` — which only have a `ContentUnit`, no `ToolStart`/`ToolResult` events — can call it without synthesizing throwaway objects.

## WHERE

- `src/mcp_coder/llm/formatting/stream_renderer.py` — add `format_tool_oneline()`
- `tests/llm/formatting/test_stream_renderer.py` — new test class / functions

## WHAT

```python
def format_tool_oneline(
    *,
    name: str,
    args: dict[str, object],
    duration_ms: int | None,
    is_error: bool,
) -> str:
    """One-line tier-1 summary for a tool invocation.

    Status semantics (tri-state — preserves the issue's running/done/error model
    without requiring a ToolResult object):
        - duration_ms is None AND is_error is False → tool still running
        - duration_ms is not None AND is_error is False → done
        - is_error is True → error (duration optional; may be None if cancelled
          before completion)

    Examples:
        ⚙ read_file("src/main.py") → done (120ms)
        ⚙ read_file("src/main.py") → running…
        ⚙ Bash("git status") → error (50ms)
        ⚙ Bash() → done (50ms)
    """
```

## HOW

- Status (in priority order):
  - `is_error is True` → `error`
  - else `duration_ms is None` → `running…`
  - else → `done`
- Selected key arg = the **first** entry of `args` (insertion order). Value rendered via `_render_value_compact()` (existing). Truncate the rendered value to ~40 chars with an `…` suffix if longer.
- When `args` is empty: render as `Bash()` (no inner content).
- Metric suffix `(Dms)` appears whenever `duration_ms is not None`. For the running case (`duration_ms is None, is_error=False`) no suffix is appended.
- For the error case, suffix is `(Dms)` if `duration_ms is not None`, else no suffix (`→ error`).
- Tool name comes from the `name` argument (already shortened by the caller — typically `_format_tool_name(...)` upstream — and stored on `ContentUnit.tool_name`).
- Line counts (`N lines`) live in the compressed/modal tiers, not in oneline; oneline shows status + duration only.

## ALGORITHM

```
if is_error:
    status = "error"
elif duration_ms is None:
    status = "running…"
else:
    status = "done"

arg_part = ""
if args:
    _key, value = next(iter(args.items()))
    rendered = _render_value_compact(value)
    if len(rendered) > 40:
        rendered = rendered[:37] + "…"
    arg_part = f"{rendered}"  # value-only inside the parentheses

oneline = f"⚙ {name}({arg_part}) → {status}"
if duration_ms is not None:
    oneline += f" ({duration_ms}ms)"
return oneline
```

## DATA

- Returns `str` (single line, no trailing newline).
- Pure function. No state. No `ToolStart` / `ToolResult` imports needed.

## TDD

Tests in `tests/llm/formatting/test_stream_renderer.py`. All tests call `format_tool_oneline(name=..., args=..., duration_ms=..., is_error=...)` directly — no `ToolStart` / `ToolResult` construction:

1. `test_format_tool_oneline_done_with_duration` — `name="read_file"`, `args={"path": "src/main.py"}`, `duration_ms=120`, `is_error=False` → expected string contains `→ done` and `(120ms)`
2. `test_format_tool_oneline_running` — `duration_ms=None`, `is_error=False` → contains `running…`, no `ms` suffix
3. `test_format_tool_oneline_error` — `duration_ms=50`, `is_error=True` → contains `→ error` and `(50ms)`
4. `test_format_tool_oneline_error_without_duration` — `duration_ms=None`, `is_error=True` → contains `→ error`, no `ms` suffix (cancelled before completion)
5. `test_format_tool_oneline_no_args` — `args={}` → output matches `⚙ {name}() → …`
6. `test_format_tool_oneline_truncates_long_arg_value` — first arg value is 100 chars → rendered value capped at 40 chars with `…`
7. `test_format_tool_oneline_uses_first_arg_only` — args has 3 keys (dict-insertion order) → only the first value appears in the parentheses

Then implement.

## Code quality gates

Pylint, pytest, mypy — all green.

## LLM Prompt

> Implement **Step 3** from `pr_info/steps/step_3.md` (`format_tool_oneline` pure function).
>
> Read `pr_info/steps/summary.md` first for context, then `pr_info/steps/Decisions.md` entry **R5-01** for the signature rationale.
>
> Constraints:
> - One new pure function in `stream_renderer.py`. No state, no renderer changes.
> - Keyword-only signature: `(*, name, args, duration_ms, is_error)`. No `ToolStart` / `ToolResult` parameters.
> - Status tri-state derived from `(duration_ms, is_error)`: running (None + False), done (set + False), error (any + True).
> - Reuse `_render_value_compact()` for arg rendering.
> - First arg by insertion order; value-only (no `key=`) inside `()`.
> - Duration suffix `({duration_ms}ms)` appended whenever `duration_ms is not None` (covers both done and error-with-duration). No line-count suffix in oneline.
> - TDD: add the 7 test cases first (all calling `format_tool_oneline(name=..., args=..., duration_ms=..., is_error=...)`), then implement.
>
> All three quality gates green after the change.
