# Step 1: Add `reset_session` field to `Response` dataclass

> **Context:** See `pr_info/steps/summary.md` for full issue context and architecture.

## Goal

Add `reset_session: bool = False` to the `Response` frozen dataclass, following the existing pattern of `clear_output`, `quit`, `send_to_llm`.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/icoder/core/types.py` | Modify — add field |
| `tests/icoder/test_types.py` | Modify — add tests |

## WHAT

### `Response` dataclass (`types.py`)

Add one field after `send_to_llm`:

```python
reset_session: bool = False  # True = reset LLM session (new conversation)
```

## HOW

- Field added to existing frozen dataclass — no imports, no integration points.
- Follows exact same pattern as `clear_output: bool = False`.

## DATA

`Response` fields after change:
- `text: str = ""`
- `clear_output: bool = False`
- `quit: bool = False`
- `send_to_llm: bool = False`
- `llm_text: str | None = None`
- `reset_session: bool = False`

## Tests (TDD — write first)

### `test_types.py` — add two tests:

1. **`test_response_reset_session_default`** — `Response()` has `reset_session=False`
2. **`test_response_reset_session_explicit`** — `Response(reset_session=True)` has `reset_session=True`

Also update `test_response_defaults` to assert `reset_session is False`.

## Commit

```
feat(icoder): add reset_session flag to Response dataclass
```

## LLM Prompt

```
Implement Step 1 from pr_info/steps/step_1.md (see pr_info/steps/summary.md for context).

Add `reset_session: bool = False` to the Response dataclass in types.py.
Add tests in test_types.py. Update test_response_defaults to also assert reset_session.
Run all code quality checks. Commit when green.
```
