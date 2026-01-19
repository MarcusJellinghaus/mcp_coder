# Implementation Finalise

Complete any remaining unchecked tasks in the task tracker before transitioning to code review.

## Process

### 1. Read Task Tracker

Read `pr_info/TASK_TRACKER.md` and identify all unchecked tasks (`- [ ]`).

If all tasks are already checked (`- [x]`), report that no finalisation is needed and exit.

### 2. Process Each Unchecked Task

For each unchecked task:

#### Commit Message Tasks
If the task contains "commit message" (case-insensitive):
- Check `git log --oneline -5` for recent commits
- If relevant commits already exist for the current step → mark task as `[x]`
- If no commits exist → write an appropriate commit message to `pr_info/.commit_message.txt`

#### Other Tasks
- Check `pr_info/steps/` for related step files that provide context
- If step files don't exist, analyse based on task name and codebase
- Verify if the task is already complete
- If not complete: implement the required work
- If complete or successfully implemented: mark as `[x]`
- If unable to complete: DO NOT mark as done - explain the issue

### 3. Quality Checks (If Code Changed)

If any code changes were made during this process:
```
- Run pylint (fix all errors)
- Run pytest (fix all failures)
- Run mypy (fix all type errors)
```

### 4. Stage and Commit

1. Stage all changes: `git add -A`
2. Write commit message to `pr_info/.commit_message.txt` if not already done
3. Commit changes with the message from `.commit_message.txt`

**Important**: Do NOT push changes. The slash command mode is for manual use only.

## Output

Report:
1. Which tasks were processed
2. Which tasks were marked complete
3. Any issues encountered
4. Location of commit message file
