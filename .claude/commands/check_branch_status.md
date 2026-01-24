---
allowed-tools: Bash(mcp-coder check-branch-status:*)
workflow-stage: quality-check
suggested-next: commit_push, rebase
---

# Check Branch Status

Check comprehensive branch readiness including CI status, rebase requirements, task completion, and GitHub labels with automatic fixing.

## Usage

Call the underlying CLI command with LLM-optimized output:

```bash
mcp-coder check-branch-status --fix --llm-truncate
```

## What This Command Does

1. **CI Status Check**: Analyzes latest workflow run and retrieves error logs
2. **Rebase Detection**: Checks if branch needs rebasing and predicts conflicts  
3. **Task Validation**: Verifies all implementation tasks are complete
4. **GitHub Labels**: Reports current workflow status label
5. **Auto-Fix**: Attempts to fix CI failures and safe issues
6. **Recommendations**: Provides actionable next steps

## Auto-Fix Capabilities

**Safe Operations (No Prompt)**:
- Fix CI test failures using existing logic
- Run code formatters and quality checks  
- Commit fixes with appropriate messages

**Prompted Operations**:
- Rebase onto parent branch (if conflicts expected)
- Update GitHub workflow status labels
- Force push operations

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
- Coordinate GitHub label transitions