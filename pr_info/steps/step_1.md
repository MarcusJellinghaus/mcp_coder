# Step 1 — Extract `verify_exit_code.py`

> Read [`summary.md`](./summary.md) first. This step is one commit / one PR.
> Pure **move** refactor — no logic changes, imports only.

## Goal

Move the two exit-code helpers out of `verify.py` into a new pure leaf module.
`verify.py` stays ~1015 lines → **remains on `.large-files-allowlist`** (do not touch
the allowlist in this step).

## WHERE

- **New:** `src/mcp_coder/cli/commands/verify_exit_code.py`
- **Modified:** `src/mcp_coder/cli/commands/verify.py`
- **Auto-modified importers** (`move_symbol` rewrites these):
  - `tests/cli/commands/test_verify_exit_codes.py`
  - `tests/cli/commands/test_verify_exit_codes_git.py`
  - `tests/cli/commands/test_verify_exit_codes_github.py`
  - `tests/cli/commands/test_verify_install_hints.py`

## WHAT (symbols to move — verbatim)

```python
def _compute_exit_code(
    active_provider: str,
    claude_result: dict[str, Any],
    langchain_result: dict[str, Any] | None,
    mlflow_result: dict[str, Any],
    test_prompt_ok: bool = True,
    mcp_result: dict[str, Any] | None = None,
    config_has_error: bool = False,
    claude_mcp_ok: bool | None = None,
    github_result: dict[str, Any] | None = None,
    git_result: dict[str, Any] | None = None,
    tools_exposed_ok: bool | None = None,
    mcp_config_ok: bool | None = None,
) -> int: ...

def _collect_install_hints(result: dict[str, Any]) -> list[str]: ...
```

## HOW (integration)

- New module needs only `from typing import Any` (both functions use `dict[str, Any]`
  / `list[str]`). It imports **nothing** from `verify.py` — pure leaf.
- After the move, `verify.py`'s `execute_verify` still calls both functions, so
  `move_symbol` adds this line to `verify.py`:
  ```python
  from .verify_exit_code import _collect_install_hints, _compute_exit_code
  ```
- No `.importlinter` / `tach.toml` change (leaf, one-directional, no cycle).

## ALGORITHM (execution)

```
1. list_symbols("src/mcp_coder/cli/commands/verify.py")   # confirm targets
2. move_symbol(verify.py, ["_compute_exit_code", "_collect_install_hints"],
               verify_exit_code.py, dry_run=True)          # preview
3. review preview: only these 2 fns move; importers repoint; verify.py gains back-import
4. move_symbol(... dry_run=False)                          # execute
5. run all checks (see summary) + git-tool compact-diff
```

## DATA (unchanged contracts)

- `_compute_exit_code(...) -> int` — 0 = all pass, 1 = any critical failure.
- `_collect_install_hints(result) -> list[str]` — install-hint strings from failed
  entries.

## Test phase (TDD-equivalent)

No new test is written (behavior unchanged). The existing tests in the four importer
files already cover these functions; `move_symbol` repoints their imports. Confirm the
suite stays green.

## Done when

- [ ] `verify_exit_code.py` created with the two functions + `from typing import Any`.
- [ ] `verify.py` imports them back; no other change to `verify.py`.
- [ ] All four importer test files reference `verify_exit_code`.
- [ ] `compact-diff` shows only import / new-file churn.
- [ ] format + lint-imports + pytest + pylint + mypy pass; `tach check` passes.
- [ ] `verify.py` stays on `.large-files-allowlist` (unchanged this step).
