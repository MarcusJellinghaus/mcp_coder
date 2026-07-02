# Step 1 — Add `EventLog.logs_dir` property

> Read `pr_info/steps/summary.md` first for the overall goal, design rationale,
> and the KISS divergence from the issue's `AppCore` routing decision.

## Goal

Expose the logs directory on `EventLog` via a read-only `logs_dir` property so
the `/info` command (Step 2) can display it. The current-file path already
exists as `EventLog.current_path` and is **reused** — do **not** add a
`file_path` property.

## WHERE

- Source: `src/mcp_coder/icoder/core/event_log.py`
- Test:   `tests/icoder/test_event_log.py`

## WHAT

Add a property to the `EventLog` class, placed next to the existing
`current_path` / `current_chat_path` properties:

```python
@property
def logs_dir(self) -> Path:
    """Directory that holds this session's log files."""
    return self._logs_dir
```

`self._logs_dir: Path` is already set in `EventLog.__init__` — the property just
exposes it. No `__init__` change, no other code change.

## HOW (integration)

- Pure additive change. No imports needed (`Path` already imported).
- Nothing else in the module or codebase references `logs_dir` yet; Step 2 will
  consume it.

## ALGORITHM

None — one-line accessor returning the stored field.

## DATA

- Returns: `Path` — the directory passed to `EventLog(logs_dir=...)`
  (e.g. `<project_dir>/logs`), already normalized to a `Path` in `__init__`.

## TDD — test first

Add to `tests/icoder/test_event_log.py` (mirrors the existing
`test_current_path_matches_initial_file` style):

```python
def test_logs_dir_returns_directory(tmp_path: Path) -> None:
    with EventLog(logs_dir=tmp_path) as log:
        assert log.logs_dir == tmp_path
        # current log file lives inside logs_dir
        assert log.current_path.parent == log.logs_dir


def test_logs_dir_stable_after_close(tmp_path: Path) -> None:
    log = EventLog(logs_dir=tmp_path)
    log.close()
    assert log.logs_dir == tmp_path
    assert log.current_path.parent == tmp_path
```

## Definition of done (one commit)

1. Write the two tests above (they fail — no `logs_dir` yet).
2. Add the `logs_dir` property.
3. Run and pass all three MCP checks:
   - `mcp__tools-py__run_pylint_check`
   - `mcp__tools-py__run_pytest_check` with
     `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
   - `mcp__tools-py__run_mypy_check`
4. Run `./tools/format_all.sh`, then commit tests + implementation together.

## Commit message

```
Add EventLog.logs_dir property (#764)
```
