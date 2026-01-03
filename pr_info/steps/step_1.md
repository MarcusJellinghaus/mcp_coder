# Step 1: Implement Tests for Claude Footer Stripping

## LLM Prompt

```
Based on the summary in `pr_info/steps/summary.md`, implement comprehensive tests for the `strip_claude_footers()` function in the existing test file `tests/utils/test_commit_operations.py`. Follow Test-Driven Development - write the tests before the function exists.

Add a new test class `TestStripClaudeFooters` with comprehensive test cases covering all the requirements from the issue. Use the existing test patterns in the file for consistency.
```

## WHERE: File Location
- **File**: `tests/utils/test_commit_operations.py`
- **New Test Class**: `TestStripClaudeFooters`
- **Integration**: Add to existing test file structure

## WHAT: Test Functions Required

### Core Test Methods
```python
def test_strip_both_footers_present()
def test_strip_robot_emoji_footer_only() 
def test_strip_coauthored_footer_only()
def test_strip_no_footers_present()
def test_strip_trailing_blank_lines()
def test_strip_empty_or_none_message()
def test_preserve_legitimate_content()
```

## HOW: Implementation Details

### Imports Needed
```python
# Already available in existing file - no new imports needed
```

### Test Class Structure
```python
class TestStripClaudeFooters:
    """Tests for strip_claude_footers function."""
```

## ALGORITHM: Test Logic Approach

```
1. CREATE test message with specific footer patterns
2. CALL strip_claude_footers(message) 
3. ASSERT expected output matches actual output
4. VERIFY legitimate content preserved
5. CHECK edge cases (empty, None, mixed content)
```

## DATA: Test Cases and Expected Results

### Test Case 1: Both Footers Present
**Input:**
```
feat: add new feature

Some commit body text

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```
**Expected Output:**
```
feat: add new feature

Some commit body text
```

### Test Case 2: Robot Emoji Footer Only
**Input:**
```
fix: bug fix

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```
**Expected Output:**
```
fix: bug fix
```

### Test Case 3: Co-Authored Footer Only
**Input:**
```
docs: update readme

Co-Authored-By: Claude <noreply@anthropic.com>
```
**Expected Output:**
```
docs: update readme
```

### Test Case 4: No Footers
**Input:**
```
feat: clean commit message
```
**Expected Output:**
```
feat: clean commit message
```

### Test Case 5: Trailing Blank Lines
**Input:**
```
feat: feature with trailing blanks



🤖 Generated with [Claude Code](https://claude.com/claude-code)



```
**Expected Output:**
```
feat: feature with trailing blanks
```

### Test Case 6: Empty/None Messages
**Input:** `""` or `None`
**Expected Output:** `""` or `None` (unchanged)

### Test Case 7: Legitimate Content Preservation
**Input:**
```
feat: add 🤖 emoji support

This commit adds robot emoji support.
The Co-Authored-By feature is also mentioned.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```
**Expected Output:**
```
feat: add 🤖 emoji support

This commit adds robot emoji support.
The Co-Authored-By feature is also mentioned.
```

## Success Criteria
- [ ] All test cases implemented with clear assertions
- [ ] Tests follow existing file patterns and naming conventions
- [ ] Tests cover all requirements from the issue
- [ ] Tests will initially fail (function doesn't exist yet)
- [ ] Clear test data and expected results defined