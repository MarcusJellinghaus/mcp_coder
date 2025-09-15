# MCP Coder Prompt Manager

Store and retrieve prompts from markdown files.

## Quick Start

```python
from mcp_coder import get_prompt

# Get a prompt
prompt = get_prompt("prompts.md", "Header Name")
print(prompt)
```

## File Format

Prompts use this structure:

```markdown
# Prompt Name
```
Your prompt content here.
Multiple lines supported.
```
```

## Usage

```python
# From file
get_prompt("file.md", "Prompt Name")

# From directory (searches all .md files)
get_prompt("prompts/", "Prompt Name")

# Wildcard pattern
get_prompt("prompts/*.md", "Prompt Name")
```

## Validation

```python
from mcp_coder import validate_prompt_markdown, validate_prompt_directory

# Validate file
result = validate_prompt_markdown("prompts.md")
print(f"Valid: {result['valid']}, Headers: {len(result['headers'])}")

# Validate directory
result = validate_prompt_directory("prompts/")
print(f"Files checked: {result['files_checked']}")
```

## Rules

- Headers must be followed by code blocks
- Header names must be unique across files
- Any header level works (#, ##, ###, etc.)
- Case-sensitive matching
