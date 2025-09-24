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

## Usage Pattern

```batch
workflows\implement.bat
```

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