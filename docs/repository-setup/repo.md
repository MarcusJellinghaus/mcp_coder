# Repo Conventions

Generic, language-agnostic repo-level files and conventions.

## Line Endings (`.gitattributes`)

- **Why:** Prevents git conflicts and ensures consistent file formats
- **Reference:** See `.gitattributes` in this repository

## File Size Management

> **Customize (`.large-files-allowlist`):** List files exempt from size limits.

**Principle:** Keep files within LLM context limits for optimal reasoning.

**Why critical:**
- Large files consume LLM context budget
- Smaller files enable more focused analysis
- Better context utilization for reasoning

**Tool: mcp-coder file size check**
```bash
mcp-coder check file-size --max-lines 750
```
- **Example config:** See `.large-files-allowlist` in this repository

## `.gitignore` Entries

Files that MCP Coder workflows expect to be gitignored:

```gitignore
# MCP configuration files (may contain sensitive paths)
.mcp.*.json

# VSCodeClaude session files (auto-generated)
.vscodeclaude_status.txt
.vscodeclaude_analysis.json
.vscodeclaude_session.json
.vscodeclaude_start.bat
.vscodeclaude_start.sh
```

- **`.vscodeclaude_*` — written automatically.** `mcp-coder init` appends any
  missing entries to `<project_dir>/.gitignore`; commit the result. A
  VSCodeClaude session launch re-appends them as a safety net, so an uncommitted
  block shows up as a dirty `.gitignore` in every session folder.
- **`.mcp.*.json` — add manually.** No tool writes this line.
