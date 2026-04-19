# Step 3: Copilot log paths

**Reference:** See `pr_info/steps/summary.md` for full context (Issue #847).

## LLM Prompt

> Implement Step 3 of the Copilot CLI provider (issue #847). See `pr_info/steps/summary.md` for full context.
>
> Create `src/mcp_coder/llm/providers/copilot/copilot_cli_log_paths.py` with log path generation for `logs/copilot-sessions/`. Mirror the pattern from `claude_code_cli_log_paths.py` but with `copilot-sessions` subdirectory. Also create the package `__init__.py` (empty for now). Follow TDD.

## WHERE

### New files
- `src/mcp_coder/llm/providers/copilot/__init__.py`
- `src/mcp_coder/llm/providers/copilot/copilot_cli_log_paths.py`
- `tests/llm/providers/copilot/__init__.py`
- `tests/llm/providers/copilot/test_copilot_cli_log_paths.py`

## WHAT

### `src/mcp_coder/llm/providers/copilot/copilot_cli_log_paths.py`
```python
COPILOT_SESSIONS_SUBDIR: str = "copilot-sessions"

def get_stream_log_path(
    logs_dir: str | None = None,
    cwd: str | None = None,
    branch_name: str | None = None,
) -> Path:
    """Generate unique path for Copilot JSONL log file.

    Same pattern as Claude's log paths but in copilot-sessions/ subdirectory.
    Filename: session_YYYYMMDD_HHMMSS_NNNNNN[_BRANCH].ndjson
    """
```

Reuse `sanitize_branch_identifier` from Claude's log paths module (import it — it's a pure string utility, not Claude-specific).

### `src/mcp_coder/llm/providers/copilot/__init__.py`
```python
# Copilot CLI provider module
```

## HOW

- Import `sanitize_branch_identifier` from `..claude.claude_code_cli_log_paths` to avoid duplication.
- Import `DEFAULT_LOGS_DIR` from the same module (it's a generic constant `"logs"`).

## ALGORITHM

```
1. Determine base_dir from logs_dir, cwd, or Path.cwd()
2. Create session_dir = base_dir / COPILOT_SESSIONS_SUBDIR
3. session_dir.mkdir(parents=True, exist_ok=True)
4. Generate timestamp filename with optional branch identifier
5. Return session_dir / filename
```

## DATA

- Input: `logs_dir`, `cwd`, `branch_name` (all optional strings)
- Output: `Path` to `logs/copilot-sessions/session_YYYYMMDD_HHMMSS_NNNNNN[_BRANCH].ndjson`

## Tests

### `tests/llm/providers/copilot/test_copilot_cli_log_paths.py`

- `test_default_path_uses_copilot_sessions_subdir` — verify path contains `copilot-sessions/` (not `claude-sessions/`)
- `test_path_with_branch_name` — verify branch identifier appears in filename
- `test_path_without_branch_name` — verify filename has no trailing identifier
- `test_path_with_custom_logs_dir` — verify custom logs_dir is respected
- `test_directory_is_created` — verify `mkdir` is called (use `tmp_path`)
- `test_ndjson_extension` — verify file ends with `.ndjson`
