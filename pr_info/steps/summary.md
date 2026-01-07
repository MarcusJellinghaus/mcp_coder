# Issue #250: Coordinator Command - Enhance Dependency Management and Documentation

## Summary

This implementation enhances the CLI coordinator command's dependency management for Jenkins-based workflows. The core problem is that mypy (via MCP code-checker) requires type stubs in the **project's virtual environment** for proper type resolution, but Windows templates are missing this setup step entirely, and Linux templates install unnecessary dependencies.

## Architectural / Design Changes

### Two-Environment Model (Existing Architecture - Now Documented)

```
┌─────────────────────────────────────────────────────────────┐
│  Execution Environment (VENV_BASE_DIR/.venv)                │
│  Pre-provisioned: mcp-coder, mcp-code-checker,              │
│  mcp-server-filesystem, claude CLI, uv                      │
│  + transitive: pytest, mypy, pylint, black, isort           │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ 1. uv sync --extra types (in project dir)
                           │ 2. mcp-coder implement
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Project Environment (repo/.venv)                           │
│  Created per-run: project dependencies + type stubs         │
│  (types-requests, types-pyperclip, etc.)                    │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Restructuring

**Before** (single `dev` group with mixed concerns):
```toml
[project.optional-dependencies]
dev = [
    "pytest-asyncio",           # Test framework
    "pytest-xdist",             # Test parallelization
    "types-pyperclip",          # Type stub
    "types-requests>=2.28.0",   # Type stub
    "mcp-server-filesystem",    # MCP server
]
```

**After** (separated by purpose):
```toml
[project.optional-dependencies]
types = ["types-pyperclip", "types-requests>=2.28.0"]
test = ["pytest-asyncio", "pytest-xdist"]
mcp = ["mcp-server-filesystem @ ..."]
dev = ["mcp-coder[types,test,mcp]"]  # Combines all
```

### Command Template Changes

- **Windows templates**: Add `uv sync --extra types` step (currently missing)
- **Linux templates**: Change `uv sync --extra dev` → `uv sync --extra types` (install only what's needed)

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `pyproject.toml` | Modify | Restructure `[project.optional-dependencies]` into `types`, `test`, `mcp`, `dev` groups |
| `src/mcp_coder/cli/commands/coordinator/command_templates.py` | Modify | Update 8 templates (4 Windows + 4 Linux) |
| `docs/configuration/CONFIG.md` | Modify | Add "Dependency Architecture" section |

## Implementation Steps

1. **Step 1**: Restructure `pyproject.toml` optional dependencies
2. **Step 2**: Update command templates in `command_templates.py`
3. **Step 3**: Add documentation to `docs/configuration/CONFIG.md`

## Acceptance Criteria

- [ ] Optional dependencies restructured into `types`, `test`, `mcp`, and `dev` groups
- [ ] Windows command templates include `uv sync --extra types` step
- [ ] Linux command templates use `uv sync --extra types` (instead of `--extra dev`)
- [ ] Documentation added explaining two-environment architecture
- [ ] CI workflow continues to work (uses `.[dev]` which includes all groups)

## Backward Compatibility

- `pip install .[dev]` continues to work (installs all groups via self-reference)
- CI workflow (`.github/workflows/ci.yml`) requires no changes
- Local development with `pip install -e ".[dev]"` unchanged

## Test Strategy

- **Step 1**: Verify `pyproject.toml` syntax with `uv pip compile` or similar
- **Step 2**: Unit tests for template content verification (templates contain expected strings)
- **Step 3**: Documentation review (no automated tests)
