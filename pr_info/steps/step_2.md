# Step 2: Apply Footer Stripping to PR Body in `parse_pr_summary()` (TDD)

## Objective

Apply the enhanced `strip_claude_footers()` function to PR body descriptions in the `parse_pr_summary()` function, using Test-Driven Development.

## Context

**Summary Reference**: See `pr_info/steps/summary.md` for full context.

**Previous Step**: Step 1 enhanced `strip_claude_footers()` to handle real-world patterns. Now we apply it to PR bodies.

**Current Limitation**: PR descriptions include advertising footers. We need to strip them before GitHub PR creation.

## WHERE

**File**: `src/mcp_coder/workflows/create_pr/core.py`
**Function**: `parse_pr_summary(llm_response: str) -> Tuple[str, str]`

**Test File**: `tests/workflows/create_pr/test_parsing.py`
**Test Class**: Tests for `parse_pr_summary()` function (add PR body footer stripping tests)

## WHAT

### 1. Add New Parameterized Tests for PR Body Integration (Write Tests First - TDD)

Add the following parameterized tests to `tests/workflows/create_pr/test_parsing.py`:

```python
@pytest.mark.parametrize("llm_response,expected_title,expected_body", [
    # Robot emoji footer
    ("TITLE: feat: add feature\nBODY:\n## Summary\nAdds feature\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)",
     "feat: add feature", "## Summary\nAdds feature"),
    
    # Co-Authored-By footer
    ("TITLE: fix: bug fix\nBODY:\n## Summary\nFixes bug\n\nCo-authored-by: Claude Opus 4.5 <noreply@anthropic.com>",
     "fix: bug fix", "## Summary\nFixes bug"),
    
    # Both footers
    ("TITLE: docs: update\nBODY:\n## Summary\nUpdates docs\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>",
     "docs: update", "## Summary\nUpdates docs"),
    
    # Empty body
    ("TITLE: feat: test\nBODY:\n",
     "feat: test", ""),
])
def test_parse_pr_summary_strips_footers(llm_response: str, expected_title: str, expected_body: str) -> None:
    """Test that parse_pr_summary() strips Claude footers from PR body."""

def test_parse_pr_summary_preserves_footer_mentions_in_content() -> None:
    """Test that legitimate PR body content mentioning footers is preserved."""
```

**Note:** Use `@pytest.mark.parametrize` to test multiple scenarios in one test function.

### 2. Modify `parse_pr_summary()` Function

**Current Signature** (unchanged):
```python
def parse_pr_summary(llm_response: str) -> Tuple[str, str]:
    """Parse LLM response into PR title and body.

    Expected format:
    TITLE: feat: some title
    BODY:
    ## Summary
    ...

    Args:
        llm_response: Raw response from LLM

    Returns:
        Tuple of (title, body) strings
    """
```

**Changes**:
- Add import of `strip_claude_footers` from `workflow_utils.commit_operations`
- Apply footer stripping to `body` variable before returning
- Strip from body ONLY, not title (titles are too short for footers)

## HOW

### Integration Points

**Import** (add to top of `core.py`):
```python
from mcp_coder.workflow_utils.llm_response_utils import strip_claude_footers
```

**Function Modification**:
```python
# At the end of parse_pr_summary(), before final return:
# Strip Claude footers from body (not title)
body = strip_claude_footers(body)
```

### Algorithm (Footer Stripping in parse_pr_summary)

```
PSEUDOCODE for parse_pr_summary() footer stripping integration:
1. Parse LLM response to extract title and body (existing logic)
2. Apply fallback logic if parsing fails (existing logic)
3. BEFORE returning (title, body):
   a. Strip Claude footers from body: body = strip_claude_footers(body)
   b. Keep title unchanged (titles don't have footers)
4. RETURN (title, body)
```

### Implementation Details

**Placement in Function**:
```python
def parse_pr_summary(llm_response: str) -> Tuple[str, str]:
    # ... existing parsing logic ...
    
    # Final fallbacks
    title = title_match or "Pull Request"
    body = body_content or "Pull Request"
    
    # NEW: Strip Claude footers from body only
    body = strip_claude_footers(body)
    
    logger.info(f"Parsed PR title: {title}")
    return title, body
```

