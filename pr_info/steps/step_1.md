# Step 1: Remove `install_from_github` from session state

## Context
See `pr_info/steps/summary.md` for full issue context (#885).

This step removes the `install_from_github` field from the session TypedDict and the `build_session()` helper. This is the foundation — all later steps depend on this field being gone.

## LLM Prompt
> Implement Step 1 of issue #885 (see `pr_info/steps/summary.md` and this file `pr_info/steps/step_1.md`). Remove the `install_from_github` field from `VSCodeClaudeSession` TypedDict and the `build_session()` function. Update all tests first (TDD), then update the source files. Run all three code quality checks after changes.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/types.py`
- `src/mcp_coder/workflows/vscodeclaude/helpers.py`
- `tests/workflows/vscodeclaude/test_types.py`
- `tests/workflows/vscodeclaude/test_helpers.py`

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

## Commit message
```
fix(vscodeclaude): remove install_from_github from session state (#885)

Remove install_from_github field from VSCodeClaudeSession TypedDict
and build_session() helper. Install behavior will be derived from
pyproject.toml at script generation time, not stored as session state.
```
