# My Prompts

This file contains your personal prompts for the mcp-coder project.

## Getting Started

Add your prompts below using the format shown in `prompt_instructions.md`.

### Development Notes

You can mix documentation and prompts in this file. Only headers followed by code blocks will be treated as prompts.

# My Prompt Title
```
My lengthy explanation of what this prompt does and when to use it.

Provide clear instructions here.
Include examples if helpful.
Use placeholders like [Insert code here] for variable content.

Expected output format: [describe the expected response]
```

# Git Commit Message Generation
```
Analyze the provided git diff and status information to generate a concise, professional commit message following conventional commit format.

REQUIREMENTS:
1. Keep commit summary BRIEF - aim for under 50 characters when possible
2. Use conventional commit format: type(scope): description
   - Types: feat, fix, docs, style, refactor, test, chore, build, ci
   - Scope is optional but helpful for context
   - Description should be imperative mood ("add" not "adds" or "added")
3. Focus on WHAT changed, not implementation details
4. Only include body text if essential for context (1-2 sentences max)
5. Analyze both staged and unstaged changes if provided

ANALYSIS STEPS:
1. Review git status to understand file changes (new, modified, deleted)
2. Examine git diff to understand the nature of changes
3. Identify the primary purpose/type of the changes
4. Determine appropriate scope if multiple areas are affected
5. Craft a clear, concise description

OUTPUT FORMAT:
Provide the commit message in plain text format ready to use:

feat(auth): add user validation

Optional body text here if needed for context.

EXAMPLES:
- feat: add user authentication system
- fix(api): resolve null pointer in validation
- docs: update installation instructions
- refactor(db): simplify connection handling
- test: add unit tests for user service
- chore: update dependencies to latest versions

Expected output: A properly formatted conventional commit message ready to use with git commit.

Do not provide anything else - just the commit message!
```
