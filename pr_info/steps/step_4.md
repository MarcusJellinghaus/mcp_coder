# Step 4: Update __init__.py exports + final verification

## Context
See `pr_info/steps/summary.md` for full issue context and architecture.

Steps 1-3 completed all functional changes. This step updates the public API exports and runs final verification.

## LLM Prompt
> Implement Step 4 of issue #680. Read `pr_info/steps/summary.md` and this step file fully. Update the `__init__.py` exports, then run all quality checks to verify everything is green.

---

## Part A: Update __init__.py

### WHERE
`src/mcp_coder/llm/formatting/__init__.py`

### WHAT
Add exports for `StreamEventRenderer` and all 5 action types:

```python
from .render_actions import (
    ErrorMessage,
    StreamDone,
    TextChunk,
    ToolResult,
    ToolStart,
)
from .stream_renderer import StreamEventRenderer

__all__ = [
    # Existing exports (keep all)
    "format_text_response",
    "format_verbose_response",
    "format_raw_response",
    "print_stream_event",
    "is_sdk_message",
    "get_message_role",
    "get_message_tool_calls",
    "serialize_message_for_json",
    "extract_tool_interactions",
    # New exports
    "StreamEventRenderer",
    "TextChunk",
    "ToolStart",
    "ToolResult",
    "ErrorMessage",
    "StreamDone",
]
```

### HOW
- Do NOT export private helpers (`_format_tool_name`, etc.)
- Consumers use `StreamEventRenderer.render()` as the only public API
- Action types are exported so consumers can do `isinstance` dispatch

---

## Part B: Final verification

### WHAT
Run all three quality checks:
1. `mcp__tools-py__run_pylint_check` — no new warnings
2. `mcp__tools-py__run_mypy_check` — no type errors
3. `mcp__tools-py__run_pytest_check` with `-n auto -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"` — all tests pass

### ALSO VERIFY
- `grep -r "append_tool_use" src/` returns no results (dead code fully removed)
- `grep -r "_format_tool_name\|_render_tool_output\|_format_tool_args" src/mcp_coder/llm/formatting/formatters.py` returns no results (helpers fully moved)

---

## Commit
One commit: "refactor(formatting): export StreamEventRenderer and render action types"
