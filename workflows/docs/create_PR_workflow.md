# Create PR Workflow

## Purpose
Automates PR creation after feature implementation: validates completion, generates PR summaries, creates GitHub PRs, cleans up planning files.

## Usage
```bash
python workflows/create_PR.py
workflows/create_PR.bat
```

## Prerequisites
- Clean working directory (no uncommitted changes)
- All tasks in `TASK_TRACKER.md` marked complete
- On feature branch (not main/master)
- GitHub credentials configured

## Workflow Steps
1. **Prerequisites Check**: Validates git status, tasks, branch
2. **PR Summary**: Generates title/description using LLM analysis of git diff
3. **Create PR**: Creates GitHub pull request
4. **Cleanup**: Deletes `pr_info/steps/`, truncates task tracker, commits changes

## Files
- **Required**: `src/mcp_coder/prompts/prompts.md`, `pr_info/TASK_TRACKER.md`
- **Generated**: GitHub PR, cleanup commits
- **Deleted**: `pr_info/steps/` directory

## Testing
- Unit tests: `tests/test_create_pr.py`
- Integration tests: `tests/workflows/test_create_pr_integration.py`

## Common Issues
- "Working directory not clean" → Commit/stash changes
- "Found incomplete tasks" → Mark all tasks complete in `TASK_TRACKER.md`
- "Current branch is parent" → Switch to feature branch