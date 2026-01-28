---
allowed-tools: Bash(mcp-coder check-branch-status:*)
workflow-stage: quality-check
suggested-next: commit_push, rebase
---

# Check Branch Status

Check comprehensive branch readiness including CI status, rebase requirements, task completion, and GitHub labels with automatic CI fixing.

## Usage

Call the underlying CLI command with LLM-optimized output:

```bash
mcp-coder check-branch-status --fix --llm-truncate
```

## What This Command Does

1. **CI Status Check**: Analyzes latest workflow run and retrieves error logs
2. **Rebase Detection**: Checks if branch needs rebasing onto main
3. **Task Validation**: Verifies all implementation tasks are complete
4. **GitHub Labels**: Reports current workflow status label
5. **Auto-Fix**: Attempts to fix CI failures using LLM
6. **Recommendations**: Provides actionable next steps

## Auto-Fix Capabilities (--fix flag)

**What gets fixed automatically:**
- CI test failures - uses LLM to analyze errors and apply fixes
- Code formatting issues - runs formatters as part of CI fix
- Commits fixes with appropriate messages

**What is informational only (no auto-fix):**
- Rebase status - reports if behind, but does not rebase (use `/rebase` instead)
- Task completion - reports incomplete tasks for manual completion
- GitHub labels - reports current label status

## When Rebase is Needed

If the status report shows "BEHIND" or recommends rebasing:

1. Ensure CI is green first (fix any failures with `--fix`)
2. Run `/rebase` to perform the rebase with merge conflict resolution

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
