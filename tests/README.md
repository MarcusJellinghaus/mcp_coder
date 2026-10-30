# Testing Guide

Tests mirror the structure of `src/mcp_coder/`.

- **Markers** (which tests need git, the Claude CLI, Jenkins and so on) are defined in `[tool.pytest.ini_options]` in `pyproject.toml`. Tests without a marker are fast unit tests.
- **Fast-suite command** and parallel-run rules: [`.claude/CLAUDE.md`](../.claude/CLAUDE.md).
- **Slow or flaky tests:** [Slow Test Review](../docs/tests/slow-test-review-methodology.md).
