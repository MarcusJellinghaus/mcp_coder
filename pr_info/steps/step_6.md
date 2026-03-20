# Step 6: API Parity — Export Missing Python APIs

> **Summary**: [pr_info/steps/summary.md](summary.md)
> **Covers**: Sub-task 7 (API parity exports)
> **Depends on**: Steps 2, 5

## LLM Prompt

```
Implement Step 6 of issue #528: Export missing Python APIs for programmatic use.

Read pr_info/steps/summary.md for full context, then read this step file for details.

Add public exports:
1. verify_claude, verify_langchain, verify_mlflow — from existing functions
2. commit_auto() — wrap execute_commit_auto for programmatic use (or export generate_commit_message_with_llm from top-level)
3. collect_branch_status — from checks package

Update tests first (TDD), then the implementation. Run all three code quality checks after.
```

## WHERE

- **Source**: `src/mcp_coder/__init__.py`
- **Source**: `src/mcp_coder/checks/__init__.py`
- **Tests**: `tests/test_module_exports.py`

## WHAT

### New exports in `src/mcp_coder/__init__.py`

```python
# Verification functions
from .llm.providers.claude.claude_cli_verification import verify_claude
from .llm.providers.langchain.verification import verify_langchain
from .llm.mlflow_logger import verify_mlflow

# Commit operations
from .workflow_utils.commit_operations import generate_commit_message_with_llm

# Branch status
from .checks.branch_status import collect_branch_status
```

Add to `__all__`:
```python
"verify_claude",
"verify_langchain", 
"verify_mlflow",
"generate_commit_message_with_llm",
"collect_branch_status",
```

### New export in `src/mcp_coder/checks/__init__.py`

```python
from .branch_status import collect_branch_status
```

Add `"collect_branch_status"` to `__all__`.

## HOW

Pure import additions — no new functions needed. The functions already exist, they just aren't exported from the top-level package.

**Note on `commit_auto`**: The issue says "Export full `commit_auto()` workflow". The existing `execute_commit_auto()` in `commit.py` is CLI-coupled (reads `argparse.Namespace`, prints to stdout, calls `sys.exit`). Rather than wrapping it, export `generate_commit_message_with_llm()` which is the programmatic API. This is simpler and already exists.

## ALGORITHM

No logic. Import additions only.

## DATA

No new data structures. Existing function signatures:

```python
# Already exists:
def verify_claude() -> dict[str, Any]: ...
def verify_langchain(check_models: bool = False, mcp_config_path: str | None = None, env_vars: dict[str, str] | None = None) -> dict[str, Any]: ...
def verify_mlflow() -> dict[str, Any]: ...
def generate_commit_message_with_llm(project_dir: Path, provider: str = "claude", execution_dir: str | None = None) -> tuple[bool, str, str | None]: ...
def collect_branch_status(project_dir: Path, max_log_lines: int = 300) -> BranchStatusReport: ...
```

## Test Cases

### `tests/test_module_exports.py`

1. `test_verify_claude_exported` — `from mcp_coder import verify_claude` succeeds
2. `test_verify_langchain_exported` — `from mcp_coder import verify_langchain` succeeds
3. `test_verify_mlflow_exported` — `from mcp_coder import verify_mlflow` succeeds
4. `test_generate_commit_message_exported` — `from mcp_coder import generate_commit_message_with_llm` succeeds
5. `test_collect_branch_status_exported` — `from mcp_coder import collect_branch_status` succeeds
6. `test_collect_branch_status_in_checks` — `from mcp_coder.checks import collect_branch_status` succeeds
