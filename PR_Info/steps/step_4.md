# Step 4: Update Help System

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md, implement Step 4: Update the help system to include the new prompt command.

Update the help command to include:
- Prompt command in commands list
- Usage examples for prompt command
- Consistent formatting with existing commands

Follow the patterns in src/mcp_coder/cli/commands/help.py and ensure all help text is updated consistently.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/help.py`
- **Functions**: `get_help_text()`, `get_usage_examples()`

## WHAT
- **Help Text Update**: Add prompt command to COMMANDS section
- **Examples Update**: Add prompt usage examples
- **Consistency Check**: Ensure formatting matches existing commands

## HOW
- **Commands Section**: Add `prompt <text>              Execute prompt via Claude CLI`
- **Examples Section**: Add practical prompt examples
- **Integration**: Maintain existing help structure and formatting

## ALGORITHM
```
1. Add prompt command to COMMANDS section
2. Add 2-3 practical examples to EXAMPLES section
3. Ensure consistent spacing and formatting
4. Verify help text includes all commands
5. Test help output for completeness
```

## DATA
- **Commands Addition**: `"prompt <text>              Execute prompt via Claude CLI"`
- **Examples**: 
  - `"mcp-coder prompt 'What is Python?'"`
  - `"mcp-coder prompt 'Explain async/await'"`
- **Format**: Consistent with existing command descriptions
- **Output**: Updated help text string with prompt command included
