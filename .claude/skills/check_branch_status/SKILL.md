---
description: Check branch readiness including CI, rebase needs, tasks, and labels
disable-model-invocation: true
allowed-tools:
  - "Bash(mcp-coder check branch-status *)"
---

!`mcp-coder check branch-status --ci-timeout 180 --llm-truncate`

# Check Branch Status

Check comprehensive branch readiness including CI status, rebase requirements, task completion, and GitHub labels.

## What This Command Does

1. **PR Discovery** (optional): When `--wait-for-pr` is set, polls GitHub for an open PR matching the current branch before proceeding. Requires a remote tracking branch. Use `--pr-timeout <seconds>` to control how long to wait (default: 600s).
2. **CI Status Check**: Analyzes latest workflow run and retrieves error logs
3. **Rebase Detection**: Checks if branch needs rebasing onto main
4. **Task Validation**: Verifies all implementation tasks are complete
5. **GitHub Labels**: Reports current workflow status label
6. **Recommendations**: Provides actionable next steps

## Optional Flags

| Flag | Description |
|------|-------------|
| `--wait-for-pr` | Enable PR discovery phase — poll GitHub until an open PR is found for the current branch before running checks |
| `--pr-timeout <seconds>` | Maximum time to wait for PR discovery (default: 600). Only used with `--wait-for-pr` |
| `--ci-timeout <seconds>` | Maximum time to wait for CI to complete (default: 180) |
| `--llm-truncate` | Truncate CI error logs for LLM-friendly output |

## Follow-Up Actions

Based on the status report, use these commands for next steps:

| Status | Action |
|--------|--------|
| CI failures | Fix the issues shown in the CI error details |
| Rebase needed | Run `/rebase` to rebase onto base branch with conflict resolution |
| Tasks incomplete | Complete remaining tasks manually |
| CI green + tasks done | Run `/commit_push` to commit and push changes |
| Ready to merge | Create PR or merge via GitHub |

## Output Format

LLM-optimized output with:
- CI error logs for failed jobs (truncated to ~300 lines total)
- Complete status information for all other components
- Clear status indicators
- Actionable recommendations

## Integration

This slash command enables interactive workflow management:
- Check readiness before creating PRs
- Diagnose CI failures
- Validate task completion
- Identify when rebase is needed (then use `/rebase`)

## Rationale

**Rationale**: LLM-driven context benefits from waiting for complete results. The 180-second timeout provides a balance between responsiveness and allowing typical CI runs to complete. No `--fix` by default to let LLM analyze failures and suggest targeted fixes.
