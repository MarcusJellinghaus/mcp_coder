---
allowed-tools: Bash(mcp-coder set-status:*)
workflow-stage: code-review
suggested-next: (bot runs implement) -> /clear -> implementation_review
---

# Implementation Needs Rework

Transition issue back to `plan-ready` for re-implementation after code review found major issues.

## When to Use

| Situation | Action |
|-----------|--------|
| Minor fixes | Fix directly, re-run `/implementation_review` |
| **Major issues** | **This command** (after `/implementation_new_tasks` + `/commit_push`) |
| Approved | `/implementation_approve` |

## Prerequisites

- New implementation steps created (`/implementation_new_tasks`)
- Changes committed and pushed (`/commit_push`)

## Instructions

```bash
mcp-coder set-status status-05:plan-ready
```

Confirm the status change was successful. If it fails, report the error. Do not use `--force` unless explicitly asked.

## Next Steps

Run `mcp-coder implement` to process the new steps, then `/implementation_review`.
