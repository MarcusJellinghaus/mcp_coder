# Step 4 — iCoder `RealLLMService.stream()` smoke test

## Goal

Add a single real-CLI smoke test that exercises iCoder's
`RealLLMService.stream()` end-to-end against the live Claude CLI. Confirms
events arrive and `session_id` is populated. Session continuity is **not**
re-tested here — already covered in Step 3 at the lowest layer.

## WHERE

- File: `tests/icoder/test_llm_service.py` (existing — append the new test)
- Marker: `@pytest.mark.claude_cli_integration` on the new test only.

## WHAT

One new test function appended to the existing file:

```python
@pytest.mark.claude_cli_integration
def test_real_llm_service_stream_smoke() -> None: ...
```

Existing tests in the file remain unit tests with mocks; the new test
uses no monkeypatching.

## HOW

Add `import pytest` if not already present (it is — file uses `pytest.MonkeyPatch`).
Use existing import of `RealLLMService` from
`mcp_coder.icoder.services.llm_service`.

Place the new test at the end of the file to keep diffs small.

## ALGORITHM

```
service = RealLLMService(provider="claude", timeout=60)
events = list(service.stream("Reply 'ok'."))
assert any(e["type"] == "text_delta" for e in events)
assert any(e["type"] == "done" for e in events)
assert service.session_id  # populated from the done event
```

## DATA

- Input: a short deterministic prompt ("Reply 'ok'.").
- Output: a list of `StreamEvent` dicts; `service.session_id` becomes a
  non-empty string after `.stream()` is consumed.

## Validation

1. Run pylint, pytest (unit-test exclusion markers — the new test is
   skipped, existing unit tests in the file still run and pass), mypy via
   MCP tools.
2. Optionally, run with `markers=["claude_cli_integration"]` locally to
   confirm the new test passes against the live Claude CLI.
3. All three quality checks must pass.

## Commit

One commit titled e.g.:
`Add iCoder RealLLMService.stream() smoke test (#916)`

---

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement
> Step 4 only: append a single `test_real_llm_service_stream_smoke`
> function to `tests/icoder/test_llm_service.py`, marked with
> `@pytest.mark.claude_cli_integration`. The test should construct
> `RealLLMService(provider="claude", timeout=60)`, call `.stream(...)`,
> and assert `text_delta` and `done` events arrived plus
> `service.session_id` is populated. Do not duplicate session-continuity
> logic (covered in Step 3). Run pylint, pytest (unit-test exclusion
> markers), and mypy via MCP tools. All three must pass before producing
> one commit. Do not modify any other file.
