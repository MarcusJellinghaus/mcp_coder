# Step 3: Update Slash Command Documentation

## LLM Prompt
```
Implement Step 3 from pr_info/steps/summary.md: Update the three slash command files with error handling notes.

Reference: pr_info/steps/step_3.md for detailed specifications.
```

## Overview
Add error handling instructions to three slash command files that use `set-status`. This ensures users know how to handle failures and when to use `--force`.

## WHERE: File Paths
- **Modify**: `.claude/commands/plan_approve.md`
- **Modify**: `.claude/commands/implementation_needs_rework.md`
- **Modify**: `.claude/commands/implementation_approve.md`

## WHAT: Text to Add

Add the following note to each file's **Instructions** section:

```markdown
**Note:** If the command fails, report the error to the user. Do not use `--force` unless explicitly asked.
```

## HOW: Placement

Insert the note directly before the **Effect** section (no blank line, per Decision 4).

### Example Structure (after change):
```markdown
**Instructions:**
1. Run the set-status command to update the issue label:
```bash
mcp-coder set-status status-XX:label-name
```

2. Confirm the status change was successful.
**Note:** If the command fails, report the error to the user. Do not use `--force` unless explicitly asked.

**Effect:** Changes issue status from ...
```

## ALGORITHM: N/A
No algorithmic logic - this is documentation-only change.

## DATA: N/A
No data structures involved.

## Changes Per File

### .claude/commands/plan_approve.md
Insert directly before `**Effect:**` line (no blank line):
```markdown
**Note:** If the command fails, report the error to the user. Do not use `--force` unless explicitly asked.
```

### .claude/commands/implementation_needs_rework.md
Insert directly before `**Effect:**` line (no blank line):
```markdown
**Note:** If the command fails, report the error to the user. Do not use `--force` unless explicitly asked.
```

### .claude/commands/implementation_approve.md
Insert directly before `**Effect:**` line (no blank line):
```markdown
**Note:** If the command fails, report the error to the user. Do not use `--force` unless explicitly asked.
```

## Notes
- Keep formatting consistent with existing file style (per Decision 4)
- The note uses backticks around `--force` for code formatting
- No blank line before the note - match existing compact style
