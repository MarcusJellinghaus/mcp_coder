# Step 1: Remove `install_from_github` from session state

## Context
See `pr_info/steps/summary.md` for full issue context (#885).

This step removes the `install_from_github` field from the session TypedDict and the `build_session()` helper. This is the foundation — all later steps depend on this field being gone.

## LLM Prompt
> Implement Step 1 of issue #885 (see `pr_info/steps/summary.md` and this file `pr_info/steps/step_1.md`). Remove the `install_from_github` field from `VSCodeClaudeSession` TypedDict and the `build_session()` function. Update all tests first (TDD), then update the source files. Run all three code quality checks after changes.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/types.py`
- `src/mcp_coder/workflows/vscodeclaude/helpers.py`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` *(minimal change — only the `build_session()` call site; full rework happens in Step 3)*
- `tests/workflows/vscodeclaude/test_types.py`
- `tests/workflows/vscodeclaude/test_helpers.py`
- `tests/workflows/vscodeclaude/test_cleanup.py`
- `tests/workflows/vscodeclaude/test_status_display.py`
- `tests/workflows/vscodeclaude/test_sessions.py`
- `tests/workflows/vscodeclaude/test_session_restart_cache.py`
- `tests/workflows/vscodeclaude/test_closed_issues_integration.py`
- `tests/workflows/vscodeclaude/test_cache_aware.py`
- `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py`

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

**This is ONLY the `build_session()` call site.** Do not touch anything else in `session_launch.py` — the remaining changes to this file (removing the `install_from_github` parameter from `launch_session()` itself and its callers) happen in Step 3.

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

The change is purely mechanical: search for `"install_from_github": False,` (and variants like `"install_from_github": True,`) in each file and delete the line. No logic changes needed — these are just session dict literals that must match the updated TypedDict.

## Commit message
```
fix(vscodeclaude): remove install_from_github from session state (#885)

Remove install_from_github field from VSCodeClaudeSession TypedDict
and build_session() helper. Install behavior will be derived from
pyproject.toml at script generation time, not stored as session state.
```
