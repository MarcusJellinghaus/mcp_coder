# Step 2: Package Integration and Prompt File Creation

## WHERE
- **Prompt file**: `src/mcp_coder/prompts/prompts.md`
- **Package exports**: `src/mcp_coder/__init__.py`
- **Configuration**: `pyproject.toml` (package data)

## WHAT
Create comprehensive prompt file and integrate into package:

**Comprehensive prompt file** (`prompts.md`):
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

## Documentation Section

This file contains prompts for the mcp-coder project...
[Additional documentation, experiences, notes, etc.]

# Another Prompt
```
Example of another prompt...
```
```

**Package integration**:
```python
# In src/mcp_coder/__init__.py
from .prompt_manager import get_prompt, validate_prompt_markdown, validate_prompt_directory
```

## HOW
- Create comprehensive `prompts.md` with documentation and prompts
- Update package exports in `__init__.py`
- Configure package data in `pyproject.toml`
- Test file path functionality with real prompt file
- Verify wildcard and directory functionality

## ALGORITHM
```
1. Create src/mcp_coder/prompts/ directory
2. Create comprehensive prompts.md with mixed content
3. Update __init__.py to export all three functions
4. Configure package data in pyproject.toml
5. Test file path, directory, and wildcard functionality
6. Verify package imports work correctly
7. Test validation functions with real prompt file
```

## DATA
**Created files**:
- `src/mcp_coder/prompts/prompts.md` - comprehensive documentation + prompts
- Updated `src/mcp_coder/__init__.py` - package exports
- Updated `pyproject.toml` - package data configuration

**Test coverage**: File paths, directories, wildcards, package imports, real file validation

---

## LLM Prompt for Step 2

You are implementing a prompt manager for the mcp-coder project.

**Context**: Read the summary at `pr_info/steps/summary.md` and decisions at `pr_info/steps/Decisions.md`. Step 1 should be complete with working core functions.

**Current Step**: Create comprehensive prompt file and integrate into package.

**Task**: 
1. Create `src/mcp_coder/prompts/prompts.md` as comprehensive documentation + prompts file
2. Update `src/mcp_coder/__init__.py` to export all three functions
3. Configure package data in `pyproject.toml`
4. Test file path, directory, and wildcard functionality with real files

**Requirements**:
- Create a lengthy markdown file with prompts, documentation, experiences mixed together
- Use various header levels (`#`, `##`, `###`, `####`) for structure
- Include actual prompts in code blocks after headers
- Test that `from mcp_coder import get_prompt` works
- Verify wildcard patterns like `prompts/*` and directory paths work
- Test validation functions with the real prompt file

**Key point**: This creates the actual prompt file and integrates the package for real-world use

**Test**: Verify file paths, directories, wildcards, package imports all work with real prompt file
