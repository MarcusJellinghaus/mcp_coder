# Step 4: Create Slash Command Files

## Reference
- **Summary**: `pr_info/steps/summary.md`
- **Step 3**: `pr_info/steps/step_3.md` (CLI must be registered)

## LLM Prompt
```
Implement Step 4 from pr_info/steps/summary.md:
Create the three slash command markdown files in `.claude/commands/`.
Follow the pattern from `.claude/commands/issue_approve.md`.
```

## WHERE
- **Files to create**:
  1. `.claude/commands/plan_approve.md`
  2. `.claude/commands/implementation_approve.md`
  3. `.claude/commands/implementation_needs_rework.md`

## WHAT - File Contents

### File 1: `.claude/commands/plan_approve.md`

```markdown
---
allowed-tools: Bash(mcp-coder set-status:*)
---

# Approve Implementation Plan

Approve the implementation plan and transition the issue to implementation-ready state.

**Instructions:**
1. Run the set-status command to update the issue label:
```bash
mcp-coder set-status status-05:plan-ready
```

2. Confirm the status change was successful.

**Effect:** Changes issue status from `status-04:plan-review` to `status-05:plan-ready`.
```

### File 2: `.claude/commands/implementation_approve.md`

```markdown
---
allowed-tools: Bash(mcp-coder set-status:*)
---

# Approve Implementation

Approve the implementation and transition the issue to PR-ready state.

**Instructions:**
1. Run the set-status command to update the issue label:
```bash
mcp-coder set-status status-08:ready-pr
```

2. Confirm the status change was successful.

**Effect:** Changes issue status from `status-07:code-review` to `status-08:ready-pr`.
```

### File 3: `.claude/commands/implementation_needs_rework.md`

```markdown
---
allowed-tools: Bash(mcp-coder set-status:*)
---

# Implementation Needs Rework

After code review identifies issues requiring additional implementation work, transition the issue back to plan-ready state.

**Instructions:**
1. Run the set-status command to update the issue label:
```bash
mcp-coder set-status status-05:plan-ready
```

2. Confirm the status change was successful.

**Effect:** Changes issue status from `status-07:code-review` back to `status-05:plan-ready` for rework.
```

## HOW - File Structure

Each slash command file follows the pattern:
1. YAML frontmatter with `allowed-tools`
2. Title as H1
3. Brief description
4. Instructions section with bash command
5. Effect description

## ALGORITHM - No code logic

These are static markdown files that instruct Claude Code to run bash commands.

## DATA - Tool Permissions

The `allowed-tools` frontmatter grants permission for:
- `Bash(mcp-coder set-status:*)` - allows running any `mcp-coder set-status` command

## Verification

After creating files, verify slash commands appear in Claude Code:
```
/plan_approve
/implementation_approve  
/implementation_needs_rework
```

## Notes

- These commands do NOT replace `/issue_approve` which uses GitHub Actions via `/approve` comment
- Users can still manually run `mcp-coder set-status <label>` if needed
- The slash commands provide convenient shortcuts for common workflow transitions
