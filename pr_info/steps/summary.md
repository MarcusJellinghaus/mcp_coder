# File Size Checker CLI Command - Implementation Summary

## Issue Reference
**Issue #75**: File size checker CLI command

## Overview
Add a CLI command `mcp-coder check file-size` that enforces maximum file line counts with allowlist support for CI integration.

## Architectural Changes

### New Package Structure
```
src/mcp_coder/
├── checks/                          # NEW package for code quality checks
│   ├── __init__.py
│   └── file_sizes.py                # Core file size checking logic
├── mcp_server_filesystem.py         # NEW thin wrapper for mcp-server-filesystem
└── cli/commands/
    └── check_file_sizes.py          # NEW CLI command handler

tests/
└── checks/                          # NEW test package
    ├── __init__.py
    └── test_file_sizes.py           # Tests for file size checking
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| New `checks/` package | Forward-thinking for future check commands (issue #350) |
| Thin wrapper in `mcp_server_filesystem.py` | Isolates external dependency, follows project patterns |
| Subcommand structure (`check file-size`) | Extensible for more check types |
| OS-native path normalization | Matches what users see in terminal |
| UTF-8 only encoding | Simple, covers 99% of code files |

### Data Structures

```python
@dataclass
class FileMetrics:
    path: Path
    line_count: int

@dataclass  
class CheckResult:
    passed: bool
    violations: list[FileMetrics]
    total_files_checked: int
    allowlisted_count: int
    stale_entries: list[str]
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `pyproject.toml` | MODIFY | Move mcp-server-filesystem to main dependencies |
| `src/mcp_coder/mcp_server_filesystem.py` | CREATE | Wrapper for list_files function |
| `src/mcp_coder/checks/__init__.py` | CREATE | Package init with exports |
| `src/mcp_coder/checks/file_sizes.py` | CREATE | Core checking logic |
| `src/mcp_coder/cli/commands/check_file_sizes.py` | CREATE | CLI handler |
| `src/mcp_coder/cli/main.py` | MODIFY | Add check command group |
| `tests/checks/__init__.py` | CREATE | Test package init |
| `tests/checks/test_file_sizes.py` | CREATE | Unit and integration tests |

## CLI Interface

```bash
mcp-coder check file-size [OPTIONS]

Options:
  --max-lines INTEGER       Maximum lines per file (default: 600)
  --allowlist-file PATH     Path to allowlist file (default: .large-files-allowlist)
  --generate-allowlist      Output violating paths for piping to allowlist
```

**Exit codes:** `0` = pass, `1` = violations found

## Implementation Steps

1. **Step 1**: Update dependencies and create mcp_server_filesystem wrapper
2. **Step 2**: Create checks package with core file_sizes.py logic (TDD)
3. **Step 3**: Create CLI command handler and integrate into main.py

## Testing Strategy

All tests use pytest `tmp_path` fixture. No special markers needed.

| Function | Test Approach |
|----------|---------------|
| `count_lines()` | Unit test with temp file |
| `load_allowlist()` | Unit test with temp file (comments, blanks, paths) |
| `get_file_metrics()` | Unit test with temp files |
| `check_file_sizes()` | Integration test with temp directory |
| `render_output()` | Pure string unit test |
| `render_allowlist()` | Pure string unit test |
