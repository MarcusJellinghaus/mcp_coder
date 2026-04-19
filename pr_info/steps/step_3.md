# Step 3: Copilot log paths

**Reference:** See `pr_info/steps/summary.md` for full context (Issue #847).

## LLM Prompt

> Implement Step 3 of the Copilot CLI provider (issue #847). See `pr_info/steps/summary.md` for full context.
>
> Create `src/mcp_coder/llm/providers/copilot/copilot_cli_log_paths.py` with log path generation for `logs/copilot-sessions/`. First, extract shared log utilities (`sanitize_branch_identifier`, `DEFAULT_LOGS_DIR`) from `claude_code_cli_log_paths.py` into a new `src/mcp_coder/llm/log_utils.py` module. Update `claude_code_cli_log_paths.py` to import from `..log_utils`. The copilot module then imports from `...log_utils`. Also create the package `__init__.py` (empty for now). Follow TDD.

## WHERE

### New files
- `src/mcp_coder/llm/log_utils.py`
- `src/mcp_coder/llm/providers/copilot/__init__.py`
- `src/mcp_coder/llm/providers/copilot/copilot_cli_log_paths.py`
- `tests/llm/test_log_utils.py`
- `tests/llm/providers/copilot/__init__.py`
- `tests/llm/providers/copilot/test_copilot_cli_log_paths.py`

### Modified files
- `src/mcp_coder/llm/providers/claude/claude_code_cli_log_paths.py` (import from `...log_utils` instead of defining locally)

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

Import shared utilities from the new `log_utils` module (two levels up from copilot package).

### `src/mcp_coder/llm/log_utils.py`
```python
"""Shared log utilities for LLM providers."""

DEFAULT_LOGS_DIR: str = "logs"

def sanitize_branch_identifier(branch_name: str) -> str:
    """Sanitize a git branch name for use in filenames."""
```
Extracted from `claude_code_cli_log_paths.py` — these are provider-agnostic utilities.

### `src/mcp_coder/llm/providers/copilot/__init__.py`
```python
# Copilot CLI provider module
```

## HOW

- **Sub-step 3a (extract shared utilities):** Extract `sanitize_branch_identifier` and `DEFAULT_LOGS_DIR` from `claude_code_cli_log_paths.py` into `src/mcp_coder/llm/log_utils.py`. Update `claude_code_cli_log_paths.py` to `from ...log_utils import sanitize_branch_identifier, DEFAULT_LOGS_DIR`. Keep both names in `claude_code_cli_log_paths.py`'s public API (i.e., import them and let them be re-exported) so that existing imports from other claude modules (e.g., `claude_code_cli.py` line 19) continue to work without changes. This minimizes the refactoring diff.
- **Sub-step 3b (copilot log paths):** Create `copilot_cli_log_paths.py` importing from `...log_utils` (three dots — up from `providers/copilot/` to `llm/`).

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

**Note on existing tests:** Existing tests for `sanitize_branch_identifier` in `tests/llm/providers/claude/test_claude_cli_stream_parsing.py` remain as-is — they test via the re-exported path which still works. The new `tests/llm/test_log_utils.py` tests the canonical location. No test removal needed.

## Tests

### `tests/llm/test_log_utils.py`
- `test_sanitize_branch_identifier_simple` — `"main"` → `"main"`
- `test_sanitize_branch_identifier_slashes` — `"feature/foo"` → `"feature_foo"`
- `test_sanitize_branch_identifier_special_chars` — strips/replaces non-alphanumeric
- `test_default_logs_dir_value` — `DEFAULT_LOGS_DIR == "logs"`

### `tests/llm/providers/copilot/test_copilot_cli_log_paths.py`

- `test_default_path_uses_copilot_sessions_subdir` — verify path contains `copilot-sessions/` (not `claude-sessions/`)
- `test_path_with_branch_name` — verify branch identifier appears in filename
- `test_path_without_branch_name` — verify filename has no trailing identifier
- `test_path_with_custom_logs_dir` — verify custom logs_dir is respected
- `test_directory_is_created` — verify `mkdir` is called (use `tmp_path`)
- `test_ndjson_extension` — verify file ends with `.ndjson`
