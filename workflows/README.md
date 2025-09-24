# Workflows

This directory contains automated workflow scripts that orchestrate existing mcp-coder functionality to streamline development tasks.

## Concept

Workflows combine multiple mcp-coder tools to create end-to-end automation:
- Task detection and planning
- Prompt management and LLM interaction  
- Code formatting and quality checks
- Git operations and commit management
- Conversation storage and documentation

## Available Workflows

### implement.bat
Automated implementation workflow that:
1. Detects tasks from pr_info/TASK_TRACKER.md
2. Retrieves implementation prompts using `prompt_manager.get_prompt()`
3. Orchestrates LLM interaction for code implementation
4. Runs quality checks (pylint, pytest, mypy)
5. Formats and commits changes
6. Updates task tracking

## Standard Tools Referenced

The workflows leverage these existing mcp-coder components:
- `prompt_manager.get_prompt()` - Prompt retrieval and management
- Standard formatters - Code formatting and style consistency
- Commit operations - Git integration and change management  
- Task tracking - Progress monitoring and status updates
- Quality checks - Automated testing and validation

## Usage Examples

### Basic Usage
```batch
# Run the implementation workflow from project root
workflows\implement.bat
```

### Expected Output
```
[10:30:15] Starting implement workflow...
[10:30:15] Checking prerequisites...
[10:30:15] Prerequisites check passed
[10:30:16] Checking for incomplete tasks...
[10:30:16] Found next task: Step 4: Test Workflow Integration
[10:30:16] Loading implementation prompt template...
[10:30:17] Calling LLM for implementation...
[10:30:45] LLM response received successfully
[10:30:45] Saving conversation for step 4...
[10:30:45] Conversation saved to pr_info\.conversations\step_4.md
[10:30:46] Running code formatters...
[10:30:47] black formatting completed successfully
[10:30:48] isort formatting completed successfully
[10:30:48] All formatters completed successfully
[10:30:48] Committing changes...
[10:30:52] Changes committed successfully: abc1234
[10:30:52] Implement workflow completed successfully!
```

### What Gets Created
- **Conversation files**: `pr_info\.conversations\step_N.md` with LLM interactions
- **Formatted code**: All Python files processed with black/isort
- **Git commit**: Automatic commit with descriptive message
- **Task progress**: Workflow progresses to next incomplete task

### Integration Points
- **Task detection**: Uses `get_incomplete_tasks()` from task_tracker module
- **Prompt loading**: Uses `get_prompt()` from prompt_manager module
- **LLM calls**: Uses `ask_llm()` from llm_interface module
- **Code formatting**: Uses `format_code()` from formatters module
- **Git operations**: Uses commit functions from utils.git_operations module

## Prerequisites

### Required Files
- `pr_info/TASK_TRACKER.md` - Task tracking file with incomplete tasks
- `src/mcp_coder/prompts/prompts.md` - Contains "Implementation Prompt Template" section
- `.git/` directory - Project must be a git repository

### Environment Setup
- Python environment with mcp-coder dependencies installed
- Git repository initialized and configured
- Claude Code CLI or API access configured for LLM calls

Workflows follow KISS principles:
- Simple orchestration of existing functionality
- Clear documentation and error handling
- Minimal complexity and dependencies
- Reusable patterns for future workflow additions

## Future Workflows

This infrastructure supports adding new workflows following the same pattern:
- Leverage existing mcp-coder tools
- Document integration points clearly
- Keep implementation simple and focused
- Maintain consistent usage patterns