# Step 3: Wire `verify_github()` into `execute_verify()` orchestration + tests

**See:** `pr_info/steps/summary.md` for full context.

## LLM Prompt

> Wire `verify_github()` into `execute_verify()` in `src/mcp_coder/cli/commands/verify.py`:
> import it, call it, display the GITHUB section after PROJECT and before LLM PROVIDER,
> collect install hints, and pass `github_result` to `_compute_exit_code()`.
> Add orchestration tests in `test_verify_orchestration.py`.
> See `pr_info/steps/summary.md` for full context.

## WHERE

- `src/mcp_coder/cli/commands/verify.py` — imports (line ~20) and `execute_verify()` (line ~451)
- `tests/cli/commands/test_verify_orchestration.py` — new test methods

## WHAT

### Import (top of file)

```python
from ...mcp_workspace_github import verify_github
```

Hard import — no try/except guard.

### In `execute_verify()`, after `_print_project_section()` (line ~523), before the LLM PROVIDER section (line ~538):

```python
github_result = verify_github(project_dir)
print(_format_section("GITHUB", github_result, symbols))
```

### Install hints — add github_result to collection (line ~704):

```python
all_hints.extend(_collect_install_hints(github_result))
```

### Exit code — pass to `_compute_exit_code()` call (line ~721):

```python
exit_code = _compute_exit_code(
    ...,
    github_result=github_result,
)
```

### Update module docstring (line 1-4):

Update "three domain verification functions" to "four" to include GitHub.

## HOW

- Import through existing shim `mcp_coder.mcp_workspace_github`
- `verify_github(project_dir)` takes a `Path` — `project_dir` is already resolved as `Path` earlier in the function
- `_format_section` and `_collect_install_hints` already handle the standard result dict shape — no changes needed to those functions
- `_compute_exit_code` already accepts `github_result` after Step 1

## ALGORITHM

```
github_result = verify_github(project_dir)
print(_format_section("GITHUB", github_result, symbols))
# ... later in install hints ...
all_hints.extend(_collect_install_hints(github_result))
# ... later in exit code ...
exit_code = _compute_exit_code(..., github_result=github_result)
```

## DATA

- `verify_github()` returns: `dict[str, Any]` with `overall_ok: bool` and entries like `{"ok": bool, "value": str, "severity": str, "install_hint"?: str}`
- Checks 1–4 (token, auth, repo URL, repo access) are `severity: "error"` and drive `overall_ok`
- Checks 5–9 (branch protection) are `severity: "warning"` only

## TESTS (write first)

Add to `test_verify_orchestration.py`:

1. `test_github_section_displayed_after_project` — mock `verify_github` to return a result dict, assert output contains `=== GITHUB` and it appears after `PROJECT` and before `LLM PROVIDER`
2. `test_verify_github_called_with_project_dir` — assert `verify_github` was called with the resolved `project_dir`
3. `test_github_install_hints_collected` — mock `verify_github` returning an entry with `install_hint`, assert hint appears in INSTALL INSTRUCTIONS output
4. `test_github_failure_causes_exit_1` — mock `verify_github` returning `overall_ok=False`, assert `execute_verify()` returns 1

Mock targets:
- `mcp_coder.cli.commands.verify.verify_github`
- Plus all existing mocks from `TestMcpServersInVerify` pattern (verify_claude/resolve_llm_method/verify_mlflow/prompt_llm etc.)
