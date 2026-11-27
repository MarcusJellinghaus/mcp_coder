# Step 1 — The review uses the reviewer's final message (`report_text`)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **this step only** (`pr_info/steps/step_1.md`).
> TDD: write the tests first, then the code. Run pylint, the fast pytest set and mypy; all
> must pass. Run the formatter before committing. One commit.

## WHERE

- `src/mcp_coder/workflows/review/reviewer.py` — new `report_text`
- `src/mcp_coder/workflows/review/core.py` — one call site
- `tests/workflows/review/test_reviewer.py` — unit tests
- `tests/workflows/review/test_core_round_outcomes.py` — **new** file, loop tests

## WHAT

```python
def report_text(response: LLMResponseDict) -> str:
    """Return the final assistant message of a reviewer turn.

    The last ``done`` event's ``result`` in ``raw_response["events"]`` when it
    is a non-empty string, else ``response["text"]`` (the joined text blocks).
    Providers without a ``result`` on ``done`` (copilot) always fall back.
    """
```

## HOW

- `core.py`, inside the empty-report retry loop:
  `report = report_response["text"]` → `report = reviewer.report_text(report_response)`.
  Nothing else in `core.py` changes; `report` is already the single value used for the
  round log, the supervisor input and `_apply_severity_floor`.
- Read defensively with `.get` (`response.get("raw_response") or {}`, then
  `.get("events")`), skipping non-dict events; never assume Claude.
- Do not touch `ResponseAssembler` or any other `prompt_llm` caller.

## ALGORITHM

```
raw = response.get("raw_response") or {}
events = raw.get("events") if isinstance(raw, dict) else None
for event in reversed(events if isinstance(events, list) else []):
    if isinstance(event, dict) and event.get("type") == "done":
        result = event.get("result")
        if isinstance(result, str) and result.strip(): return result.strip()
        break
return response["text"]
```

## DATA

- Returns `str` (stripped final result, or the unchanged joined text).

## Tests (write first)

`test_reviewer.py`:
- events `[text_delta "Still reviewing.", tool_use_start, text_delta "a.py:1 — high — x", done result "a.py:1 — high — x"]`,
  `text="Still reviewing.a.py:1 — high — x"` → `"a.py:1 — high — x"`.
- `done` with `result=""` → joined text.
- `raw_response={}` (no `events`) → joined text.
- copilot-style `done` without `result` → joined text.

`test_core_round_outcomes.py` (new; reuse `env`, `_run`, `_resp`, `_DISMISS`,
`_label_transition` from `conftest.py`; local helper building a response whose
`raw_response["events"]` ends in a `done` event with a given `result`):
- Reviewer response text `"Still reviewing.a.py:1 — high — x"`, done result
  `"a.py:1 — high — x"`; supervisor dismisses. The round log under
  `tmp_path/pr_info/` contains `a.py:1 — high — x` and not `Still reviewing`, and the
  supervisor prompt (`env.prompt_llm.call_args_list[1].args[0]`) does not contain
  `Still reviewing`.
- Done result `""` with non-empty joined text: the run proceeds (reviewer called once,
  no empty-report retry, i.e. `prompt_llm` call count is 2 for a dismiss run).
