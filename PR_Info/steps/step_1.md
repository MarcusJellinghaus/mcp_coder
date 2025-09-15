# Step 1: Create Test Directory Structure

## Context
Reference: `pr_info/steps/summary.md` - Test Structure Reorganization Summary

## Objective
Create the nested directory structure and `__init__.py` files to mirror the source code hierarchy.

## WHERE
- `tests/llm_providers/` (new directory)
- `tests/llm_providers/__init__.py` (new file)
- `tests/llm_providers/claude/` (new directory)
- `tests/llm_providers/claude/__init__.py` (new file)
- `tests/utils/` (new directory)
- `tests/utils/__init__.py` (new file)

## WHAT
Create directory structure with proper Python package initialization:
```python
# Function signature (conceptual)
def create_test_directory_structure() -> bool
```

## HOW
- Use filesystem operations to create directories
- Add minimal `__init__.py` files for Python package recognition
- Ensure directories are created in correct hierarchy

## ALGORITHM
```
1. Create tests/llm_providers/ directory
2. Create tests/llm_providers/__init__.py with package comment
3. Create tests/llm_providers/claude/ directory  
4. Create tests/llm_providers/claude/__init__.py with package comment
5. Create tests/utils/ directory
6. Create tests/utils/__init__.py with package comment
```

## DATA
**Input**: None
**Output**: Directory structure created successfully (boolean)
**Structure**: New directories and `__init__.py` files as specified

## LLM Prompt
```
Create the test directory structure for the mcp_coder project. Based on the summary in pr_info/steps/summary.md, create:

1. tests/llm_providers/ directory
2. tests/llm_providers/__init__.py with comment "# LLM providers tests"
3. tests/llm_providers/claude/ directory
4. tests/llm_providers/claude/__init__.py with comment "# Claude provider tests"
5. tests/utils/ directory  
6. tests/utils/__init__.py with comment "# Utils tests"

Use the file system tools to create these directories and files. Ensure proper Python package structure.
```
