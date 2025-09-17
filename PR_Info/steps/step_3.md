# Step 3: Create Commit Message Generation Prompt

## Objective
Add the LLM prompt template for commit message generation to the existing prompts system.

## LLM Prompt
```
Based on the MCP Coder CLI Implementation Summary and previous steps, implement Step 3: Create the commit message generation prompt.

Requirements:
- Add commit prompt to src/mcp_coder/prompts/prompts.md
- Base the prompt on the existing tools/commit_summary.bat logic
- Use the existing prompt format from prompts.md
- Focus on generating concise, conventional commit messages
- Include instructions for handling git diff analysis

The prompt should analyze git diffs and generate commit messages following conventional commit format.
```

## WHERE (File Structure)
```
src/mcp_coder/prompts/prompts.md (updated)
```

## WHAT (Content Addition)

### Prompt Template Structure
```markdown
# Git Commit Message Generation
```
[Detailed prompt content based on commit_summary.bat]
```

## HOW (Integration Points)

### Prompt Format (following existing pattern)
```markdown
# Git Commit Message Generation
```
[Prompt content here following the existing format in prompts.md]
```

### Integration with existing prompt_manager.py
- Uses existing `get_prompt()` function
- Prompt name: "Git Commit Message Generation"
- No code changes needed - leverages existing infrastructure

## ALGORITHM (Prompt Logic)
```
1. Analyze provided git diff (staged, unstaged, untracked files)
2. Identify main changes and their scope/type
3. Generate conventional commit format: type(scope): description
4. Keep commit summary under 50 characters when possible
5. Add body only if essential for context (1-2 sentences max)
6. Focus on WHAT changed, not implementation details
```

## DATA (Prompt Output Format)

### Expected LLM Response Format
```
feat: add user authentication

Implements login/logout functionality with JWT tokens.
```

OR for simple changes:
```
fix: resolve null pointer in user validation
```

### Prompt Input Format
- Git status information
- Comprehensive diff (staged + unstaged + untracked)
- Context about repository state

## Tests Required

### `tests/test_prompts.py` (additions)
```python
def test_commit_prompt_exists():
    """Test commit message generation prompt exists and is loadable."""

def test_commit_prompt_format():
    """Test commit prompt follows expected format."""

def test_commit_prompt_content():
    """Test commit prompt contains key instructions."""
```

## Prompt Content Requirements

### Must Include:
1. **Diff Analysis**: Instructions to analyze git diff output
2. **Format Requirements**: Conventional commit format guidance
3. **Length Limits**: 50 char summary, 72 char body lines
4. **Type Classification**: feat, fix, docs, style, refactor, test, chore
5. **Scope Guidance**: When and how to include scope
6. **Body Guidelines**: When to include body text

### Must Avoid:
1. Implementation details in commit message
2. Overly verbose descriptions
3. Multiple changes in single commit message
4. Non-standard commit formats

## Example Prompt Scenarios

### Input: New feature with tests
```
=== STAGED CHANGES ===
A  src/auth/login.py
A  tests/test_auth.py
M  src/main.py
```

### Expected Output:
```
feat(auth): add user login functionality

Implements JWT-based authentication with login endpoint and tests.
```

## Acceptance Criteria
1. ✅ Prompt added to prompts.md following existing format
2. ✅ Prompt content based on commit_summary.bat logic
3. ✅ Instructions for conventional commit format
4. ✅ Git diff analysis guidance included
5. ✅ Prompt is loadable via existing get_prompt() function
6. ✅ All tests pass
7. ✅ Prompt generates appropriate commit messages for various scenarios
