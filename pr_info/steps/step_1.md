# Step 1: Update Dependencies and Add Mypy Prompt

## WHERE
- File: `pyproject.toml`
- File: `src/mcp_coder/prompts/prompts.md`

## WHAT
Move `mcp-code-checker` dependency and add mypy fix prompt template.

### Changes Required:
1. **pyproject.toml**: Move `mcp-code-checker` from `[project.optional-dependencies.dev]` to `[project.dependencies]`
2. **prompts.md**: Add new prompt section "Mypy Fix Prompt"

## HOW
- **Dependency**: Move one line from dev to main dependencies
- **Prompt**: Add new section after existing prompts, before end of file

## ALGORITHM
```
1. Move mcp-code-checker from dev to main dependencies
2. Add mypy fix prompt template to prompts.md
3. Verify prompt can be loaded with get_prompt()
```

## DATA
- **Dependency line**: `"mcp-code-checker @ git+https://github.com/MarcusJellinghaus/mcp-code-checker.git"`
- **Prompt name**: "Mypy Fix Prompt"
- **Prompt content**: Instructions to fix mypy type errors

## LLM Prompt for This Step

```
Reference: pr_info/steps/summary.md

Implement Step 1: Update dependencies and add mypy prompt template.

TASKS:
1. Move mcp-code-checker from dev dependencies to main dependencies in pyproject.toml
2. Add a simple "Mypy Fix Prompt" section to src/mcp_coder/prompts/prompts.md

The mypy prompt should:
- Instruct LLM to fix type errors shown in mypy output
- Be concise and focused on type fixing only
- Follow the existing prompt format in prompts.md

Keep it minimal - just move the dependency and add the prompt template.
```
