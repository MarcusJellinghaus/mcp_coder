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
