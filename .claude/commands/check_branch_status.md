---
allowed-tools: Bash(mcp-coder check branch-status:*)
workflow-stage: quality-check
suggested-next: commit_push, rebase
---

# Check Branch Status

Check comprehensive branch readiness including CI status, rebase requirements, task completion, and GitHub labels with automatic CI fixing.

## Usage

Call the underlying CLI command with LLM-optimized output:

```bash
mcp-coder check branch-status --fix --llm-truncate
```

## What This Command Does

1. **CI Status Check**: Analyzes latest workflow run and retrieves error logs
2. **Rebase Detection**: Checks if branch needs rebasing onto main
3. **Task Validation**: Verifies all implementation tasks are complete
4. **GitHub Labels**: Reports current workflow status label
5. **Auto-Fix**: Attempts to fix CI failures using LLM
6. **Recommendations**: Provides actionable next steps

## Auto-Fix Capabilities (--fix flag)

- CI test failures - uses LLM to analyze errors and apply fixes
- Code formatting issues - runs formatters as part of CI fix
- Commits fixes with appropriate messages

## Follow-Up Actions

Based on the status report, use these commands for next steps:

| Status | Action |
|--------|--------|
| Rebase needed | Run `/rebase` to rebase onto main with conflict resolution |
| Tasks incomplete | Complete remaining tasks manually |
| CI green + tasks done | Run `/commit_push` to commit and push changes |
| Ready to merge | Create PR or merge via GitHub |

## Output Format

LLM-optimized output with:
- Truncated CI error logs only (~200 lines)
- Complete status information for all other components
- Clear status indicators
- Actionable recommendations
- Progress on fixes applied

## Integration

This slash command enables interactive workflow management:
- Check readiness before creating PRs
- Diagnose and fix CI failures
- Validate task completion
- Identify when rebase is needed (then use `/rebase`)
