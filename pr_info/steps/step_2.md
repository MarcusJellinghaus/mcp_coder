# Step 2 — Add `mirror` callback to `OutputLog`

**Goal:** `OutputLog` accepts an optional one-arg callback and invokes
it from the same call sites that already populate `_recorded`, plus
the `write("")` blank-spacer path which is **not** currently recorded.
The widget remains ignorant of `EventLog`.

Refer to `pr_info/steps/summary.md` for the full architectural
overview. Step 1 (`EventLog.write_chat`) must be merged first because
step 3 will wire `mirror=event_log.write_chat`; step 2 can be written
against a plain `Mock`.

## WHERE

- **Implementation:**
  `src/mcp_coder/icoder/ui/widgets/output_log.py`
- **Tests:** `tests/icoder/ui/test_output_log.py`

## WHAT

Modify the existing `OutputLog` class:

```python
from typing import Callable

class OutputLog(RichLog):
    def __init__(
        self,
        *,
        mirror: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None: ...
```

Behavior:

- `OutputLog.write(content, ...)`
  - `str` → previously not recorded; **still not recorded**, but if
    `self._mirror` is set, call `self._mirror(content)` (this is what
    delivers blank-line spacers `write("")` to the `.txt`).
  - `Text` → no change (covered by `append_text` path).
  - Other renderable (e.g. `Markdown`) → append `markup` to
    `_recorded` *and* call `self._mirror(markup)` when set.

- `OutputLog.append_text(text, style=None)` → append to `_recorded`
  *and* call `self._mirror(text)` when set.

The mirror is a fire-and-forget hook: `OutputLog` does not try/except
around it because `EventLog.write_chat` already swallows its own
errors (step 1). The widget therefore stays trivially simple.

## HOW

- Store the callback on `self._mirror`.
- The three call sites are the same three lines that already touch
  `self._recorded`; the mirror call goes immediately after each
  `self._recorded.append(...)`.
- For the `str` branch in `write()`, there is no
  `self._recorded.append` today — add only the mirror invocation, do
  not change `_recorded` semantics (existing tests rely on it).

## ALGORITHM (pseudocode)

```
__init__(*, mirror=None, **kwargs):
    super().__init__(wrap=True, **kwargs)
    self._recorded = []
    self._mirror = mirror

write(content):
    if isinstance(content, str):
        if self._mirror: self._mirror(content)   # ← new
    elif isinstance(content, Text):
        pass
    else:
        markup = getattr(content, "markup", None) or str(content)
        self._recorded.append(markup)
        if self._mirror: self._mirror(markup)    # ← new
    super().write(content, ...)

append_text(text, style=None):
    self._recorded.append(text)
    if self._mirror: self._mirror(text)          # ← new
    super().write(Text(text, style=style) if style else text)
```

## DATA

- Constructor:
  `OutputLog(*, mirror: Callable[[str], None] | None = None, **kwargs)`.
- No new public methods, no new public attributes, no change to
  `recorded_lines`.
- `mirror` is invoked with exactly one positional `str`. Empty
  strings ARE passed through (blank-line spacers).

## TDD — Tests to add first

Append to `tests/icoder/ui/test_output_log.py` (module already exists
and is marked `pytest.mark.textual_integration`). Use
`unittest.mock.Mock` for the callback.

1. **`test_mirror_called_for_blank_line_spacer`**
   Construct an app yielding `OutputLog(mirror=mock)`. After mount,
   call `output.write("")`. Assert `mock.call_args_list ==
   [call("")]`. (This is the new behavior — covers the spacer path.)

2. **`test_mirror_called_for_markdown_write`**
   Same scaffolding. Call `output.write(Markdown("# Hello\n**bold**"))`.
   Assert `mock` was called exactly once with a non-empty `str`
   containing `"Hello"` (matches what is appended to `_recorded`).

3. **`test_mirror_called_for_append_text`**
   Call `output.append_text("plain")` and
   `output.append_text("styled", style="dim")`. Assert
   `mock.call_args_list == [call("plain"), call("styled")]`.

4. **`test_no_mirror_when_callback_is_none`**
   Construct `OutputLog()` (default `mirror=None`). Call `write("")`,
   `write(Markdown("x"))`, and `append_text("y")`. Assert no error
   raised and `recorded_lines` still behaves as before
   (`"x"`-markup and `"y"` recorded; `""` not recorded).

5. **`test_existing_recorded_semantics_preserved`**
   Re-run the two existing assertions
   (`test_output_log_write_records_text` and
   `test_output_log_append_text_records`) implicitly by leaving them
   in place. Confirm via pytest that they remain green when adding
   the new parameter.

## Implementation order (TDD loop)

1. Add the four new tests; confirm they fail with the expected
   `mock` assertion errors / `TypeError` (because `mirror=` does not
   yet exist).
2. Add the `mirror` parameter and the three `self._mirror(...)`
   call sites in `output_log.py`. Re-run pytest until all new and
   pre-existing tests pass.
3. Run all three quality gates per `CLAUDE.md`:
   - `mcp__tools-py__run_pylint_check`
   - `mcp__tools-py__run_pytest_check` with
     `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
   - `mcp__tools-py__run_mypy_check`
4. Stage + commit (one commit). Message suggestion:
   `iCoder: add mirror callback to OutputLog (#982)`.

## Out of scope for this step

- No change to `ICoderApp.compose()` — the callback is still `None`
  in production after step 2; the wiring happens in step 3.
- No change to `EventLog`.
- No documentation change.

## LLM prompt for this step

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`.
> Implement step 2 only. Strictly TDD: add the four new tests in
> `tests/icoder/ui/test_output_log.py` first (using
> `unittest.mock.Mock` for the callback), then add the `mirror`
> parameter and the three `self._mirror(...)` call sites in
> `src/mcp_coder/icoder/ui/widgets/output_log.py` (string branch of
> `write`, non-`Text` renderable branch of `write`, and
> `append_text`). Do not modify `ICoderApp` or `EventLog`. Existing
> tests for `OutputLog` must remain green. Use only MCP tools per
> `CLAUDE.md`. Run all three quality gates (`run_pylint_check`,
> `run_pytest_check` with `-n auto` and the integration-exclusion
> `-m` filter, `run_mypy_check`) until they all pass. Stage and
> commit exactly one commit when green.
