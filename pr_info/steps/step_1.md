# Step 1: Restructure pyproject.toml Optional Dependencies

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 1.

Task: Restructure the optional dependencies in pyproject.toml to separate type stubs from other dev dependencies.

Reference: pr_info/steps/step_1.md for detailed specifications.
```

## Overview

Split the monolithic `dev` optional dependency group into purpose-specific groups: `types`, `test`, `mcp`, and `dev` (which combines all).

## WHERE

| File | Action |
|------|--------|
| `pyproject.toml` | Modify `[project.optional-dependencies]` section |

## WHAT

### Current Structure (Before)
```toml
[project.optional-dependencies]
dev = [
    "pytest-asyncio",
    "pytest-xdist",
    "types-pyperclip",
    "types-requests>=2.28.0",
    "mcp-server-filesystem @ git+https://github.com/MarcusJellinghaus/mcp_server_filesystem.git",
]
```

### New Structure (After)
```toml
[project.optional-dependencies]
# Type stubs - required in PROJECT venv for mypy type resolution
types = [
    "types-pyperclip",
    "types-requests>=2.28.0",
]

# Test utilities - for local development (execution env already has pytest/mypy)
test = [
    "pytest-asyncio",
    "pytest-xdist",
]

# MCP servers - for local development (execution env already has these)
mcp = [
    "mcp-server-filesystem @ git+https://github.com/MarcusJellinghaus/mcp_server_filesystem.git",
]

# Full development setup - combines all groups for local development
dev = [
    "mcp-coder[types,test,mcp]",
]
```

## HOW

1. Replace the existing `[project.optional-dependencies]` section with the new structure
2. Preserve the exact package specifications (versions, git URLs)
3. Use self-referencing syntax `mcp-coder[types,test,mcp]` for the `dev` group

## DATA

### Dependency Groups

| Group | Purpose | Packages |
|-------|---------|----------|
| `types` | Type stubs for mypy in project venv | `types-pyperclip`, `types-requests>=2.28.0` |
| `test` | Test parallelization utilities | `pytest-asyncio`, `pytest-xdist` |
| `mcp` | MCP servers for local development | `mcp-server-filesystem` |
| `dev` | All dependencies for local development | Self-reference to all groups |

## Verification

1. **Syntax check**: Run `python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"` to verify TOML syntax
2. **Install check**: Run `pip install -e ".[dev]"` to verify all groups install correctly
3. **Individual group check**: Run `pip install -e ".[types]"` to verify types-only installation

## Notes

- The `dev` group uses PEP 508 self-referencing extras syntax
- Comments are added for clarity but are optional
- Order of groups doesn't matter for functionality but follows logical grouping
