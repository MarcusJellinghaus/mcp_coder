# Step 4: Thread `from_github` through session_launch.py

> **Context**: See `pr_info/steps/summary.md` for the full plan.
> This step threads the `from_github` parameter through the session launch
> functions so the flag flows from the CLI to `create_startup_script()`.

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 4.

Add `from_github: bool = False` parameter to `process_eligible_issues()`,
`prepare_and_launch_session()`, and `regenerate_session_files()` in
session_launch.py. Thread it through to `create_startup_script()` and
`build_session()`. Write tests first (TDD), then implement. Run all three
code quality checks.
```

## Files to Modify

### Tests (write first)

**`tests/workflows/vscodeclaude/test_orchestrator_launch.py`** — Add/update tests:

- `test_prepare_and_launch_session_passes_from_github_to_startup_script`:
  Mock `create_startup_script` and call `prepare_and_launch_session(from_github=True)`.
  Assert `create_startup_script` was called with `from_github=True`.

- `test_prepare_and_launch_session_stores_from_github_in_session`:
  Call `prepare_and_launch_session(from_github=True)`. Assert returned session
  has `session["from_github"] is True`.

- `test_process_eligible_issues_passes_from_github`:
  Mock `prepare_and_launch_session` and call `process_eligible_issues(from_github=True)`.
  Assert `prepare_and_launch_session` was called with `from_github=True`.

- `test_regenerate_session_files_reads_from_github_from_session`:
  Create a session dict with `from_github: True`. Mock `create_startup_script`.
  Call `regenerate_session_files(session, issue)`. Assert `create_startup_script`
  was called with `from_github=True`.

- `test_regenerate_session_files_with_from_github_false`:
  Create a session dict with `from_github: False`. Mock `create_startup_script`.
  Call `regenerate_session_files(session, issue)`. Assert `create_startup_script`
  was called with `from_github=False`.

### Implementation

**`src/mcp_coder/workflows/vscodeclaude/session_launch.py`**

- WHERE: Three functions in session_launch.py
- WHAT: Add `from_github: bool = False` parameter to each
- HOW: Pass through the call chain, use `session["from_github"]` for restart

```python
def prepare_and_launch_session(
    ...,
    from_github: bool = False,     # ← NEW
) -> VSCodeClaudeSession:
    ...
    # Pass to create_startup_script
    script_path = create_startup_script(
        ...,
        from_github=from_github,
    )
    ...
    # Pass to build_session
    session = build_session(
        ...,
        from_github=from_github,
    )

def process_eligible_issues(
    ...,
    from_github: bool = False,     # ← NEW
) -> list[VSCodeClaudeSession]:
    ...
    session = prepare_and_launch_session(
        ...,
        from_github=from_github,
    )

def regenerate_session_files(
    session: VSCodeClaudeSession,
    issue: IssueData,
) -> Path:
    ...
    from_github = session["from_github"]
    script_path = create_startup_script(
        ...,
        from_github=from_github,
    )
```

## Data

- `from_github` flows: `process_eligible_issues()` → `prepare_and_launch_session()`
  → `create_startup_script()` and `build_session()`
- `regenerate_session_files()` reads `session["from_github"]` directly
  (required field, no `.get()` fallback needed)

## Verification

- All existing session_launch tests pass unchanged
- New tests verify flag threading
- pylint, mypy, pytest all green
