# Summary — #1007 commit: make `mcp-coder commit` the commit command, push by default

## Goal

- `mcp-coder commit` is the commit command; `commit auto` is removed (no alias).
- Push is on by default; `--no-push` opts out.
- Commits are refused (exit 1, before the LLM call and before `--preview`) on a
  protected branch (`main`, `master`, detected default) or when the current
  branch cannot be determined (detached HEAD / unreadable HEAD). This applies
  with push on or off.
- Docs updated to match.

## Architectural / design changes

| Area | Before | After |
|---|---|---|
| CLI shape | `commit` is a subparser group with one mode `auto` | `commit` is a leaf parser; flags live directly on it |
| Dispatch (`main.py`) | `commit` + `commit_mode` → `_handle_commit_command` (placeholder branch prints "not yet implemented") | `commit` → `execute_commit_auto` directly; handler and `commit_mode` fallback in `_command_name` removed |
| Catalog | key `"commit auto"` | key `"commit"` (description unchanged) |
| Push default | `--push` store_true, default off | `argparse.BooleanOptionalAction`, default on (`--push` / `--no-push`) |
| Branch policy | Only the push guard checks the branch; protected = detected default, or `main`/`master` if detection fails | Shared helper `_branch_refusal` in `cli/commands/commit.py`; protected = `{"main", "master"}` ∪ {detected default}; used as a pre-commit check (exit 1) and in the push guard (exit 2) |

### The shared helper (KISS)

```python
def _branch_refusal(project_dir: Path) -> tuple[bool, str] | None:
    """None if allowed; (False, "") if branch unknown; (True, name) if protected."""
```

- Reads the current branch first; if `None`, refuses without calling
  `get_default_branch_name`.
- No new class/dataclass — a plain optional tuple. Each caller formats its own
  message.
- `_push_after_commit` calls the helper once and picks its message from the
  tuple: "Cannot push: not on a branch" or "Refusing to push to protected
  branch '<name>'" (both existing messages kept). It then reads the branch name
  for the push itself.

### Order of operations in `execute_commit_auto`

1. resolve project dir → 2. `validate_git_repository` (exit 1) →
3. **`_branch_refusal` (exit 1, new)** → 4. LLM message (exit 2) →
5. `--preview` prompt (cancel → exit 0) → 6. commit (exit 2) →
7. push if `getattr(args, "push", False)` (exit 2 on failure/refusal).

`getattr(args, "push", False)` is deliberately kept: tests build
`argparse.Namespace` without `push`; the parser default supplies "on".

### Unchanged on purpose

- Function name `execute_commit_auto`.
- Workflow-internal commits (`workflow_steps/commit.py`,
  `workflows/implement/finalisation.py`) — they do not go through the CLI path.
- Historical docs: `docs/tests/runtime_statistics.md`, `docs/tests/performance_data/*`.

## Files modified (no new files or folders)

### Source
- `src/mcp_coder/cli/commands/commit.py` — helper, pre-check, push guard, docstrings/log text (step 1)
- `src/mcp_coder/workflow_utils/commit_operations.py` — "before running commit auto" → "before running commit" (step 1)
- `src/mcp_coder/cli/parsers.py` — `add_commit_parsers` becomes a leaf parser (step 2)
- `src/mcp_coder/cli/main.py` — dispatch, remove `_handle_commit_command`, `_command_name` cleanup (step 2)
- `src/mcp_coder/cli/command_catalog.py` — key rename (step 2)

### Tests
- `tests/cli/commands/test_commit_push.py` — autouse branch fixture, refusal tests, push-guard `master`/`main` case (step 1)
- `tests/cli/commands/test_commit.py` — autouse branch fixture, error string (step 1); parser test argv/renames (step 2)
- `tests/cli/test_parsers.py`, `tests/cli/test_main.py`, `tests/cli/test_shared_args.py`,
  `tests/cli/test_help_anti_drift.py`, `tests/cli/commands/test_help.py`,
  `tests/integration/test_mcp_config_integration.py` (step 2)

### Docs
- `docs/cli-reference.md` (step 2)

## Steps

1. [step_1.md](./step_1.md) — Branch guard (pre-commit refusal + wider push guard). CLI shape unchanged, push still off by default.
2. [step_2.md](./step_2.md) — CLI reshape: `commit` leaf parser, push on by default, test renames, docs.

The guard lands first so push is never on by default without it.
