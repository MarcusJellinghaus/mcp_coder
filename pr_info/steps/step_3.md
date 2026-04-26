# Step 3: Update `session_launch.py` — rename param in launch functions

## Context
See `pr_info/steps/summary.md` for full issue context (#885).

Thread `skip_github_install` through `prepare_and_launch_session()` and `process_eligible_issues()`. (`regenerate_session_files()` was already cleaned up in Step 1.)

## LLM Prompt
> Implement Step 3 of issue #885 (see `pr_info/steps/summary.md` and this file `pr_info/steps/step_3.md`). Update `session_launch.py`: rename `install_from_github` to `skip_github_install` in `prepare_and_launch_session()` and `process_eligible_issues()` signatures. Also update `commands.py` call-site kwargs from `install_from_github=` to `skip_github_install=` to prevent TypeError. Note: `build_session()` kwarg was already removed in Step 1, `create_startup_script()` kwarg was already renamed in Step 2, and `regenerate_session_files()` was already cleaned up in Step 1. Update tests first (TDD), then source. Run all three code quality checks.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py`
- `src/mcp_coder/cli/commands/coordinator/commands.py`
- `tests/workflows/vscodeclaude/test_session_launch.py`
- `tests/workflows/vscodeclaude/test_session_launch_regenerate.py`

## WHAT

### `session_launch.py` — `prepare_and_launch_session()`
```python
def prepare_and_launch_session(
    ...
    # install_from_github: bool = False,  ← DELETE
    skip_github_install: bool = False,     # ← ADD
) -> VSCodeClaudeSession:
```

Changes inside the function:
- Update `create_startup_script()` call: the kwarg was already renamed to `skip_github_install=` in Step 2 — now update the variable from `install_from_github` to `skip_github_install` (i.e., `skip_github_install=install_from_github` becomes `skip_github_install=skip_github_install`)
- The `build_session()` call's `install_from_github=install_from_github` kwarg was already removed in Step 1

### `session_launch.py` — `process_eligible_issues()`
```python
def process_eligible_issues(
    ...
    # install_from_github: bool = False,  ← DELETE
    skip_github_install: bool = False,     # ← ADD
) -> list[VSCodeClaudeSession]:
```

Change inside the function:
- Pass `skip_github_install=skip_github_install` to `prepare_and_launch_session()` (instead of `install_from_github=install_from_github`)

### `session_launch.py` — `regenerate_session_files()` *(no changes needed)*

The `regenerate_session_files()` cleanup was already completed in Step 1:
- The `install_from_github = session.get("install_from_github", False)` line was deleted
- The `install_from_github=install_from_github` kwarg was removed from the `create_startup_script()` call

The function now calls `create_startup_script()` without any install flag (auto-detect via default). No further changes needed here.

### `commands.py` — Update call-site kwargs

The function signatures renamed in this step are called from `commands.py`. Update the kwargs to prevent TypeError between Steps 3 and 5:

- At line ~600 (`execute_coordinator_vscodeclaude`): change `install_from_github=install_from_github` to `skip_github_install=install_from_github` in the `process_eligible_issues()` call
- At line ~759 (`_handle_intervention_mode`): change `install_from_github=install_from_github` to `skip_github_install=install_from_github` in the `prepare_and_launch_session()` call

Scope: only the kwarg names change. The variable rename (`install_from_github` → `skip_github_install`) and CLI flag change happen in Step 5.

## ALGORITHM
```
1. prepare_and_launch_session: rename param to skip_github_install, update variable in create_startup_script call
2. process_eligible_issues: rename param to skip_github_install, pass to prepare_and_launch_session
(regenerate_session_files was already cleaned up in Step 1 — no action here)
```

## Test changes

### `test_session_launch.py` — `TestInstallFromGithubThreading`

1. **`test_prepare_and_launch_session_passes_install_from_github_to_startup_script`**: 
   - Rename to `test_prepare_and_launch_session_passes_skip_github_install_to_startup_script`
   - Pass `skip_github_install=True` instead of `install_from_github=True`
   - Assert `mock_create_startup.call_args.kwargs["skip_github_install"] is True`

2. **`test_prepare_and_launch_session_stores_install_from_github_in_session`**:
   - **Delete this test entirely** — `install_from_github` is no longer stored in session

3. **`test_process_eligible_issues_passes_install_from_github`**:
   - Rename to `test_process_eligible_issues_passes_skip_github_install`
   - Pass `skip_github_install=True` instead of `install_from_github=True`
   - Assert `mock_launch.call_args.kwargs["skip_github_install"] is True`

4. **`test_regenerate_session_files_reads_install_from_github_from_session`**:
   - Rewrite: verify `create_startup_script` is called **without** `skip_github_install` (or with default `False`)
   - The `"install_from_github": True` was already removed from the session dict in Step 1 (mechanical cleanup)

5. **`test_regenerate_session_files_with_install_from_github_false`**:
   - **Delete this test** — regenerate no longer reads from session, always auto-detects
   - (The `"install_from_github": False` in its session dict was already removed in Step 1)

### `test_session_launch_regenerate.py`
- `mock_session` fixture: `"install_from_github": False` was already removed from session dict in Step 1 (mechanical cleanup). No changes needed here.

## Commit message
```
fix(vscodeclaude): thread skip_github_install through session launch (#885)

Rename install_from_github to skip_github_install in
prepare_and_launch_session() and process_eligible_issues().
Also update commands.py call-site kwargs to match.
```
