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

# mcp-coder session and log files
.mcp-coder/
logs/

# Scratch files for LLM sessions: MCP-writable via .mcp-file-access, never committed
.scratch/
```

- **`.vscodeclaude_*` — written automatically.** `mcp-coder init` appends any
  missing entries to `<project_dir>/.gitignore`; commit the result. A
  VSCodeClaude session launch re-appends them as a safety net, so an uncommitted
  block shows up as a dirty `.gitignore` in every session folder.
- **`.scratch/` — written by `mcp-coder init`** (not by the session launch),
  only once `.mcp-file-access` keeps it writable for MCP; see below.
- **`.mcp.*.json` — add manually.** No tool writes this line.
- **`.mcp-coder/` and `logs/` — add manually.** Required for the automated LLM
  rebase: review and fix-conflict hand off to a human instead of running it
  when `.mcp-coder/` is not ignored.

The automated LLM rebase runs pytest in the mcp-coder tool environment
(`sys.executable`), so the repo's test dependencies must be installed there.

## MCP file access rules (`.mcp-file-access`)

mcp-workspace reads `.mcp-file-access` at the project root (one
`<level> <gitignore pattern>` per line, last match wins) and lets its rules
override `.gitignore` for the MCP file tools. `mcp-coder init` creates it, or
appends the template rules it lacks:

```text
read-only   /.vscodeclaude_status.txt
read-only   /.mcp.json
read-only   /.claude/settings.json
read-only   /.claude/settings.local.json
read-write  /.scratch/
```

- **Commit it**, together with the `.gitignore` change. MCP tools can't edit
  it (always read-only for them); edit it by hand.
- `read-write /.scratch/` keeps the gitignored `.scratch/` usable for scratch
  probes, issue body files and Jenkins logs.
- No `.mcp.linux.json` / `.mcp.macos.json` rules: they are gitignored, and a
  `read-only` rule would expose them to MCP reads.
- Needs mcp-workspace with `.mcp-file-access` support in every environment
  that runs the MCP server; an older server hides a gitignored `.scratch/`.
