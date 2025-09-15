# Step 3: Documentation and Final Validation

## WHERE
- **Documentation**: Enhanced docstrings and usage examples
- **Validation**: Comprehensive quality checks and testing
- **Final integration**: End-to-end functionality verification

## WHAT
**Enhanced documentation and comprehensive validation**:

1. **Comprehensive docstrings** with practical examples:
   ```python
   def get_prompt(source: str, header: str) -> str:
       """Get prompt from markdown source.
       
       Args:
           source: File path, directory, wildcard pattern, or markdown content
           header: Header name to search for (any level: #, ##, ###, ####)
           
       Examples:
           # From string content
           prompt = get_prompt('# Test\n```\nHello\n```', 'Test')
           
           # From file
           prompt = get_prompt('prompts/prompts.md', 'Short Commit')
           
           # From directory (all .md files)
           prompt = get_prompt('prompts/', 'Short Commit')
           
           # From wildcard
           prompt = get_prompt('prompts/*.md', 'Short Commit')
       """
   ```

2. **Usage documentation** including markdown format requirements
3. **Error handling examples** and troubleshooting guidance

## HOW
- Add comprehensive docstrings with practical usage examples
- Document markdown format requirements and expectations
- Include error handling examples for common issues
- Run complete quality checks (pylint, pytest, mypy)
- Verify end-to-end functionality with real prompt files
- Test package imports and exports work correctly

## ALGORITHM
```
1. Add comprehensive docstrings to all functions
2. Include practical usage examples in documentation
3. Document markdown format requirements
4. Add error handling examples and troubleshooting
5. Run complete quality checks (pylint, pytest, mypy)
6. Test end-to-end functionality with real files
7. Verify package imports work: `from mcp_coder import get_prompt`
8. Test all input types: string content, files, directories, wildcards
9. Validate cross-file duplicate detection works
10. Confirm error messages are clear and actionable
```

## DATA
**Final deliverable**: Production-ready prompt manager with comprehensive documentation

**Key features**:
- Works with string content, file paths, directories, and wildcards
- Clear error messages with file locations and line numbers
- Cross-file duplicate detection using virtual concatenation
- Detailed validation results for troubleshooting
- Comprehensive documentation with usage examples
- Full package integration and exports

**Quality assurance**: All checks pass (pylint, pytest, mypy), comprehensive test coverage

---

## LLM Prompt for Step 3

You are implementing a prompt manager for the mcp-coder project.

**Context**: Read the summary at `pr_info/steps/summary.md` and decisions at `pr_info/steps/Decisions.md`. Steps 1-2 should be complete with working core functions and package integration.

**Current Step**: Add comprehensive documentation and run final validation.

**Task**: 
1. Add comprehensive docstrings with practical usage examples to all functions
2. Document markdown format requirements and error handling patterns
3. Run complete quality checks (pylint, pytest, mypy) and fix any issues
4. Test end-to-end functionality with real prompt files
5. Verify all input types work correctly (string content, files, directories, wildcards)

**Requirements**:
- Include practical examples in docstrings showing different input types
- Document the expected markdown format (headers + code blocks)
- Show error handling examples for common issues
- Ensure all quality checks pass without issues
- Test cross-file duplicate detection with multiple prompt files
- Verify package imports work: `from mcp_coder import get_prompt, validate_prompt_markdown, validate_prompt_directory`
- Confirm error messages are clear and actionable

**Success criteria**: Production-ready prompt manager with excellent documentation, passing all quality checks, and comprehensive functionality.
