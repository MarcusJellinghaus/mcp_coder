# Step 2 — Dead test code and unused GitHub fixtures

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> Delete the commented-out Claude API test code, and the unused GitHub fixtures with
> their imports and vulture whitelist entries. Don't change any live test logic.
> Run the checks and make one commit.

## Precondition

Search the project for `GitHubTestSetup|github_test_setup|create_github_manager`.
Hits are expected only in `tests/conftest.py` and `vulture_whitelist.py` (the `pr_info/` plan files may mention the names too; ignore those).
If any other file uses them: write one line to `pr_info/.blocked.txt` naming that file, and stop.

## WHERE / WHAT

### `tests/llm/providers/claude/test_claude_integration.py`
- In `TestCriticalPathIntegration`: delete the comment block from `# TODO: Commented out due to Claude Code SDK compatibility issues` through the last commented line of `test_session_continuity_api` (`#     assert result2["session_id"] == session_id`).
- Replace the module-level comment pair
  `# API-specific features like cost tracking are business features, not critical path`
  `# Basic API functionality is covered by the critical path tests above`
  with:
  `# CLI features beyond the critical path (e.g. cost tracking) are not integration-tested here`
  `# Basic CLI functionality is covered by the critical path tests above`
- In `test_env_vars_propagation`:
  - Delete everything from `# Test API method - env_vars should be passed to SDK` to the end of the file. The function then ends with the `# Successful execution means env_vars were prepared and passed correctly` comment after the CLI asserts.
  - Replace the docstring with:

```python
        """Verify env_vars propagate to Claude Code via the CLI method.

        This is a real integration test that makes actual API calls to verify
        environment variables are correctly set and accessible.

        The test verifies:
        1. CLI method: env_vars passed to subprocess work correctly
        2. The CLI can successfully execute with MCP servers using env vars
        """
```

### `tests/conftest.py`
- Delete the `GitHubTestSetup` class, the `github_test_setup` fixture (with its `@pytest.fixture` decorator), `T = TypeVar("T")` and `create_github_manager`. That's lines ~256–412, from `class GitHubTestSetup(TypedDict):` to the end of `create_github_manager`. Keep two blank lines before the following `@pytest.fixture` / `def require_claude_cli`.
- Delete the block:

```python
try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict
```

- Delete `from typing import Any, TypeVar, cast` (only the deleted code used it).
- Keep `import os` and `import git`, which other fixtures still use.

### `vulture_whitelist.py`
- Delete these three lines and one of the blank lines around them:

```
# conftest.py - Fixtures for GitHub integration test setup
_.github_test_setup
_.create_github_manager
```

## HOW / ALGORITHM / DATA

No new functions, imports or data structures. Deletions only.

## Checks, then commit

1. Run `mcp__mcp-tools-py__run_format_code`.
2. Run pylint, mypy (catches leftover use of `Any`/`cast`/`TypedDict`), and the unit tests with the CLAUDE.md command (`-n auto`).
3. Search `tests/` and `vulture_whitelist.py` for `claude_api_integration|github_test_setup|create_github_manager|claude_sdk_working`. Expect 0 hits.
4. Commit once, e.g. `test: remove dead Claude API test code and unused GitHub fixtures`.
