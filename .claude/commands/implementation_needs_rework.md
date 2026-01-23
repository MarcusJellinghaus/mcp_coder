---
allowed-tools: Bash(mcp-coder set-status:*)
workflow-stage: code-review
suggested-next: (bot runs implement) -> /clear -> implementation_review
---

# Implementation Needs Rework

Set status to plan-ready after creating new steps (and pushing them) from code review findings.

**Typical workflow:**
1. `/implementation_review` - identifies issues
2. `/discuss` - discuss and decide on changes  
3. `/implementation_new_tasks` - create additional implementation steps
4. `/commit_push` - commit the updated plan
5. **This command** - transition to plan-ready
6. `mcp-coder implement` - process the new steps

**Instructions:**
1. Run the set-status command to update the issue label:
```bash
mcp-coder set-status status-05:plan-ready
```

2. Confirm the status change was successful.
**Note:** If the command fails, report the error to the user. Do not use `--force` unless explicitly asked.

**Effect:** Changes issue status from `status-07:code-review` to `status-05:plan-ready` for rework.
