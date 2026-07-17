# Step 2 — `InputSubmitted` post-site invariant

**Reference:** `pr_info/steps/summary.md`
**Acceptance criteria:** AC4 (reworded observable, per design #1037 §10)
**Commit:** one — test + marker comment + checks passing.

## Goal

Assert the observable that locks the "Enter-only" assumption: **no production
code posts `InputSubmitted` outside `input_area.py`**. There is no public API
to distinguish a physical from a synthetic keypress, so we assert the
source-level observable instead of driving a keypress harness (KISS: a source
search, not a Textual pilot).

## TDD order

1. Add the source-search test to the file created in Step 1.
2. Add a marker comment at the `post_message(self.InputSubmitted(...))` site.
3. Run all three quality gates.

## WHERE

- **Modify:** `tests/icoder/test_self_invocation_guard.py` (append one test;
  reuse the `_call_sites` helper from Step 1)
- **Modify:** `src/mcp_coder/icoder/ui/widgets/input_area.py`

## WHAT

### Test (append to the Step 1 file)

```python
def test_input_submitted_constructed_only_in_input_area() -> None:
    """`InputSubmitted(...)` is constructed only inside input_area.py.

    The submit message that reaches handle_input->dispatch is posted only from
    InputArea's Enter-keypress handler. If any other production module were to
    construct/post it, model output could reach dispatch. `InputSubmitted\\(`
    matches both the class definition and the post site — both live in
    input_area.py.
    """
    hits = _call_sites(r"InputSubmitted\(")
    files = {name for name, _ in hits}
    assert files == {"input_area.py"}, f"unexpected InputSubmitted sites: {hits}"
```

### Production edit (marker comment only)

In `input_area.py`, at the single post site inside `_on_key`, immediately above
`self.post_message(self.InputSubmitted(text))`:

```python
            # SECURITY BOUNDARY (#1040): the ONLY place InputSubmitted is
            # posted — a human Enter keypress. This is what reaches
            # AppCore.handle_input -> registry.dispatch. Model/stream output
            # must never post this message. Locked by
            # tests/icoder/test_self_invocation_guard.py.
            if text:
                self.post_message(self.InputSubmitted(text))
                self.clear()
```

(Only the comment is added; the surrounding `if text:` / `post_message` /
`clear()` lines are unchanged.)

## HOW

- Reuses `_call_sites(pattern)` from Step 1 — no new helper.
- `\.dispatch\(` style precision is not needed here; `InputSubmitted\(` matches
  the class def and the construction, both in `input_area.py`. The type
  reference in `app.py` (`InputArea.InputSubmitted)`) has no `(` after the name
  and is correctly not matched.

## ALGORITHM (test core)

```
hits = _call_sites(r"InputSubmitted\(")
files = set of filenames in hits
assert files == {"input_area.py"}
```

## DATA

- Test asserts the set of matching filenames equals `{"input_area.py"}`.

## Quality gates

Run pylint, pytest (fast exclusion set, `-n auto`), mypy. `format_all.sh`
before commit.

## LLM prompt

> Implement Step 2 from `pr_info/steps/step_2.md` (context in
> `pr_info/steps/summary.md`). Using the MCP workspace tools only:
> (1) append `test_input_submitted_constructed_only_in_input_area` to
> `tests/icoder/test_self_invocation_guard.py`, reusing the existing
> `_call_sites` helper; (2) add the specified marker comment directly above the
> `self.post_message(self.InputSubmitted(text))` line in
> `src/mcp_coder/icoder/ui/widgets/input_area.py`, changing nothing else. Then
> run `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check`
> (`extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`),
> and `mcp__tools-py__run_mypy_check`; fix until all pass. This is one commit.
