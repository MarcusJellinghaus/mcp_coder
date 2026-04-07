# Repo Conventions

Repo-level files and conventions: line endings, `pyproject.toml`, and centralized `.gitignore` entries.

## Line Endings (`.gitattributes`)

- **Why:** Prevents git conflicts and ensures consistent file formats
- **Reference:** See `.gitattributes` in this repository

## `pyproject.toml`

**Principle:** Include architecture tools in development dependencies.

**Reference:** See `pyproject.toml` in this repository for complete dependency setup including version constraints and optional dependency groups.

## `.gitignore` Entries

Files that MCP Coder workflows expect to be gitignored. Add the following block to your project's `.gitignore`:

```gitignore
# MCP configuration files (may contain sensitive paths)
.mcp.*.json

# VSCodeClaude session status (prevents working folders from appearing "dirty")
.vscodeclaude_status.txt
```
