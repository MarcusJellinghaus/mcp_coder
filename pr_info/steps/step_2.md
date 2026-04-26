# Step 2: Fix core bug — auto-detect GitHub installs in `workspace.py`

## Context
See `pr_info/steps/summary.md` for full issue context (#885).

This is the core bug fix. Remove the `if install_from_github:` guard so `_build_github_install_section()` always runs. Replace the `install_from_github` param with `skip_github_install` for opt-out. Add a cache awareness comment.

## LLM Prompt
> Implement Step 2 of issue #885 (see `pr_info/steps/summary.md` and this file `pr_info/steps/step_2.md`). Fix the core bug in `workspace.py`: remove the `install_from_github` guard, rename the param to `skip_github_install`, and add a cache comment. Update tests first (TDD), then source. Run all three code quality checks after changes.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/workspace.py`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` *(minimal change — only the `prepare_and_launch_session()` call site; `regenerate_session_files()` was cleaned in Step 1, full rework in Step 3)*
- `tests/workflows/vscodeclaude/test_workspace_startup_script_github.py`

## WHAT

### `workspace.py` — `create_startup_script()`

**Signature change:**
```python
def create_startup_script(
    ...
    # install_from_github: bool = False,  ← DELETE
    skip_github_install: bool = False,     # ← ADD
) -> Path:
```

**Logic change** (inside the `if is_windows:` block, after `venv_section` is built):
```python
# BEFORE (guarded — the bug):
if install_from_github:
    github_install_section = _build_github_install_section(folder_path)
    venv_section = venv_section + github_install_section

# AFTER (always auto-detect):
if not skip_github_install:
    github_install_section = _build_github_install_section(folder_path)
    venv_section = venv_section + github_install_section
```

**Docstring**: Update the `install_from_github` param doc to `skip_github_install` with:
```
skip_github_install: If True, skip reading [tool.mcp-coder.install-from-github]
    from pyproject.toml. Default False (auto-detect).
```

### `workspace.py` — `_build_github_install_section()`

**Add cache comment** after the `uv pip install` lines are built, before `return`:
```python
# NOTE: If stale git cache becomes an issue, add --reinstall to the
# uv pip install commands above to force re-fetch from GitHub.
```

### `session_launch.py` — Update `create_startup_script()` call site

This is ONLY updating the kwarg name at the `prepare_and_launch_session()` call site. Do not touch anything else in `session_launch.py` — the remaining changes to this file (renaming the `install_from_github` parameter in function signatures) happen in Step 3.

**In `prepare_and_launch_session()`** (line ~196), change:
```python
install_from_github=install_from_github,
```
to:
```python
skip_github_install=install_from_github,
```
(Note: the *variable* is still called `install_from_github` at this point because the function signature hasn't been renamed yet — that happens in Step 3. We're only fixing the kwarg name to match `create_startup_script()`'s renamed parameter.)

**`regenerate_session_files()` is already clean** — Step 1 removed the `install_from_github` variable and the `install_from_github=install_from_github` kwarg from `create_startup_script()`. The function now calls `create_startup_script()` without any install flag, relying on the default (`False` before this step, `False` for `skip_github_install` after). No changes needed here.

## ALGORITHM
```
1. Read skip_github_install param (default False)
2. If not skip_github_install:
3.   Call _build_github_install_section(folder_path)
4.   Append result to venv_section (empty string = no-op)
5. Continue with script generation as before
```

## DATA
- `skip_github_install: bool = False` — new param (replaces `install_from_github: bool = False`)
- Return value unchanged: `Path` to created script

## Test changes

### `test_workspace_startup_script_github.py`

Rewrite `TestCreateStartupScriptFromGithub`:

1. **`test_from_github_injects_install_commands`**: Remove `install_from_github=True` — should now work **without** the flag (this is the core bug test). Keep all content assertions.

2. **`test_from_github_false_no_github_section`**: Rename to `test_skip_github_install_suppresses_section`. Pass `skip_github_install=True` instead of `install_from_github=False`. Assert no "GitHub override" in content.

3. **`test_from_github_missing_config_section`**: Remove `install_from_github=True` — auto-detect with no config should produce no GitHub section. Keep assertion.

4. **`test_from_github_empty_packages`**: Remove `install_from_github=True`. Keep assertion.

5. **`test_from_github_only_packages`**: Remove `install_from_github=True`. Keep assertion.

6. **`test_from_github_only_packages_no_deps`**: Remove `install_from_github=True`. Keep assertion.

7. **`test_from_github_missing_pyproject_toml`**: Remove `install_from_github=True`. Keep assertion.

**Key pattern**: Most tests just delete `install_from_github=True` because auto-detect is now the default. Only the opt-out test passes `skip_github_install=True`.

## Commit message
```
fix(vscodeclaude): auto-detect GitHub installs from pyproject.toml (#885)

Remove the install_from_github guard in create_startup_script() so
_build_github_install_section() always runs. The function is already
idempotent (returns "" when no packages configured).

Replace install_from_github param with skip_github_install opt-out.
Add cache awareness comment near uv pip install generation.
```
