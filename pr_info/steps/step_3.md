# Step 3: Add PR Summary Prompt Template

## WHERE
- **Implementation**: `src/mcp_coder/prompts/prompts.md`

## WHAT
Add prompt template for generating pull request summaries from git diffs.

### Template Requirements
- Generate concise PR title (under 60 characters)
- Create structured PR body with sections
- Handle various types of changes (features, fixes, refactoring)
- Extract meaningful information from git diff

## HOW

### Integration Points
- **Existing File**: Add new section to prompts.md
- **Naming**: Use header "PR Summary Generation" for `get_prompt()` calls
- **Format**: Follow existing prompt template structure in file
- **Usage**: Will be called by `get_prompt(PROMPTS_FILE_PATH, "PR Summary Generation")`

### Template Structure
- Clear instructions for LLM
- Specify expected output format
- Handle edge cases (empty diffs, binary files)
- Consistent with existing prompt styles

## ALGORITHM (Pseudocode)
```
1. Analyze git diff for types of changes
2. Generate concise title summarizing main purpose
3. Create structured body with:
   - Summary section
   - Changes overview
   - Optional test plan
4. Format for direct GitHub PR usage
```

## LLM Prompt

### Context
You are implementing Step 3 of the Create Pull Request Workflow. Review the summary document in `pr_info/steps/summary.md` for full context. This step builds on Steps 1-2 (git diff and cleanup functions).

### Task
Add a new prompt template to `src/mcp_coder/prompts/prompts.md` for generating pull request summaries from git diffs.

### Requirements
1. **Study Existing Prompts**: Review current prompts in the file for:
   - Structure and formatting style
   - Instruction clarity and specificity
   - Output format specifications
   - Use of examples and guidelines
2. **Template Design**: Create prompt that:
   - Takes git diff as input
   - Generates PR title and body
   - Handles various change types (feat/fix/docs/refactor)
   - Produces GitHub-ready markdown format
3. **Output Format**: Specify exact format for parsing:
   - First line: PR title (no markdown header)
   - Remaining lines: PR body content
   - Clear separation for easy parsing
4. **Integration**: Ensure template works with existing `get_prompt()` function

### Expected Output
- New prompt template section in prompts.md
- Clear instructions for LLM behavior
- Specified output format for easy parsing
- Examples of expected title/body format

### Success Criteria
- Template follows existing file structure
- Clear, actionable instructions for LLM
- Produces consistently parseable output
- Handles edge cases (empty diff, large changes)