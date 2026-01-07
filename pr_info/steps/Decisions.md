# Decisions - Issue #250

This document records decisions made during plan review for the Coordinator Command Dependency Management enhancement.

## Decision 1: All templates use `--extra types`

**Context:** The test command templates (`DEFAULT_TEST_COMMAND` and `DEFAULT_TEST_COMMAND_WINDOWS`) currently use `--extra dev`. The question was whether they should stay with `--extra dev` since they verify the complete environment setup.

**Decision:** All 8 templates (including test commands) should use `--extra types` consistently.

**Rationale:** Consistency across all templates. The test commands verify environment setup, but type stubs are the only dependency group needed in the project environment for mypy to work correctly.

## Decision 2: Use `--project` flag for Windows templates

**Context:** The original plan proposed changing directories (`cd %WORKSPACE%\repo`, `uv sync`, `cd %VENV_BASE_DIR%`) to install type stubs in the project environment.

**Decision:** Use `uv sync --project %WORKSPACE%\repo --extra types` instead of directory changes.

**Rationale:** 
- Cleaner and simpler approach
- Avoids directory-changing dance
- Single line instead of multiple commands
- `--project` flag tells uv which project to sync without needing to `cd` there
