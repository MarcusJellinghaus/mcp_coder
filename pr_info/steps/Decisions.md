# Implementation Plan Decisions

## Decisions from Plan Review Discussion (2026-02-05)

### 1. MCP Tool Commands in Step 3
**Decision**: Update step_3.md to use MCP tool syntax instead of raw pytest bash commands.
**Rationale**: Aligns with CLAUDE.md requirements that mandate MCP tools for all file operations and code checks.
**Chosen Option**: A - Update all test commands to use MCP tools

### 2. Code Quality Checks in Step 3
**Decision**: Do not add explicit pylint/mypy reminders in step_3.md.
**Rationale**: CLAUDE.md is always loaded and mandates these checks after ANY code changes. Avoid redundancy.
**Chosen Option**: C - Keep as-is, assume implementer knows CLAUDE.md requirements

### 3. Format Before Commit Reminder
**Decision**: Do not add explicit format_all reminder in step_3.md.
**Rationale**: CLAUDE.md already mandates running `./tools/format_all.sh` before commits. Keep plan DRY.
**Chosen Option**: B - Keep as-is

### 4. Existing Workspaces Documentation
**Decision**: Do not document upgrade instructions for existing workspaces.
**Rationale**: Workspaces are typically temporary. Users can recreate if needed.
**Chosen Option**: C - Not needed

### 5. Documentation Update
**Decision**: Add concise note to `docs/coordinator-vscodeclaude.md` about dev dependencies.
**Rationale**: Complete documentation without excessive detail.
**Chosen Option**: A - Add brief mention, be concise
**Action**: Add this as a task in the implementation steps
