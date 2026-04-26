# Step 1: Remove `install_from_github` from session state

## Context
See `pr_info/steps/summary.md` for full issue context (#885).

This step removes the `install_from_github` field from the session TypedDict and the `build_session()` helper. This is the foundation — all later steps depend on this field being gone.

## LLM Prompt
> Implement Step 1 of issue #885 (see `pr_info/steps/summary.md` and this file `pr_info/steps/step_1.md`). Remove the `install_from_github` field from `VSCodeClaudeSession` TypedDict and the `build_session()` function. Also remove the `install_from_github` line from the `updated_session` dict in `session_restart.py` to prevent mypy failure. Update all tests first (TDD), then update the source files. Run all three code quality checks after changes.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/types.py`
- `src/mcp_coder/workflows/vscodeclaude/helpers.py`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` *(two changes: remove `build_session()` kwarg AND clean up `regenerate_session_files()` — see WHAT section)*
- `tests/workflows/vscodeclaude/test_types.py`
- `tests/workflows/vscodeclaude/test_helpers.py`
- `tests/workflows/vscodeclaude/test_cleanup.py`
- `tests/workflows/vscodeclaude/test_status_display.py`
- `tests/workflows/vscodeclaude/test_sessions.py`
- `tests/workflows/vscodeclaude/test_session_restart_cache.py`
- `tests/workflows/vscodeclaude/test_closed_issues_integration.py`
- `tests/workflows/vscodeclaude/test_cache_aware.py`
- `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py`
- `src/mcp_coder/workflows/vscodeclaude/session_restart.py`
- `tests/workflows/vscodeclaude/test_session_launch.py`

## WHAT

### `types.py` — Remove field from TypedDict
```python
class VSCodeClaudeSession(TypedDict):
    folder: str
    repo: str
    issue_number: int
    status: str
    vscode_pid: int | None
    started_at: str
    is_intervention: bool
    # install_from_github: bool  ← DELETE THIS LINE
```

### `helpers.py` — Remove param from `build_session()`
```python
def build_session(
    folder: str,
    repo: str,
    issue_number: int,
    status: str,
    vscode_pid: int,
    is_intervention: bool,
    # install_from_github: bool = False,  ← DELETE
) -> VSCodeClaudeSession:
```
Remove `"install_from_github": install_from_github` from the returned dict.

### `session_launch.py` — Remove kwarg from `build_session()` call site

At line ~227, the `build_session()` call passes `install_from_github=install_from_github`. Delete that kwarg:

```python
        session = build_session(
            folder=folder_str,
            repo=repo_full_name,
            issue_number=issue_number,
            status=status,
            vscode_pid=pid,
            is_intervention=is_intervention,
            # install_from_github=install_from_github,  ← DELETE THIS LINE
        )
```

**`build_session()` call site only** — do not touch the `prepare_and_launch_session()` or `process_eligible_issues()` signatures yet (those happen in Step 3).

### `session_launch.py` — Remove `install_from_github` from `regenerate_session_files()`

With `install_from_github` removed from the `VSCodeClaudeSession` TypedDict, `session.get("install_from_github", False)` in `regenerate_session_files()` will fail mypy. Clean this up now:

1. **Delete** this line (~line 428):
```python
install_from_github = session.get("install_from_github", False)
```

2. **Remove** the `install_from_github=install_from_github` kwarg from the `create_startup_script()` call (~line 452):
```python
    script_path = create_startup_script(
        ...
        # install_from_github=install_from_github,  ← DELETE THIS LINE
    )
```

The function will then use `create_startup_script()`'s default `install_from_github=False` — functionally equivalent, since auto-detect isn't implemented until Step 2.

### `session_restart.py` — Remove field from `updated_session` dict

In `restart_closed_sessions()`, delete the `"install_from_github": session.get("install_from_github", False),` line from the `updated_session` dict (around line 435). This prevents mypy failure between Steps 1 and 4.

Scope: only this one line change. The test cleanup for `test_session_restart.py` and `test_session_restart_closed_sessions.py` remains in Step 4.

## HOW
- Direct field deletion in TypedDict
- Parameter removal from function signature
- Key removal from returned dict literal

## Test changes

### `test_types.py`
- `test_vscodeclaude_session_type_structure`: Remove `"install_from_github"` from `expected_fields` set
- `test_vscodeclaude_session_creation`: Remove `"install_from_github": False` from session dict, remove `isinstance` assert
- `test_vscodeclaude_session_supports_install_from_github`: **Delete entire test**

### `test_helpers.py`
- **Delete entire `TestBuildSessionInstallFromGithub` class** (3 tests that verify `install_from_github` param behavior)

### Mechanical test cleanup — remove `install_from_github` from session dict literals

When the `install_from_github` field is deleted from `VSCodeClaudeSession`, every test file that constructs session dict literals with `"install_from_github": False` will fail. Remove this key-value pair from all session dicts in the following files:

| File | ~Occurrences |
|------|-------------|
| `tests/workflows/vscodeclaude/test_cleanup.py` | 39 |
| `tests/workflows/vscodeclaude/test_status_display.py` | 29 |
| `tests/workflows/vscodeclaude/test_sessions.py` | 22 |
| `tests/workflows/vscodeclaude/test_session_restart_cache.py` | 7 |
| `tests/workflows/vscodeclaude/test_closed_issues_integration.py` | 6 |
| `tests/workflows/vscodeclaude/test_cache_aware.py` | 4 |
| `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py` | 3 |
| `tests/workflows/vscodeclaude/test_session_launch.py` | 2 |

The `test_session_launch.py` occurrences are in the `regenerate_session_files` tests — two session dicts (lines ~445 and ~509) contain `"install_from_github"` that must be removed when the TypedDict field is deleted.

The change is purely mechanical: search for `"install_from_github": False,` (and variants like `"install_from_github": True,`) in each file and delete the line. No logic changes needed — these are just session dict literals that must match the updated TypedDict.

## Commit message
```
fix(vscodeclaude): remove install_from_github from session state (#885)

Remove install_from_github field from VSCodeClaudeSession TypedDict
and build_session() helper. Also clean up regenerate_session_files()
and the updated_session dict in session_restart.py to stop reading
the deleted field. Install behavior will be derived from pyproject.toml
at script generation time, not stored as session state.
```
