# Step 6: Update Documentation

## LLM Prompt
```
Update documentation to reflect the new --continue parameter using the simplified approach. Update README.md, CLI argument help text, and simplified help.py without examples.

Reference: PR_Info/steps/summary.md and PR_Info/steps/Decisions.md - implementing --continue parameter for mcp-coder prompt command.

This is step 6 of 7: Documentation updates using the refactored help system from step 1.
```

## WHERE
- **File 1**: `README.md` - Update examples section
- **File 2**: `src/mcp_coder/cli/main.py` - Update argument help text
- **File 3**: `src/mcp_coder/cli/commands/help.py` - Update simplified help text (no examples)

## WHAT
**Documentation sections to update**:
```python
# README.md: Add usage examples to existing examples section
# main.py: Clear, descriptive argument help text
# help.py: Update get_help_text() to mention new parameter (no examples per Decision #3)
```

## HOW
- **Consistency**: Follow existing documentation patterns and style
- **Examples**: Add practical examples to README only (Decision #3)
- **Context**: Explain when to use `--continue` vs `--continue-from`
- **Simplicity**: Use refactored help system from Step 1

## ALGORITHM
```
1. UPDATE README.md examples section with new parameter usage
2. UPDATE CLI argument help text for clarity and user guidance
3. UPDATE simplified get_help_text() to mention new parameter (no examples)
4. ENSURE consistency across all documentation
5. VERIFY help system works with refactored structure
```

## DATA
**README.md Addition**:
```markdown
# Session storage and continuation examples:
mcp-coder prompt "Start project planning" --store-response
mcp-coder prompt "What's next?" --continue-from response_2025-09-19T14-30-22.json
mcp-coder prompt "What's next?" --continue  # Auto-finds latest session
```

**main.py Help Text**:
```python
continue_group.add_argument(
    "--continue",
    action="store_true", 
    help="Continue from the most recent stored session (automatically finds latest response file)"
)
```

**help.py Updates** (simplified, no examples):
```python
# In get_help_text() - simple mention of new parameter
--continue-from FILE   Continue conversation from previous stored session
--continue             Continue from the most recent stored session
```

**Documentation Themes**:
- **Convenience**: Emphasize ease of use (no need to remember filenames)
- **Workflow**: Show how it fits into development workflows in README
- **Clarity**: Distinguish from `--continue-from` clearly
- **Requirements**: Mention need for existing response files
- **Simplicity**: Use refactored help system without examples (Decision #3)
