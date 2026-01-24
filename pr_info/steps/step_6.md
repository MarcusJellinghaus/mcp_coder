# Step 6: Create Slash Command Wrapper

## LLM Prompt
```
Based on the summary document and this step, create the slash command wrapper that enables Claude Code to use the branch status functionality interactively.

Create `.claude/commands/check_branch_status.md` that provides a simple wrapper around the CLI command. Follow the existing patterns used by other slash commands in the .claude/commands/ directory.

Reference the summary document for the command modes and ensure the slash command uses LLM-optimized output.
```

## WHERE
- **New File**: `.claude/commands/check_branch_status.md`
- **Reference Files**: Other `.claude/commands/*.md` files for pattern consistency

## WHAT

### Slash Command Content
```markdown
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
- Truncated CI error logs (~200 lines)
- Clear status indicators  
- Actionable recommendations
- Progress on fixes applied

## Integration

This slash command enables interactive workflow management:
- Check readiness before creating PRs
- Diagnose and fix CI failures
- Validate task completion
- Coordinate GitHub label transitions
```

### Expected CLI Execution
```bash
# The slash command will execute:
mcp-coder check-branch-status --fix --llm-truncate
```

## HOW

### Integration Pattern
Follow existing `.claude/commands/` patterns:
1. Clear markdown documentation with usage examples
2. Explanation of what the command does
3. Simple bash command execution
4. Integration context for Claude Code workflows

### File Structure Template
```markdown
# [Command Name]
[Brief description]

## Usage  
[Bash command to execute]

## What This Command Does
[Numbered list of capabilities]

## [Special Sections]
[Any command-specific details]

## Integration
[How it fits into workflows]
```

## DATA

### Command Behavior
```bash
# Executed command:
mcp-coder check-branch-status --fix --llm-truncate

# Expected behaviors:
- Returns 0 on success (ready or fixed)
- Returns 1 on errors or user decline
- Outputs LLM-optimized format (~200 lines)
- Attempts safe auto-fixes automatically
- Prompts for risky operations
```

### Use Cases for Claude Code
```
1. Pre-PR readiness check
2. CI failure diagnosis and fixing
3. Implementation workflow validation  
4. Branch status before major operations
5. GitHub label management assistance
```

## Implementation Notes
- **Simplicity**: Just a wrapper around CLI command with optimal flags
- **Documentation**: Clear explanation of capabilities for Claude Code context
- **Consistency**: Follow same markdown structure as other slash commands  
- **LLM Context**: Explain how output is optimized for LLM consumption
- **Workflow Integration**: Show how this fits into broader development workflows