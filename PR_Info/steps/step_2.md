# Step 2: Test File Path Functionality 

## WHERE
- **Example file**: `src/mcp_coder/prompts/commit.md` (optional)
- **Test update**: Add file path test to `tests/test_prompt_manager.py`

## WHAT
Optionally create a real prompt file to test file path functionality:

```markdown
# Short Commit
```
Provide a brief commit message for the changes.
Keep it under 50 characters.
```

# Detailed Commit
```
Provide a detailed commit message with body.
Include rationale and context for the changes.
```
```

**Add one more test**:
```python
def test_get_prompt_from_file():
    """Test reading from actual file path (if file exists)."""
```

## HOW
- Optionally create real prompt file
- Add test for file path functionality
- Verify both memory stream AND file path work

## ALGORITHM
```
1. (Optional) Create src/mcp_coder/prompts/commit.md
2. Add test for file path reading
3. Verify auto-detection works for both types
4. Test that file path and memory stream both work
```

## DATA
**Optional file**: `src/mcp_coder/prompts/commit.md`
**Test coverage**: Both memory streams AND file paths work

---

## LLM Prompt for Step 2

You are implementing a prompt manager for the mcp-coder project.

**Context**: Read the summary at `pr_info/steps/summary.md`. Step 1 should be complete with working functions that handle memory streams.

**Current Step**: Test and optionally implement file path functionality.

**Task**: 
1. Add a test for file path functionality in `tests/test_prompt_manager.py`
2. Optionally create `src/mcp_coder/prompts/commit.md` for testing real files

**Requirements**:
- Verify that your auto-detection works for both memory streams and file paths
- Test that the same functions work with both input types
- If you create a real file, use the same format as the embedded test data

**Key point**: This step verifies the flexible input system works for both use cases

**Test**: Verify both `get_prompt(memory_stream, "Header")` AND `get_prompt("file.md", "Header")` work
