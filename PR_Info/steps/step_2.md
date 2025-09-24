# Step 2: Move Implementation Prompt Template

## Objective
Move the Implementation Prompt Template from DEVELOPMENT_PROCESS.md to prompts.md to avoid duplication and enable get_prompt() access.

## WHERE
- `src/mcp_coder/prompts/prompts.md` - Add new prompt section
- `PR_Info/DEVELOPMENT_PROCESS.md` - Replace prompt text with link

## WHAT
### Main Functions
- No new functions - using existing `get_prompt()` functionality
- Text extraction and replacement operations

## HOW
### Integration Points
- Leverage existing `prompt_manager.get_prompt()` system
- Follow existing prompt format in prompts.md
- Maintain link reference in original location

## ALGORITHM
```
1. Extract "Implementation Prompt Template using task tracker" text from DEVELOPMENT_PROCESS.md
2. Add as new prompt section in src/mcp_coder/prompts/prompts.md  
3. Replace original prompt text with reference link
4. Verify prompt is accessible via get_prompt()
5. Keep original document structure intact
```

## DATA
### Input/Output
- **Extract**: Multi-line prompt text from DEVELOPMENT_PROCESS.md
- **Add**: New prompt section in prompts.md with proper markdown formatting
- **Replace**: Original prompt location with simple link reference
- **Return**: Accessible prompt via `get_prompt("mcp_coder/prompts/prompts.md", "Implementation Prompt Template using task tracker")`

## Implementation Notes
- Use exact prompt header name for get_prompt() compatibility
- Maintain markdown formatting and structure
- Preserve all prompt content without modification
- Keep link reference clear in DEVELOPMENT_PROCESS.md

## LLM Prompt
```
Please look at pr_info/steps/summary.md and implement Step 2.

Extract the "Implementation Prompt Template using task tracker" from PR_Info/DEVELOPMENT_PROCESS.md and:
1. Add it to src/mcp_coder/prompts/prompts.md as a new prompt section
2. Replace the original text in DEVELOPMENT_PROCESS.md with a link reference
3. Ensure the prompt follows the correct format for get_prompt() usage
4. Verify the prompt is accessible via get_prompt()

Keep the exact prompt content unchanged - just move it to avoid duplication.
```
