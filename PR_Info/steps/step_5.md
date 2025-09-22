# Step 5: Update Documentation

## LLM Prompt
```
Update all documentation to reflect the new --continue-from-last parameter. This includes README.md, CLI help command, and inline help text to provide comprehensive user guidance.

Reference: PR_Info/steps/summary.md - implementing --continue-from-last parameter for mcp-coder prompt command.

This is step 5 of 6: Documentation updates after implementing the feature.
```

## WHERE
- **File 1**: `README.md` - Update examples and API reference
- **File 2**: `src/mcp_coder/cli/commands/help.py` - Update help text and examples
- **File 3**: `src/mcp_coder/cli/main.py` - Update argument help text

## WHAT
**Documentation sections to update**:
```python
# README.md: Add to examples section
# help.py: Update get_help_text() and get_usage_examples()  
# main.py: Update argument help text
```

## HOW
- **Consistency**: Follow existing documentation patterns and style
- **Examples**: Add practical examples showing the new parameter usage
- **Context**: Explain when to use `--continue-from-last` vs `--continue-from`
- **Cross-references**: Ensure all documentation mentions are consistent

## ALGORITHM
```
1. UPDATE README.md examples section with new parameter
2. MODIFY help.py to include --continue-from-last in command description
3. ADD usage examples showing the new parameter
4. UPDATE CLI argument help text for clarity
5. ENSURE consistency across all documentation
```

## DATA
**README.md Addition**:
```markdown
# Session storage and continuation:
mcp-coder prompt "Start project planning" --store-response                      # Save session
mcp-coder prompt "What's next?" --continue-from response_2025-09-19T14-30-22.json # Continue from specific file
mcp-coder prompt "What's next?" --continue-from-last                            # Continue from most recent session
```

**help.py Updates**:
```python
# In get_help_text()
--continue-from FILE   Continue conversation from previous stored session
--continue-from-last   Continue from the most recent stored session
                      (automatically finds latest response file)

# In get_usage_examples()  
mcp-coder prompt "What's next?" --continue-from-last                            # Auto-continue from latest
```

**main.py Help Text**:
```python
continue_group.add_argument(
    "--continue-from-last",
    action="store_true", 
    help="Continue from the most recent stored session (auto-finds latest response file)"
)
```

**Documentation Themes**:
- **Convenience**: Emphasize ease of use (no need to remember filenames)
- **Workflow**: Show how it fits into development workflows  
- **Alternatives**: Clearly distinguish from `--continue-from`
- **Requirements**: Mention need for existing response files
