# Step 1: Create Slash Command

## Overview

Create the `/implementation_finalise` slash command that allows manual invocation of the finalisation process.

## WHERE

**File to create**: `.claude/commands/implementation_finalise.md`

## WHAT

A markdown file with:
1. YAML frontmatter defining allowed tools
2. Clear instructions for the LLM to follow

### Allowed Tools

```yaml
allowed-tools: 
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git add:*)
  - Bash(git commit:*)
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - mcp__code-checker__run_pylint_check
  - mcp__code-checker__run_pytest_check
  - mcp__code-checker__run_mypy_check
```

### Prompt Content

The prompt should instruct Claude to:

1. Check `pr_info/TASK_TRACKER.md` for unchecked tasks (`- [ ]`)
2. For each unchecked task:
   - If it's a "commit message" task and changes are already committed → mark `[x]` and skip
   - Otherwise: verify if done, complete it if not, then mark `[x]`
3. Use step files in `pr_info/steps/` for context if they exist
4. If step files don't exist, analyse based on task names and codebase
5. If unable to complete a task, DO NOT mark it done - explain the issue
6. Run quality checks (pylint, pytest, mypy) only if any code changes were made
7. Write commit message to `pr_info/.commit_message.txt`
8. Do NOT auto-push (slash command mode)

## HOW

Create the file following the pattern of existing commands like `.claude/commands/commit_push.md` and `.claude/commands/implementation_review.md`.

## ALGORITHM

```
1. Parse TASK_TRACKER.md for unchecked tasks (- [ ])
2. For each unchecked task:
   a. Check if it's a "commit message" task
   b. If commit task: check git log for existing commits → mark done if found
   c. Else: read task context, verify/complete work, mark done
3. If any code changes made → run pylint, pytest, mypy
4. Stage all changes
5. Write commit message to pr_info/.commit_message.txt
6. Commit changes (but don't push)
```

## DATA

- **Input**: `pr_info/TASK_TRACKER.md`, optionally `pr_info/steps/*.md`
- **Output**: Updated `TASK_TRACKER.md`, `pr_info/.commit_message.txt`, git commit

## TEST APPROACH

Manual testing only - slash commands are markdown prompts for Claude, not Python code.

Verify:
1. Command appears in `/help` or can be invoked with `/implementation_finalise`
2. Correctly identifies and processes unchecked tasks
3. Handles missing step files gracefully
4. Writes commit message to correct location

## LLM PROMPT FOR THIS STEP

```
Implement Step 1 from pr_info/steps/step_1.md.

Read the summary at pr_info/steps/summary.md for context.

Create the slash command file at `.claude/commands/implementation_finalise.md` following the specifications in step_1.md. Use existing commands in `.claude/commands/` as reference for the format and style.

After creating the file, verify it has:
1. Correct YAML frontmatter with allowed-tools
2. Clear instructions for the finalisation process
3. Proper handling of commit message tasks
4. Instructions for quality checks
5. Commit message output path specification
```
