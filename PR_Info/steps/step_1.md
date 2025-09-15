# Step 1: Core Implementation with Comprehensive Testing

## WHERE
- **Test file**: `tests/test_prompt_manager.py`
- **Implementation**: `src/mcp_coder/prompt_manager.py`

## WHAT
Create comprehensive test suite and implement core functionality:

**Comprehensive test coverage**:
```python
def test_get_prompt_from_string():
    """Test basic prompt retrieval from string content."""

def test_get_prompt_from_file():
    """Test prompt retrieval from file path."""

def test_get_prompt_wildcard():
    """Test wildcard and directory handling."""

def test_get_prompt_missing_header():
    """Test error handling for missing headers."""
    
def test_get_prompt_duplicate_headers():
    """Test error handling for duplicate headers."""

def test_validate_prompt_markdown_valid():
    """Test validation of properly formatted markdown."""
    
def test_validate_prompt_markdown_invalid():
    """Test validation of improperly formatted markdown."""

def test_header_level_matching():
    """Test that any header level matches (#, ##, ###, ####)."""
```

**Core implementation** (three main functions):
```python
def get_prompt(source: str, header: str) -> str:
    """Get prompt from markdown source (file path, directory/wildcard, or string content)."""

def validate_prompt_markdown(source: str) -> dict:
    """Validate prompt markdown structure, return detailed results."""

def validate_prompt_directory(directory: str) -> dict:
    """Validate all markdown files in directory including cross-file duplicates."""
```

## HOW
- **Enhanced error handling**: Clear `ValueError` messages with file names and line numbers
- **Robust parsing**: Handle any header level, detect duplicates within and across files
- **Input auto-detection**: Distinguish file path vs. string content using simple heuristics
- **Type safety**: Add proper type hints and comprehensive validation
- **Virtual concatenation**: Combine multiple files for unified duplicate detection

## ALGORITHM
```
get_prompt():
1. Auto-detect input type (file path vs. string content)
2. Handle wildcards/directories (expand to file list)
3. Load and concatenate all relevant files
4. Find header with any level (# ## ### ####) using regex
5. Extract next code block (between triple backticks)
6. Check for duplicates across all content
7. Return text or raise detailed ValueError

validate_prompt_markdown():
1. Load content (file or string)
2. Parse all headers and code blocks
3. Check for duplicates within content
4. Return detailed dict with validation results

validate_prompt_directory():
1. Load all .md files in directory
2. Concatenate and validate combined content
3. Check cross-file duplicates
4. Return comprehensive validation results
```

## DATA
**Input types**:
- File path: `"prompts/prompts.md"`
- Directory: `"prompts"` (auto-expands to `prompts/*.md`)
- Wildcard: `"prompts/*"` or `"prompts/*.md"`
- String content: actual markdown text (auto-detected)

**Returns**:
- `get_prompt()` → `str` (prompt text)
- `validate_prompt_markdown()` → `dict` with `{"valid": bool, "errors": [list]}`
- `validate_prompt_directory()` → `dict` with detailed validation results

**Exceptions**: 
- `ValueError` for missing headers/blocks, duplicate headers (with file locations)
- `FileNotFoundError` for missing files

---

## LLM Prompt for Step 1

You are implementing a prompt manager for the mcp-coder project.

**Context**: Read the summary at `pr_info/steps/summary.md` and decisions at `pr_info/steps/Decisions.md` to understand the requirements.

**Current Step**: Create comprehensive test suite and core implementation.

**Task**: 
1. Create `tests/test_prompt_manager.py` with comprehensive test coverage
2. Create `src/mcp_coder/prompt_manager.py` with three main functions

**Requirements**:
- Use TDD: write comprehensive tests first, then implement
- Functions: `get_prompt(source, header)`, `validate_prompt_markdown(source)`, `validate_prompt_directory(directory)`
- Support file paths, directories/wildcards, and string content (auto-detected)
- Handle any header level (`#`, `##`, `###`, `####`) for same prompt name
- Detect duplicates within and across files using virtual concatenation
- Return detailed validation results with file names and line numbers
- Use `glob` for wildcard handling, simple heuristics for input detection
- Fail completely on errors with clear `ValueError` messages

**Test coverage**: String content, file paths, wildcards, error cases, duplicate detection, header level matching

**Implementation**: Auto-detect input type, concatenate files, regex parsing, comprehensive error handling
