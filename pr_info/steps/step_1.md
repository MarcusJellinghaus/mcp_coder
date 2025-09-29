# Step 1: Data Structures and Type Definitions

## Objective
Create TypedDict data structures for structured API returns, following the same patterns as `PullRequestData` in the existing codebase.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Module**: New file in existing github_operations package

## WHAT
Define three TypedDict classes:
```python
class IssueData(TypedDict): ...
class CommentData(TypedDict): ...  
class LabelData(TypedDict): ...
```

## HOW
- Import TypedDict from typing
- Follow exact same structure pattern as `PullRequestData` 
- Use Optional for nullable GitHub API fields
- Include comprehensive docstrings

## ALGORITHM
```
1. Import required typing modules
2. Define IssueData with issue fields (number, title, state, etc.)
3. Define CommentData with comment fields (id, body, user, etc.)
4. Define LabelData with label fields (name, color, description)  
5. Add module-level docstring explaining data structures
```

## DATA
```python
IssueData = {
    "number": int,
    "title": str, 
    "body": str,
    "state": str,  # "open" or "closed"
    "labels": List[str],
    "user": Optional[str],
    "created_at": Optional[str],
    "updated_at": Optional[str], 
    "url": str,
    "locked": bool
}

CommentData = {
    "id": int,
    "body": str,
    "user": Optional[str], 
    "created_at": Optional[str],
    "updated_at": Optional[str],
    "url": str
}

LabelData = {
    "name": str,
    "color": str,
    "description": Optional[str]
}
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 1: Data Structures.

Create TypedDict classes in src/mcp_coder/utils/github_operations/issue_manager.py following the exact same patterns as PullRequestData in pr_manager.py.

Requirements:
- Follow the existing code style and imports from pr_manager.py
- Include comprehensive docstrings for each TypedDict
- Use Optional types for nullable GitHub API fields
- Add module-level docstring explaining the data structures

Focus only on the TypedDict definitions - no classes or functions yet.
```
