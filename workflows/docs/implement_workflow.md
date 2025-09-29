# Implement Workflow

## Purpose
Continuous automation script that processes ALL incomplete implementation tasks sequentially: generates code, fixes types, formats, commits, and pushes for each task until feature is complete.

## Usage
```bash
python workflows/implement.py
workflows/implement.bat
```

## Prerequisites
- Clean working directory (no uncommitted changes)
- On feature branch (not main/master)
- `TASK_TRACKER.md` or `pr_info/steps/` directory exists
- Development tools installed (black, isort, mypy)

## Workflow Loop
For each incomplete task:
1. **Get Task**: Extract next incomplete task from tracker
2. **LLM Implementation**: Generate code using implementation prompt
3. **Save Conversation**: Store interaction in `pr_info/.conversations/step_N.md`
4. **Type Check**: Run mypy with auto-fixing (saves fix attempts separately)
5. **Format Code**: Apply black and isort
6. **Commit**: Generate commit message and commit changes
7. **Push**: Push to remote repository
8. **Repeat**: Continue until no incomplete tasks remain

## Features
- **Auto-populate task tracker**: From `pr_info/steps/` directory if needed
- **Smart mypy fixing**: Prevents infinite loops, max 3 identical attempts
- **Conversation history**: Saves all LLM interactions with timestamps
- **Quality assurance**: Automatic formatting and type checking
- **Git integration**: Auto-generated commit messages and pushing

## Files
- **Required**: `mcp_coder/prompts/prompts.md`, `TASK_TRACKER.md` or `pr_info/steps/`
- **Generated**: `pr_info/.conversations/step_N*.md`, git commits
- **Modified**: Source code, `TASK_TRACKER.md` (tasks marked complete)

## Common Issues
- "Working directory not clean" → Commit/stash changes
- "Current branch is main" → Switch to feature branch  
- "No implementation tasks" → Create `pr_info/steps/` or populate `TASK_TRACKER.md`
- "LLM timeout" → Check Claude API credentials/network