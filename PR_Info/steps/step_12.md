# Step 12: Update Help System for All Features

## LLM Prompt
```
Based on the summary in PR_Info/steps/summary.md, implement Step 12: Update the help system to include the complete prompt command with all features.

Update the help command to include:
- Prompt command description with all verbosity levels and storage options
- Multiple usage examples showing different parameter combinations
- Clear explanations of verbosity levels and storage functionality
- Consistent formatting with existing commands

This is the final step to complete the prompt command implementation with full documentation.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/help.py`
- **Functions**: `get_help_text()`, `get_usage_examples()`

## WHAT
- **Enhanced Help Text**: Add complete prompt command description with all features
- **Multiple Examples**: Show various usage patterns with different parameters
- **Feature Documentation**: Explain verbosity levels and storage capabilities
- **Consistent Formatting**: Maintain existing help text structure and style

## HOW
- **Commands Section**: Add comprehensive prompt command description
- **Examples Section**: Add 4-5 practical examples showing different feature combinations
- **Verbosity Explanation**: Document the three verbosity levels (just-text, verbose, raw)
- **Storage Documentation**: Explain storage and continuation functionality

## ALGORITHM
```
1. Add prompt command to COMMANDS section with complete feature description
2. Add multiple examples to EXAMPLES section:
   - Basic prompt usage (default just-text)
   - Verbose output example
   - Raw debug output example
   - Storage and continuation examples
3. Ensure consistent spacing and formatting with existing commands
4. Include brief explanations of key features inline with examples
```

## DATA
- **Commands Addition**: 
  ```
  "prompt <text>              Execute prompt via Claude API with configurable debug output
                             Supports --verbosity, --store-response, --continue-from"
  ```
- **Examples**:
  - `"mcp-coder prompt 'What is Python?'"` (basic usage - just-text default)
  - `"mcp-coder prompt 'Explain async/await' --verbosity=verbose"` (detailed debug)
  - `"mcp-coder prompt 'Debug this error' --verbosity=raw --store-response"` (complete debug + storage)
  - `"mcp-coder prompt 'Follow up question' --continue-from response_2025-09-18T14-30-22.json"` (continuation)
- **Feature Descriptions**: Brief inline explanations of verbosity levels and storage
- **Format**: Consistent with existing command documentation style
