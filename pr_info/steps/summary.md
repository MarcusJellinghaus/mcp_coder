<<<<<<< HEAD
# Issue #435: Remove Advertising Footers from PR Descriptions

## Problem Statement

When creating a PR via `create-pr`, LLM-generated descriptions include advertising footers (e.g., `🤖 Generated with [Claude Code]`, `Co-Authored-By: Claude <noreply@anthropic.com>`) that should be automatically removed before submission to GitHub.

## Current State

- ✅ **Commit messages**: Footer stripping implemented via `strip_claude_footers()` in `src/mcp_coder/workflow_utils/commit_operations.py`
- ❌ **PR descriptions**: No footer stripping - footers appear in GitHub PRs

## Solution Overview

**KISS Principle Applied**: Minimal enhancement with targeted refactoring.

Instead of complex tiered pattern matching, we:
1. Move `strip_claude_footers()` to a shared module (used by both commits and PRs)
2. Enhance it to handle real-world patterns with case-insensitive regex
3. Reuse it for PR body stripping

## Architectural / Design Changes

### Design Decision: Minimal Enhancement (Option 2)

**What We're Doing:**
- ✅ Create shared module `llm_response_utils.py` (function used by both commits and PRs)
- ✅ Move `strip_claude_footers()` to shared module
- ✅ Enhance with case-insensitive regex matching
- ✅ Support model name variations (Claude Opus 4.5, Claude Sonnet 4.5, etc.)
- ✅ Apply footer stripping to PR body in `parse_pr_summary()`
- ✅ Mirror test structure to source structure
- ✅ Use parameterized tests to reduce duplication

**What We're NOT Doing:**
- ❌ No tiered pattern matching (Tier 1/Tier 2 complexity - REJECTED)
- ❌ No 5-line safety limits (current backward iteration is sufficient)
- ❌ No regex for markdown link detection (can add later if needed)

**Rationale:**
- Solves the problem with focused changes
- Shared module reflects actual usage (commits + PRs)
- Test structure mirrors source structure (best practice)
- Avoids complex tiered patterns (KISS principle)
- Can extend later if more complexity is needed

### Footer Patterns to Remove

Based on git analysis of 100 commits:

1. **Robot emoji pattern** (always remove):
   - `🤖 Generated with [Claude Code](https://claude.com/claude-code)`
   - `🤖 Generated with https://claude.com/claude-code`

2. **Co-Authored-By pattern** (case-insensitive, with model variations):
   - `Co-authored-by: Claude Opus 4.5 <noreply@anthropic.com>` (23 occurrences)
   - `Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>` (5 occurrences)
   - `Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>` (17 occurrences)
   - `co-authored-by: Claude Sonnet 4.5 <noreply@anthropic.com>` (1 occurrence)
   - `Co-authored-by: Claude <noreply@anthropic.com>` (2 occurrences)

3. **Trailing blank lines** (always remove)

**Preserved Patterns:**
- ✅ AutoRunner Bot footers: `Co-authored-by: AutoRunner Bot <autorunner@example.com>`
- ✅ Legitimate content mentioning Claude or footers in body

## Files to Create or Modify

### Files to Create

1. **`src/mcp_coder/workflow_utils/llm_response_utils.py`**
   - New shared module for LLM response processing utilities
   - Move `strip_claude_footers()` function from `commit_operations.py`
   - Enhance function with case-insensitive regex pattern matching
   - Support model name variations in Co-Authored-By pattern

2. **`tests/workflow_utils/test_llm_response_utils.py`**
   - New test file mirroring source structure
   - Move all `TestStripClaudeFooters` tests from `test_commit_operations.py`
   - Add new parameterized tests for case-insensitive matching
   - Add new parameterized tests for model name variations
   - Test AutoRunner Bot preservation

### Files to Modify

1. **`src/mcp_coder/workflow_utils/commit_operations.py`**
   - Remove `strip_claude_footers()` function (moved to `llm_response_utils.py`)
   - Add import: `from .llm_response_utils import strip_claude_footers`

2. **`src/mcp_coder/workflows/create_pr/core.py`**
   - Import `strip_claude_footers` from `workflow_utils.llm_response_utils`
   - Apply footer stripping to body in `parse_pr_summary()` function

