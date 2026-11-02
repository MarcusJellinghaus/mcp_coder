# Step 4 — Least-privilege settings file shared by CLI and automated callers

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md` only.
> Write/adjust the tests first, then the implementation. Run pylint, pytest (fast
> unit set, `-n auto`), mypy and lint-imports until they pass, run
> `run_format_code`, and make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/rebase_permissions.py`
- `src/mcp_coder/cli/commands/rebase.py`
- Tests: `tests/workflows/rebase/test_rebase_permissions.py`, `tests/cli/commands/test_rebase.py`

## WHAT

```python
@contextmanager
def rebase_settings_file(override: str | None = None) -> Iterator[str]:
    """Yield the settings path for the rebase LLM session.

    ``override`` (an already-resolved path) is yielded unchanged. Otherwise
    ``REBASE_LLM_PERMISSIONS`` is written to a temp JSON file that exists for the
    whole ``with`` block and is deleted afterwards.
    """
```

## HOW

- Remove `"mcp__mcp-workspace__move_file"` from `REBASE_LLM_PERMISSIONS`; update the
  module docstring (drop the "CLI materializes" sentence, mention the context manager).
- CLI: keep explicit `--settings` resolution via `resolve_claude_settings_path` in the
  CLI (that resolver lives in `cli/utils`). Replace `_resolve_rebase_settings`' temp-file
  branch with:
  `with rebase_settings_file(explicit_or_none) as settings_file: return run_rebase_workflow(...).exit_code`

## ALGORITHM

```
if override is not None: yield override; return
write REBASE_LLM_PERMISSIONS to NamedTemporaryFile(suffix=".json", delete=False)
try: yield path
finally: Path(path).unlink(missing_ok=True)
```

## DATA

Yields `str` (absolute path).

## Tests

- `move_file` not in `REBASE_LLM_PERMISSIONS["permissions"]["allow"]`.
- Inside the block the temp file exists and parses to `REBASE_LLM_PERMISSIONS`;
  after the block it is gone (also when the body raises).
- Override is yielded unchanged and not deleted.
- CLI: without `--settings` the workflow receives a temp path that no longer exists
  after the call; with `--settings` the resolved path is passed through.
