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

Files that MCP Coder workflows expect to be gitignored. Add the following block to your project's `.gitignore`:

```gitignore
# MCP configuration files (may contain sensitive paths)
.mcp.*.json

# VSCodeClaude session status (prevents working folders from appearing "dirty")
.vscodeclaude_status.txt
```