3. **`tests/workflow_utils/test_commit_operations.py`**
   - Remove `TestStripClaudeFooters` class (moved to `test_llm_response_utils.py`)

4. **`tests/workflows/create_pr/test_parsing.py`**
   - Add parameterized tests for PR body integration with `parse_pr_summary()`
   - Test full LLM response format (TITLE: / BODY:) with footers

## Implementation Approach

### Test-Driven Development (TDD)

Each step follows TDD:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Verify integration

### Steps Overview

1. **Step 1**: Create `llm_response_utils.py` module and enhance `strip_claude_footers()` with case-insensitive regex (TDD)
2. **Step 2**: Apply footer stripping to PR body in `parse_pr_summary()` (TDD)
3. **Step 3**: Integration testing and quality gates

## Success Criteria

- [ ] PR descriptions don't contain `🤖` footer
- [ ] PR descriptions don't contain `Co-authored-by: Claude ... <noreply@anthropic.com>` (any case variation)
- [ ] PR descriptions don't contain model name variations (Opus 4.5, Sonnet 4.5)
- [ ] AutoRunner Bot footers are preserved
- [ ] `strip_claude_footers()` docstring updated to reflect case-insensitive matching, model variations, and PR body usage
- [ ] All existing commit message tests pass (backward compatibility)
- [ ] All new parameterized tests pass
- [ ] Test structure mirrors source structure
- [ ] Quality gates pass (pylint, pytest, mypy)

## Testing Strategy

### Unit Tests
- Case-insensitive Co-Authored-By matching
- Model name variations (Opus 4.5, Sonnet 4.5, no model name)
- AutoRunner Bot preservation
- Backward compatibility with existing tests

### Integration Tests
- PR body stripping in `parse_pr_summary()`
- End-to-end PR creation workflow

## Future Enhancements (Out of Scope)

If needed later, we can:
- Add tiered pattern matching (markdown links requiring blank lines)
- Add 5-line safety limits
- Refactor to dedicated `llm_response_utils.py` module
- Extend to issue descriptions if footers appear there
=======
# Issue #435: Remove Advertising Footers from PR Descriptions

## Problem Statement

When creating a PR via `create-pr`, LLM-generated descriptions include advertising footers (e.g., `🤖 Generated with [Claude Code]`, `Co-Authored-By: Claude <noreply@anthropic.com>`) that should be automatically removed before submission to GitHub.

## Current State

- ✅ **Commit messages**: Footer stripping implemented via `strip_claude_footers()` in `src/mcp_coder/workflow_utils/commit_operations.py`
- ❌ **PR descriptions**: No footer stripping - footers appear in GitHub PRs

## Solution Overview

**KISS Principle Applied**: Minimal enhancement with targeted refactoring.

Instead of complex tiered pattern matching, we:
1. Move `strip_claude_footers()` to a shared module (used by both commits and PRs)
2. Enhance it to handle real-world patterns with case-insensitive regex
3. Reuse it for PR body stripping

## Architectural / Design Changes

### Design Decision: Minimal Enhancement (Option 2)

**What We're Doing:**
- ✅ Create shared module `llm_response_utils.py` (function used by both commits and PRs)
- ✅ Move `strip_claude_footers()` to shared module
- ✅ Enhance with case-insensitive regex matching
- ✅ Support model name variations (Claude Opus 4.5, Claude Sonnet 4.5, etc.)
- ✅ Apply footer stripping to PR body in `parse_pr_summary()`
- ✅ Mirror test structure to source structure
- ✅ Use parameterized tests to reduce duplication

**What We're NOT Doing:**
- ❌ No tiered pattern matching (Tier 1/Tier 2 complexity - REJECTED)
- ❌ No 5-line safety limits (current backward iteration is sufficient)
- ❌ No regex for markdown link detection (can add later if needed)

**Rationale:**
- Solves the problem with focused changes
- Shared module reflects actual usage (commits + PRs)
- Test structure mirrors source structure (best practice)
- Avoids complex tiered patterns (KISS principle)
- Can extend later if more complexity is needed

### Footer Patterns to Remove

Based on git analysis of 100 commits:

