# Step 1: Add `from_github` to data layer (types + helpers)

> **Context**: See `pr_info/steps/summary.md` for the full plan.
> This step adds the `from_github` field to the session TypedDict and the
> `build_session()` helper, establishing the data foundation for all subsequent steps.

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 1.

Add `from_github: NotRequired[bool]` field to `VSCodeClaudeSession` TypedDict
and update `build_session()` to accept and include it. Update existing tests
that assert on the TypedDict field set. Write new tests first (TDD), then
implement. Run all three code quality checks (pylint, pytest, mypy) after changes.
```

## Files to Modify

### Tests (write first)

**`tests/workflows/vscodeclaude/test_types.py`** — Update existing tests:
- `test_vscodeclaude_session_type_structure`: Add `"from_github"` to the expected fields set.
- `test_vscodeclaude_session_creation`: Add `"from_github": False` to the session dict literal.

**`tests/workflows/vscodeclaude/test_types.py`** — Add test:
- `test_vscodeclaude_session_supports_from_github`: Verify a `VSCodeClaudeSession`
  dict can include `from_github: True` and the value is accessible.

**`tests/workflows/vscodeclaude/test_helpers.py`** — Add tests:
- `test_build_session_with_from_github_true`: Call `build_session(..., from_github=True)`,
  assert `session["from_github"] is True`.
- `test_build_session_with_from_github_false`: Call `build_session(..., from_github=False)`,
  assert `session["from_github"] is False`.
- `test_build_session_default_from_github`: Call `build_session()` without `from_github`
  (default), assert `session["from_github"] is False`.

### Implementation

**`src/mcp_coder/workflows/vscodeclaude/types.py`**

- WHERE: `VSCodeClaudeSession` TypedDict
- WHAT: Add `from_github: bool` field
- HOW: New field in the TypedDict class body

```python
from typing import NotRequired, TypedDict

class VSCodeClaudeSession(TypedDict):
    folder: str
    repo: str
    issue_number: int
    status: str
    vscode_pid: int | None
    started_at: str
    is_intervention: bool
    from_github: NotRequired[bool]  # ← NEW (optional for backward compat)
```

**`src/mcp_coder/workflows/vscodeclaude/helpers.py`**

- WHERE: `build_session()` function
- WHAT: Add `from_github: bool = False` parameter
- HOW: New keyword argument with default, added to return dict

```python
def build_session(
    folder: str,
    repo: str,
    issue_number: int,
    status: str,
    vscode_pid: int,
    is_intervention: bool,
    from_github: bool = False,   # ← NEW
) -> VSCodeClaudeSession:
    return {
        ...,
        "from_github": from_github,  # ← NEW
    }
```

## Data

- `VSCodeClaudeSession["from_github"]` → `NotRequired[bool]`
- Backward compat: existing session JSON files lack this key;
  all consumers must use `session.get("from_github", False)`

## Verification

- All existing tests pass (new param has default value)
- New tests pass
- pylint, mypy, pytest all green
