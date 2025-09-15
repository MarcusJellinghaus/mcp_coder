# Step 1: Create Simple Test and Core Implementation

## WHERE
- **Test file**: `tests/test_prompt_manager.py`
- **Implementation**: `src/mcp_coder/prompt_manager.py`

## WHAT
Create one simple test file and implement the core prompt manager:

**Simple test** (just test the basics):
```python
def test_get_prompt_basic():
    """Test basic prompt retrieval works."""

def test_validate_prompt_basic():
    """Test basic validation works."""
```

**Core implementation** (two functions):
```python
def get_prompt(filename: str, header: str) -> str:
    """Get prompt from markdown file."""

def validate_prompt_markdown(filename: str) -> bool:
    """Basic validation of prompt file."""
```

## HOW
- Write minimal test first (TDD)
- Implement functions to make test pass
- Use `importlib.resources` for file access
- Simple regex parsing for markdown

## ALGORITHM
```
get_prompt():
1. Load file from src/mcp_coder/prompts/
2. Find "# {header}" with regex
3. Extract next code block (between ```)
4. Return text or raise exception

validate_prompt_markdown():
1. Try to load file, return False if fails
2. Check basic structure exists
3. Return True/False
```

## DATA
**Returns**:
- `get_prompt()` → `str` (prompt text)
- `validate_prompt_markdown()` → `bool`

---

## LLM Prompt for Step 1

You are implementing a prompt manager for the mcp-coder project.

**Context**: Read the summary at `pr_info/steps/summary.md` to understand the overall goal.

**Current Step**: Create a simple test and implement the core functionality in one step.

**Task**: 
1. Create `tests/test_prompt_manager.py` with 2 basic tests
2. Create `src/mcp_coder/prompt_manager.py` with 2 functions to make tests pass

**Requirements**:
- Keep it minimal - just test basic functionality works
- Use TDD: write test first, then implement
- Functions: `get_prompt(filename, header)` and `validate_prompt_markdown(filename)`
- Use `importlib.resources` to access files from `src/mcp_coder/prompts/`
- Simple regex to find `# Header` and extract next code block

**Test should verify**: Basic prompt retrieval and validation work (don't overcomplicate)

**Implementation should**: Load markdown, find header, extract code block, return text
