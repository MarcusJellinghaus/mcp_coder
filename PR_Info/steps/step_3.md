# Step 3: Update Import Statements in Moved Test Files

## Context
Reference: `pr_info/steps/summary.md` - Test Structure Reorganization Summary
Prerequisite: Step 2 completed (Claude test files moved)

## Objective
Update import statements in moved test files to work from their new locations in the nested directory structure.

## WHERE
**Files to update**:
- `tests/llm_providers/claude/test_claude_client.py`
- `tests/llm_providers/claude/test_claude_client_integration.py`
- `tests/llm_providers/claude/test_claude_code_api.py`
- `tests/llm_providers/claude/test_claude_code_cli.py`
- `tests/llm_providers/claude/test_claude_executable_finder.py`

## WHAT
Fix import paths to work from new nested location:
```python
# Function signature (conceptual)
def update_import_statements(file_path: str) -> bool
```

## HOW
- Analyze existing import statements in each file
- Update relative imports to work from new location depth
- Ensure all `mcp_coder.*` imports remain functional
- Maintain import functionality without changing test logic

## ALGORITHM
```
1. Read each moved test file
2. Identify all import statements (from mcp_coder.*)
3. Verify imports still work from new nested location
4. Update any relative imports if needed
5. Save updated files
6. Validate import syntax is correct
```

## DATA
**Input**: Test file paths with potentially broken imports
**Output**: Test files with corrected import statements
**Structure**: Updated Python import statements maintaining module access

## LLM Prompt
```
Update import statements in the moved Claude test files. Based on the summary in pr_info/steps/summary.md and after completing steps 1-2, check and fix imports in:

- tests/llm_providers/claude/test_claude_client.py
- tests/llm_providers/claude/test_claude_client_integration.py
- tests/llm_providers/claude/test_claude_code_api.py
- tests/llm_providers/claude/test_claude_code_cli.py
- tests/llm_providers/claude/test_claude_executable_finder.py

Review each file's imports and ensure they work from the new nested location. The imports should still reference `mcp_coder.*` modules correctly. Update only import statements - do not change test logic or content.
```
