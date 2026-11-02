# Step 1 — Branch guard: refuse commits on protected branches / detached HEAD

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`.
> Follow TDD: write/adjust the tests first, then the implementation.
> Do not change the CLI parser, `main.py` or the catalog in this step.
> Run pylint, mypy and the fast pytest suite (see CLAUDE.md); all must pass.
> Run `run_format_code`, then make exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/commit.py`
- `src/mcp_coder/workflow_utils/commit_operations.py`
- `tests/cli/commands/test_commit_push.py`
- `tests/cli/commands/test_commit.py`

## WHAT

### New helper in `commit.py`

```python
_PROTECTED_BRANCHES = frozenset({"main", "master"})

def _branch_refusal(project_dir: Path) -> tuple[bool, str] | None:
    """Check whether committing/pushing on the current branch is refused.

    Returns:
        None if the branch is allowed; (False, "") if the current branch cannot
        be determined; (True, branch) if the branch is protected.
    """
```

### ALGORITHM (`_branch_refusal`)

```
branch = get_current_branch_name(project_dir)
if branch is None: return (False, "")          # do NOT call get_default_branch_name
default = get_default_branch_name(project_dir)
protected = _PROTECTED_BRANCHES | ({default} if default else set())
return (True, branch) if branch in protected else None
```

### Pre-check in `execute_commit_auto` (after `validate_git_repository`, before `resolve_llm_method`)

```
refusal = _branch_refusal(project_dir)
if refusal is not None:
    is_protected, branch = refusal
    if is_protected: logger.error("Refusing to commit on protected branch '%s'", branch)
    else: logger.error("Refusing to commit: cannot determine current branch (detached HEAD or unreadable HEAD)")
    return 1
```

### Push guard in `_push_after_commit`

- Keep the existing `branch = get_current_branch_name(...)` / `if branch is None:`
  block and its message "Cannot push: not on a branch" unchanged (exit 2).
- Replace the `default` / `blocked` computation with:
  ```
  if _branch_refusal(project_dir) is not None:
      logger.error("Refusing to push to protected branch '%s'", branch)
      return 2
  ```

### Text updates

- `execute_commit_auto` docstring: "Execute commit command with optional preview."
  Exit-code line: "0 for success or preview cancelled, 1 for validation error or
  refused branch, 2 for commit/LLM/push error".
- Log message: `"Starting commit with preview=%s"`.
- `commit_operations.py`: "... before running commit auto." → "... before running commit."

## DATA

- `_branch_refusal` → `None | tuple[bool, str]` (see above).
- `execute_commit_auto` exit codes: 0 ok / preview cancelled; 1 not a repo, no
  changes, refused branch; 2 LLM, commit or push failure.

## Tests (write first)

### `tests/cli/commands/test_commit_push.py`

1. Autouse fixture (module level) patching both lookups to a feature branch:
   ```python
   @pytest.fixture(autouse=True)
   def _feature_branch() -> Iterator[None]:
       with patch(f"{MODULE}.get_current_branch_name", return_value="feature/x"), \
            patch(f"{MODULE}.get_default_branch_name", return_value="main"):
           yield
   ```
   Existing `TestPushAfterCommit` tests keep their own `@patch` decorators,
   which override the fixture.
2. `TestPushAfterCommit`: add `test_push_refused_on_master_when_default_main`
   (current `"master"`, default `"main"`) → returns 2, `"protected branch"` in log.
3. New class `TestCommitBranchGuard` with one parametrized test:
   - params `(current, default)`: `("main", "main")`, `("master", "main")`,
     `("develop", "develop")`, `(None, "main")`; crossed with `push` in
     `[True, False]`.
   - Patch `get_current_branch_name` / `get_default_branch_name` (override
     fixture), `validate_git_repository` → `(True, None)`,
     `generate_commit_message_with_llm`, `commit_staged_files`,
     `_push_after_commit`, `builtins.input`.
   - Args: `Namespace(preview=True, llm_method="claude", project_dir="/repo", push=push)`.
   - Assert: result `== 1`; LLM generator, `commit_staged_files`, `input`
     and `_push_after_commit` not called.
   - Assert log substring: `"protected branch"` when `current` is not None,
     else `"cannot determine current branch"` and `get_default_branch_name`
     not called.

### `tests/cli/commands/test_commit.py`

- Add the same autouse fixture (with `Iterator` import) so every
  `execute_commit_auto` test past validation runs on a feature branch
  (covers `TestExecuteCommitAuto`, `TestPreviewModeLogic`,
  `TestExecuteCommitAutoResolveTuple`, `TestCommitAutoClaudeCwd`).
- In `test_execute_commit_auto_no_changes`: mocked error string
  "... before running commit auto." → "... before running commit.".
- Do not add new tests here (file-size gate).

## Done when

- All new tests fail before the implementation and pass after.
- pylint, mypy and the fast pytest suite pass.
