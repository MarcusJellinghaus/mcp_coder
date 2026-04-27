# Step 3 — Real-CLI streaming integration tests

## Goal

Add three integration tests against the real Claude CLI to cover the
streaming pipeline that was previously untested end-to-end:

1. `ask_claude_code_cli_stream()` — basic question, verify `text_delta` +
   `done` events.
2. `ask_claude_code_cli_stream()` — session continuity (resume via
   `session_id`).
3. `prompt_llm_stream(provider="claude")` — events flow through the
   high-level interface.

## WHERE

- New file: `tests/llm/providers/claude/test_claude_code_cli_streaming_integration.py`
- Marker: `@pytest.mark.claude_cli_integration` (class- or module-level)

## WHAT

Three test functions / methods. Suggested signatures (sync, no fixtures):

```python
@pytest.mark.claude_cli_integration
class TestClaudeCodeCliStreamingIntegration:
    def test_basic_question_yields_text_delta_and_done(self) -> None: ...
    def test_session_continuity_via_session_id(self) -> None: ...
    def test_prompt_llm_stream_claude_provider_yields_events(self) -> None: ...
```

## HOW

Imports at module top:

```python
import pytest

from mcp_coder.llm.interface import prompt_llm_stream
from mcp_coder.llm.providers.claude.claude_code_cli_streaming import (
    ask_claude_code_cli_stream,
)
```

No fixtures from `conftest.py` are used — the existing
`make_stream_json_output` fixture is for mocked unit tests.

Use the same prompt style as the existing `_logging_integration.py` tests:
short, deterministic ("What is 2+2? Reply with just the number.",
"Reply 'ok'.").

Use `timeout=60` to align with the existing integration tests' tolerances.

## ALGORITHM

### Test 1 — basic question

```
events = list(ask_claude_code_cli_stream(
    question="What is 2+2? Reply with just the number.",
    timeout=60,
))
assert any(e["type"] == "text_delta" for e in events)
done = next(e for e in events if e["type"] == "done")
assert done.get("session_id")
```

### Test 2 — session continuity

```
events1 = list(ask_claude_code_cli_stream(
    question="Remember: my favorite color is blue. Reply 'noted'.",
    timeout=60,
))
session_id = next(e for e in events1 if e["type"] == "done")["session_id"]
assert session_id

events2 = list(ask_claude_code_cli_stream(
    question="What is my favorite color? Reply with just the color.",
    session_id=session_id,
    timeout=60,
))
text = "".join(e["text"] for e in events2 if e["type"] == "text_delta")
assert "blue" in text.lower()
done2 = next(e for e in events2 if e["type"] == "done")
assert done2["session_id"]  # may differ from session_id; just ensure populated
```

### Test 3 — prompt_llm_stream high-level

```
events = list(prompt_llm_stream(
    "Reply 'ok'.",
    provider="claude",
    timeout=60,
))
assert any(e["type"] == "done" for e in events)
```

## DATA

Each test consumes the iterator into a list and asserts against
`StreamEvent` dicts:

- `{"type": "text_delta", "text": str}`
- `{"type": "done", "session_id": str | None, "usage": dict, "cost_usd": float | None}`

No new fixtures, no new helpers, no new conftest entries.

## Validation

1. Run pylint, pytest (unit-test exclusion markers), mypy via MCP tools.
   The new tests will be skipped under the unit pattern but mypy must
   still type-check the file successfully.
2. Optionally, run with `markers=["claude_cli_integration"]` locally to
   confirm the new tests pass against a live Claude CLI before committing.
3. All three quality checks must pass.

## Commit

One commit titled e.g.:
`Add real-CLI streaming integration tests for Claude provider (#916)`

---

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement
> Step 3 only: create
> `tests/llm/providers/claude/test_claude_code_cli_streaming_integration.py`
> with the three test methods described, using the
> `@pytest.mark.claude_cli_integration` marker. Keep tests minimal — no
> fixtures, no helpers, ~10–20 lines each. Run pylint, pytest (unit-test
> exclusion markers — the new tests will be skipped, that is expected),
> and mypy via MCP tools. All three must pass before producing one commit.
> Do not modify any other file.