1. **Robot emoji pattern** (always remove):
   - `🤖 Generated with [Claude Code](https://claude.com/claude-code)`
   - `🤖 Generated with https://claude.com/claude-code`

2. **Co-Authored-By pattern** (case-insensitive, with model variations):
   - `Co-authored-by: Claude Opus 4.5 <noreply@anthropic.com>` (23 occurrences)
   - `Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>` (5 occurrences)
   - `Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>` (17 occurrences)
   - `co-authored-by: Claude Sonnet 4.5 <noreply@anthropic.com>` (1 occurrence)
   - `Co-authored-by: Claude <noreply@anthropic.com>` (2 occurrences)

3. **Trailing blank lines** (always remove)

**Preserved Patterns:**
- ✅ AutoRunner Bot footers: `Co-authored-by: AutoRunner Bot <autorunner@example.com>`
- ✅ Legitimate content mentioning Claude or footers in body

## Files to Create or Modify

### Files to Create

1. **`src/mcp_coder/workflow_utils/llm_response_utils.py`**
   - New shared module for LLM response processing utilities
   - Move `strip_claude_footers()` function from `commit_operations.py`
   - Enhance function with case-insensitive regex pattern matching
   - Support model name variations in Co-Authored-By pattern

2. **`tests/workflow_utils/test_llm_response_utils.py`**
   - New test file mirroring source structure
   - Move all `TestStripClaudeFooters` tests from `test_commit_operations.py`
   - Add new parameterized tests for case-insensitive matching
   - Add new parameterized tests for model name variations
   - Test AutoRunner Bot preservation

### Files to Modify

1. **`src/mcp_coder/workflow_utils/commit_operations.py`**
   - Remove `strip_claude_footers()` function (moved to `llm_response_utils.py`)
   - Add import: `from .llm_response_utils import strip_claude_footers`

2. **`src/mcp_coder/workflows/create_pr/core.py`**
   - Import `strip_claude_footers` from `workflow_utils.llm_response_utils`
   - Apply footer stripping to body in `parse_pr_summary()` function

3. **`tests/workflow_utils/test_commit_operations.py`**
   - Remove `TestStripClaudeFooters` class (moved to `test_llm_response_utils.py`)

4. **`tests/workflows/create_pr/test_parsing.py`**
   - Add parameterized tests for PR body integration with `parse_pr_summary()`
   - Test full LLM response format (TITLE: / BODY:) with footers

## Implementation Approach

### Test-Driven Development (TDD)

Each step follows TDD:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Verify integration

### Steps Overview

1. **Step 1**: Create `llm_response_utils.py` module and enhance `strip_claude_footers()` with case-insensitive regex (TDD)
2. **Step 2**: Apply footer stripping to PR body in `parse_pr_summary()` (TDD)
3. **Step 3**: Integration testing and quality gates

## Success Criteria

- [x] PR descriptions don't contain `🤖` footer
- [x] PR descriptions don't contain `Co-authored-by: Claude ... <noreply@anthropic.com>` (any case variation)
- [x] PR descriptions don't contain model name variations (Opus 4.5, Sonnet 4.5)
- [x] AutoRunner Bot footers are preserved
- [x] `strip_claude_footers()` docstring updated to reflect case-insensitive matching, model variations, and PR body usage
- [x] All existing commit message tests pass (backward compatibility)
- [x] All new parameterized tests pass
- [x] Test structure mirrors source structure
- [x] Quality gates pass (pylint, pytest, mypy)

## Testing Strategy

### Unit Tests
- Case-insensitive Co-Authored-By matching
- Model name variations (Opus 4.5, Sonnet 4.5, no model name)
- AutoRunner Bot preservation
- Backward compatibility with existing tests

### Integration Tests
- PR body stripping in `parse_pr_summary()`
- End-to-end PR creation workflow

## Future Enhancements (Out of Scope)

If needed later, we can:
- Add tiered pattern matching (markdown links requiring blank lines)
- Add 5-line safety limits
- Refactor to dedicated `llm_response_utils.py` module
- Extend to issue descriptions if footers appear there
>>>>>>> d713e7b (docs: mark Step 3 integration testing tasks as complete)
