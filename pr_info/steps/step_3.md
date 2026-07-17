# Step 3 — Behavioural dispatch boundary: human in, model out

**Reference:** `pr_info/steps/summary.md`
**Acceptance criteria:** AC1, AC2, AC3 (supporting check)
**Commit:** one — two complementary tests + checks passing.

## Goal

Prove the two sides of the boundary behaviourally:

- **Positive (AC2):** a user-typed `/skill_name` routed through
  `AppCore.handle_input` **does** dispatch and invoke the skill.
- **Negative (AC1 + AC3 supporting):** model-shaped `/skill_name` text driven
  through the render path (`ICoderApp._handle_stream_event`, also the entry
  used by `ui/replay.py`) renders as **plain text** and **never** calls
  `registry.dispatch`.

These are complementary halves of one invariant (not independent features), so
they share one commit.

## TDD order

1. Add the positive unit test to `test_app_core.py`.
2. Add the negative pilot test to `test_app_pilot.py`.
3. Run all three quality gates.

## WHERE

- **Modify:** `tests/icoder/test_app_core.py` (positive unit test)
- **Modify:** `tests/icoder/test_app_pilot.py` (negative pilot test —
  file already carries `pytestmark = pytest.mark.textual_integration` and the
  `icoder_app` / `make_icoder_app` fixtures)

No production code changes in this step.

## WHAT

### Positive unit test (`test_app_core.py`)

```python
def test_user_typed_skill_dispatches_and_invokes(app_core: AppCore) -> None:
    """A user-typed /skill routed via handle_input dispatches and invokes it."""
    from mcp_coder.icoder.skills import ClaudeSkill, register_skill_commands

    skill = ClaudeSkill(
        name="issue_update",
        description="Update an issue",
        prompt_template="Update issue $ARGUMENTS",
    )
    register_skill_commands(app_core.registry, [skill], "langchain")

    response = app_core.handle_input("/issue_update 5")

    assert response.actions == (SendToLLM(text="Update issue 5"),)
```

(`AppCore` and `SendToLLM` are already imported at the top of `test_app_core.py`.)

### Negative pilot test (`test_app_pilot.py`)

Add near the other streaming tests. Uses `MagicMock` + `monkeypatch` (import
`from unittest.mock import MagicMock` at the top if not present; `monkeypatch`
is a pytest built-in fixture).

```python
async def test_model_stream_slash_text_never_dispatches(
    icoder_app: ICoderApp,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Model /skill-shaped text driven through the render path renders as
    plain text and never reaches registry.dispatch.

    Drives ICoderApp._handle_stream_event directly — the same entry ui/replay.py
    uses — so no human input is involved. The registry spy is a supporting
    check (the render path never references the registry); the load-bearing
    guarantee is the single-call-site test in test_self_invocation_guard.py.
    """
    app = icoder_app
    async with app.run_test() as pilot:
        spy = MagicMock(wraps=app._core.registry.dispatch)
        monkeypatch.setattr(app._core.registry, "dispatch", spy)

        app._handle_stream_event({"type": "text_delta", "text": "/issue_update 5"})
        app._handle_stream_event({"type": "done"})
        await pilot.pause()

        spy.assert_not_called()
        output = app.query_one(OutputLog)
        assert output.recorded_lines.count("/issue_update 5") == 1
```

## HOW

- **Positive:** `register_skill_commands(..., "langchain")` installs a real
  skill command; `handle_input` runs the production human path
  (`handle_input` -> `registry.dispatch` -> skill handler). The langchain
  handler expands `$ARGUMENTS`, so the result is `SendToLLM(text="Update issue 5")`.
- **Negative:** `_handle_stream_event` is the render-path entry; a `text_delta`
  buffers, and the `done` event flushes it to `OutputLog` (same flow verified
  by existing `test_streaming_*` tests via `output.recorded_lines`). The spy
  wraps the real `dispatch` and asserts it is never invoked.

## ALGORITHM (negative test core)

```
start app under pilot
wrap registry.dispatch with a spy (monkeypatch)
feed a slash-shaped text_delta, then a done event, to _handle_stream_event
pause the event loop
assert spy never called
assert the slash text appears once in OutputLog.recorded_lines (rendered as text)
```

## DATA

- Positive: `response.actions == (SendToLLM(text="Update issue 5"),)`.
- Negative: `spy.assert_not_called()`; `recorded_lines.count("/issue_update 5") == 1`.

## Quality gates

Run pylint, pytest (fast exclusion set, `-n auto` — the `textual_integration`
marker is NOT excluded, so the pilot test runs), mypy. `format_all.sh` before
commit.

## LLM prompt

> Implement Step 3 from `pr_info/steps/step_3.md` (context in
> `pr_info/steps/summary.md`). Using the MCP workspace tools only:
> (1) add `test_user_typed_skill_dispatches_and_invokes` to
> `tests/icoder/test_app_core.py`; (2) add
> `test_model_stream_slash_text_never_dispatches` to
> `tests/icoder/test_app_pilot.py`, adding `from unittest.mock import MagicMock`
> to its imports if absent. No production code changes. Then run
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check`
> (`extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`),
> and `mcp__tools-py__run_mypy_check`; fix until all pass. This is one commit.
