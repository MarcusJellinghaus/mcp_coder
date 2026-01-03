# Remove Claude Code Footers from Commit Messages

## Problem Statement

Claude Code's `implement` workflow generates commit messages that include unwanted footer lines:

```
feat(task_tracker): Replace header-level parsing with boundary-based extraction
- Replace complex header-level tracking logic in _find_implementation_section()
...

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

These footers pollute git history and need to be removed from commit messages only.

## Architectural Overview

### Current Architecture
- **Location**: `src/mcp_coder/utils/commit_operations.py`
- **Flow**: LLM → `parse_llm_commit_response()` → validation → commit
- **Issue**: No footer stripping step exists

### Design Changes

#### 1. New Function Addition
- **Function**: `strip_claude_footers(message: str) -> str`
- **Purpose**: Remove Claude Code signature lines from commit messages
- **Algorithm**: Simple backward iteration from end of message
- **Scope**: Commit messages only (existing scope limitation)

#### 2. Integration Point
- **Where**: After `parse_llm_commit_response()` in `generate_commit_message_with_llm()`
- **Change**: Single line addition: `commit_message = strip_claude_footers(commit_message)`
- **Impact**: Minimal disruption to existing flow

#### 3. Design Principles Applied
- **KISS**: Simple string matching, no regex patterns
- **Single Responsibility**: Function does one clear job
- **Backward Compatibility**: Handles messages without footers gracefully
- **Maintainability**: Clear logic, easy to test

### Footer Patterns to Remove
1. Lines starting with `🤖` (robot emoji)
2. Exact match: `Co-Authored-By: Claude <noreply@anthropic.com>`
3. Handle independently (any order, either/both present)
4. Clean trailing blank lines

## Files to Modify

### Source Code
- **`src/mcp_coder/utils/commit_operations.py`**
  - Add `strip_claude_footers()` function
  - Integrate into `generate_commit_message_with_llm()`

### Test Code  
- **`tests/utils/test_commit_operations.py`**
  - Add comprehensive tests for `strip_claude_footers()`
  - Update existing tests to handle footer stripping

## Implementation Strategy

### Test-Driven Development Approach
1. **Step 1**: Implement comprehensive tests for footer stripping
2. **Step 2**: Implement `strip_claude_footers()` function
3. **Step 3**: Integrate into commit message generation flow

### Key Requirements Preserved
- ✅ Strip lines starting with `🤖`
- ✅ Strip `Co-Authored-By: Claude <noreply@anthropic.com>`
- ✅ Handle patterns independently
- ✅ Clean trailing blank lines
- ✅ Only affect commit messages
- ✅ Preserve legitimate content

## Benefits

1. **Clean Git History**: Removes unwanted Claude Code signatures
2. **Minimal Code Changes**: Single function + integration point
3. **Maintainable**: Simple logic, comprehensive tests
4. **Safe**: No disruption to existing commit generation flow
5. **Backward Compatible**: Works with messages that don't have footers