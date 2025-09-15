# Step 3: Complete Setup (Package Config + Exports)

## WHERE
- **Configuration**: `pyproject.toml` (only if using real files)
- **Package exports**: `src/mcp_coder/__init__.py`

## WHAT
**Complete the remaining setup tasks** following the detailed instructions that will be included in the `prompt_manager.py` file:

1. **Package configuration** (only if using real prompt files):
   ```toml
   [tool.setuptools.package-data]
   "mcp_coder" = ["prompts/*.md"]
   ```

2. **Export functions** - Add to `src/mcp_coder/__init__.py`:
   ```python
   from .prompt_manager import get_prompt, validate_prompt_markdown
   ```

## HOW
- Follow the detailed setup instructions in `prompt_manager.py`
- The implementation file will contain complete step-by-step guidance
- Package config only needed if using real files (not just memory streams)
- Test that everything works after setup

## ALGORITHM
```
1. Read setup instructions in prompt_manager.py
2. Update __init__.py for exports (always needed)
3. Update pyproject.toml for package data (only if using files)
4. Test final integration works
5. Run tests to verify everything passes
```

## DATA
**Final deliverable**: Complete, working prompt manager system ready for use
**Key feature**: Works with memory streams (no files needed) OR real files

---

## LLM Prompt for Step 3

You are implementing a prompt manager for the mcp-coder project.

**Context**: Read the summary at `pr_info/steps/summary.md`. Steps 1-2 should be complete with working prompt manager that handles both memory streams and optionally files.

**Current Step**: Complete the final setup by following instructions in the prompt_manager.py file.

**Task**: The `prompt_manager.py` file will contain detailed instructions for:
1. Updating `src/mcp_coder/__init__.py` to export the prompt manager functions
2. Optionally updating `pyproject.toml` (only if using real prompt files)
3. Final testing and validation

**Requirements**:
- Follow the step-by-step instructions that will be included in `prompt_manager.py`
- Always update exports in `__init__.py`
- Package configuration only needed if using real files (not memory streams)
- Test that the complete system works: `from mcp_coder import get_prompt`

**Success criteria**: The prompt manager works with both memory streams and files, integrated into the package.
