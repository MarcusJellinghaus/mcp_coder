# Step 2: Move Claude Provider Test Files

## Context
Reference: `pr_info/steps/summary.md` - Test Structure Reorganization Summary
Prerequisite: Step 1 completed (directory structure created)

## Objective
Move all Claude-related test files from `tests/` root to `tests/llm_providers/claude/` directory.

## WHERE
**Source locations** (to be moved FROM):
- `tests/test_claude_client.py`
- `tests/test_claude_client_integration.py`
- `tests/test_claude_code_api.py`
- `tests/test_claude_code_cli.py`
- `tests/test_claude_executable_finder.py`

**Target location** (to be moved TO):
- `tests/llm_providers/claude/` (all files above)

## WHAT
Move test files while preserving content:
```python
# Function signature (conceptual)
def move_claude_test_files() -> list[str]
```

## HOW
- Use file system move operations
- Maintain original file names and content
- Ensure no data loss during transfer

## ALGORITHM
```
1. Move test_claude_client.py to tests/llm_providers/claude/
2. Move test_claude_client_integration.py to tests/llm_providers/claude/
3. Move test_claude_code_api.py to tests/llm_providers/claude/
4. Move test_claude_code_cli.py to tests/llm_providers/claude/
5. Move test_claude_executable_finder.py to tests/llm_providers/claude/
6. Verify all files moved successfully
```

## DATA
**Input**: List of source file paths
**Output**: List of successfully moved files
**Structure**: 5 test files relocated to new directory structure

## LLM Prompt
```
Move Claude provider test files to the new directory structure. Based on the summary in pr_info/steps/summary.md and after completing step 1, move these files:

From tests/ to tests/llm_providers/claude/:
- test_claude_client.py
- test_claude_client_integration.py  
- test_claude_code_api.py
- test_claude_code_cli.py
- test_claude_executable_finder.py

Use the file system tools to move these files. Preserve all file content exactly - only change the location.
```
