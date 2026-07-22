# Step 1 — A-B-A session-interleave prototype (mandatory first commit)

> References `pr_info/steps/summary.md` §7. This is an **integration-marked** regression test
> that proves the persistent-supervisor / fresh-reviewer interleave and **decides the
> session-id chaining discipline** the engine (Step 7) will implement. It also validates
> `create_plan`'s reuse-original-id assumption.

## WHERE
- `tests/workflows/review/__init__.py` (new, empty package marker)
- `tests/workflows/review/test_prototype_session_interleave.py` (new)

## WHAT
```python
import pytest

@pytest.mark.claude_cli_integration
def test_supervisor_recalls_across_interleaved_reviewer_sessions() -> None: ...

@pytest.mark.claude_cli_integration
def test_reuse_original_id_vs_recapture_returned_id() -> None: ...
```

## HOW
- Uses `mcp_coder.llm.interface.prompt_llm` directly — no new production code.
- Mark with the existing `claude_cli_integration` marker (see `pyproject.toml`); excluded
  from the fast unit run, executed in CI.
- No MCP tools needed; a plain `provider="claude"` round-trip with `session_id` chaining is
  enough to observe context retention.

## ALGORITHM (test 1)
```
sup1 = prompt_llm("Remember token ALPHA. Reply OK.", session_id=None)      # A (turn 1)
_    = prompt_llm("Fresh reviewer, share nothing.", session_id=None)        # B (fresh)
sup2 = prompt_llm("Remember token BETA too.", session_id=sup1.session_id)   # A (turn 2)
_    = prompt_llm("Another fresh reviewer.", session_id=None)               # B (fresh)
sup3 = prompt_llm("Name BOTH tokens you were told.", session_id=<see below>)# A (turn 3)
assert "ALPHA" in sup3.text and "BETA" in sup3.text     # turn 3 recalls turn 1 AND turn 2
```

## ALGORITHM (test 2 — decides discipline, records create_plan finding)
```
run test-1 flow twice: once resuming with the ORIGINAL id every turn (create_plan style),
once RE-CAPTURING each returned session_id and resuming with the latest.
record which discipline preserves BETA at turn 3.
if reuse-original drops BETA: assert recapture works, and add a NOTE in the test docstring +
  pr_info log that create_plan/core.py (reuse-original resume sites) silently loses prompt-2
  context in production (fix out of scope for #1072).
```

## DATA
- `prompt_llm` returns `LLMResponseDict` — read `["text"]`, `["session_id"]`.
- Test asserts substring recall (`ALPHA`, `BETA`) and pins the winning discipline as a module
  constant/comment consumed by Step 7 (`_next_supervisor_session_id`).

## TDD / checks
- The test *is* the deliverable; it must pass under `claude_cli_integration`.
- Run: `run_pytest_check(markers=["claude_cli_integration"], extra_args=["-n","auto","-k","interleave"])`
  then pylint + mypy on the test module.

## LLM prompt for this step
> Implement Step 1 of `pr_info/steps/summary.md`. Create
> `tests/workflows/review/__init__.py` and
> `tests/workflows/review/test_prototype_session_interleave.py` containing two
> `@pytest.mark.claude_cli_integration` tests that drive `mcp_coder.llm.interface.prompt_llm`
> in an A-B-A interleave (persistent "supervisor" id + fresh "reviewer" `session_id=None`),
> resuming the supervisor at least twice (≥3 supervisor turns) and asserting turn 3 recalls
> both earlier turns. The second test compares reuse-original-id vs re-capture-returned-id and
> records which discipline preserves context; if reuse-original fails, document the
> `create_plan` context-loss finding in the docstring. No production code. Follow the exact
> pseudocode in Step 1. Then run pylint + mypy and the `claude_cli_integration` test.
