# Create PR Workflow

## Purpose
Automates PR creation after feature implementation: validates completion, generates PR summaries, creates GitHub PRs, cleans up planning files.

## Usage
```bash
# Use default claude_code_api method
python workflows/create_PR.py
workflows/create_PR.bat

# Use claude_code_cli method instead
python workflows/create_PR.py --llm-method claude_code_cli
workflows/create_PR.bat --llm-method claude_code_cli

# Other options
python workflows/create_PR.py --project-dir /path/to/project --log-level DEBUG --llm-method claude_code_api
```

## Parameters
- `--project-dir PATH`: Project directory path (default: current directory)
- `--log-level LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) (default: INFO)
- `--llm-method METHOD`: LLM method to use (claude_code_cli, claude_code_api) (default: claude_code_api)

## LLM Methods
- **claude_code_api** (default): Faster, requires API credentials
- **claude_code_cli**: Fallback option, requires CLI setup
- Use CLI method if API fails or for debugging

## Prerequisites
- Clean working directory (no uncommitted changes)
- All tasks in `TASK_TRACKER.md` marked complete
- On feature branch (not main/master)
- GitHub credentials configured

## Workflow Steps
1. **Prerequisites Check**: Validates git status, tasks, branch
2. **PR Summary**: Generates title/description using LLM analysis of git diff (supports both claude_code_api and claude_code_cli methods)
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
- "LLM API failed" → Try `--llm-method claude_code_cli` or check API credentials
- "Empty LLM response" → Verify Claude Code authentication and network connectivity