**Edge Cases**:
- Empty body → `strip_claude_footers("")` returns `""` (safe)
- Body with only footers → `strip_claude_footers()` returns `""` (acceptable)
- Title unchanged → footers never appear in titles

## DATA

### Input

```python
llm_response: str  # Raw LLM response with TITLE: and BODY: markers
```

### Output

```python
returns: Tuple[str, str]  # (title, body_with_footers_removed)
```

### Test Data Examples

**Input 1** (PR body with robot emoji):
```
"TITLE: feat: add new feature\nBODY:\n## Summary\nAdds feature\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

**Expected Output 1**:
```python
("feat: add new feature", "## Summary\nAdds feature")
```

**Input 2** (PR body with Co-Authored-By):
```
"TITLE: fix: bug fix\nBODY:\n## Summary\nFixes bug\n\nCo-authored-by: Claude Opus 4.5 <noreply@anthropic.com>"
```

**Expected Output 2**:
```python
("fix: bug fix", "## Summary\nFixes bug")
```

**Input 3** (PR body with both footers):
```
"TITLE: docs: update docs\nBODY:\n## Summary\nUpdates documentation\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Expected Output 3**:
```python
("docs: update docs", "## Summary\nUpdates documentation")
```

**Input 4** (PR body mentioning footers in content - should preserve):
```
"TITLE: feat: add footer support\nBODY:\n## Summary\nThis PR adds support for 🤖 robot emojis in content.\nThe Co-Authored-By field is also documented."
```

**Expected Output 4**:
```python
("feat: add footer support", "## Summary\nThis PR adds support for 🤖 robot emojis in content.\nThe Co-Authored-By field is also documented.")
```

## LLM Implementation Prompt

```
Please implement Step 2 of the plan in pr_info/steps/summary.md.

Context: We are integrating the enhanced strip_claude_footers() function into 
the parse_pr_summary() function in src/mcp_coder/workflows/create_pr/core.py 
to remove advertising footers from PR body descriptions.

Follow TDD approach:
1. Add ~2 new parameterized tests to tests/workflows/create_pr/test_parsing.py as described in step_2.md
2. Tests should verify parse_pr_summary() with full LLM response format (TITLE:/BODY:) containing footers
3. Run tests to verify they fail (red phase)
4. Then modify parse_pr_summary() in core.py:
   - Add import: from mcp_coder.workflow_utils.llm_response_utils import strip_claude_footers
   - Apply footer stripping to body before return: body = strip_claude_footers(body)
   - Keep title unchanged
5. Run tests to verify they pass (green phase)

Key requirements:
- Test location mirrors source structure (test_parsing.py mirrors core.py)
- Strip footers from body ONLY (not title)
- Place footer stripping just before the final return statement
- Handle edge cases (empty body, body with only footers)
- Preserve legitimate content that mentions footers
- Use parameterized tests for multiple scenarios
- Follow the pseudocode algorithm in step_2.md

After implementation, run: mcp__code-checker__run_pytest_check with appropriate markers
to verify all tests pass.
```

## Acceptance Criteria

- [ ] ~2 new parameterized tests added to `tests/workflows/create_pr/test_parsing.py`
- [ ] All new PR body tests pass
- [ ] All existing tests still pass (backward compatibility)
- [ ] Tests use full LLM response format (TITLE:/BODY:)
- [ ] Test location mirrors source structure (test_parsing.py for core.py)
- [ ] `parse_pr_summary()` imports `strip_claude_footers` from `llm_response_utils`
- [ ] `parse_pr_summary()` applies footer stripping to body only
- [ ] PR titles are unchanged (not stripped)
- [ ] Edge cases handled (empty body, body with only footers)
- [ ] Legitimate content mentioning footers is preserved
- [ ] Pytest runs successfully for `tests/workflows/create_pr/test_parsing.py`
