# Step 3: Add Documentation to CONFIG.md

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 3.

Task: Add a "Dependency Architecture for Automated Workflows" section to docs/configuration/CONFIG.md explaining the two-environment model and type stub requirements.

Reference: pr_info/steps/step_3.md for detailed specifications.
```

## Overview

Add documentation explaining the two-environment architecture and why type stubs must be installed separately in the project environment for mypy to work correctly.

## WHERE

| File | Action |
|------|--------|
| `docs/configuration/CONFIG.md` | Add new section before "Troubleshooting" |

## WHAT

### New Section Content

Add the following section to `docs/configuration/CONFIG.md` before the "Troubleshooting" section:

```markdown
## Dependency Architecture for Automated Workflows

When using mcp-coder in automated Jenkins workflows, there are two separate Python environments:

### Two-Environment Model

```
┌─────────────────────────────────────────────────────────────┐
│  Execution Environment (VENV_BASE_DIR/.venv)                │
│  Pre-provisioned: mcp-coder, mcp-code-checker,              │
│  mcp-server-filesystem, claude CLI, pytest, mypy, pylint    │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ 1. uv sync --extra types (in repo/)
                           │ 2. mcp-coder implement
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Project Environment (repo/.venv)                           │
│  Per-run: project dependencies + type stubs                 │
└─────────────────────────────────────────────────────────────┘
```

### Why Type Stubs Need Separate Installation

The MCP code-checker runs mypy against **project code** using the **project's virtual environment**. For mypy to resolve types correctly, type stub packages (e.g., `types-requests`, `types-pyperclip`) must be installed in the project's `.venv`, not the execution environment.

The coordinator command templates automatically run `uv sync --extra types` in the project directory before executing mcp-coder commands.

### Configuring Your Project for Automated Workflows

If your project uses mcp-coder workflows, define a `types` extra in your `pyproject.toml`:

```toml
[project.optional-dependencies]
# Type stubs required for mypy in automated workflows
types = [
    "types-requests>=2.28.0",
    # Add other type stubs your project needs
]

# Full dev setup for local development
dev = [
    "your-project[types]",
    # Other dev dependencies...
]
```

This ensures:
- Automated workflows install only type stubs (`uv sync --extra types`)
- Local development installs everything (`pip install -e ".[dev]"`)
```

## HOW

1. Open `docs/configuration/CONFIG.md`
2. Find the "## Troubleshooting" section
3. Insert the new "## Dependency Architecture for Automated Workflows" section **before** Troubleshooting
4. Ensure proper markdown formatting with blank lines between sections

## Insertion Point

The section should be inserted after "## Usage Examples" / cache configuration content and before "## Troubleshooting".

Look for this pattern:
```markdown
...existing content about cache configuration...

## Troubleshooting
```

Insert the new section so it becomes:
```markdown
...existing content about cache configuration...

## Dependency Architecture for Automated Workflows

...new content...

## Troubleshooting
```

## DATA

### Section Structure

| Subsection | Purpose |
|------------|---------|
| Two-Environment Model | ASCII diagram showing the architecture |
| Why Type Stubs Need Separate Installation | Explanation of the problem |
| Configuring Your Project | Guidance for other projects |

## Verification

1. **Markdown lint**: Ensure proper heading hierarchy (## for main section, ### for subsections)
2. **Link check**: No external links added, no verification needed
3. **Manual review**: Read through to ensure clarity and accuracy

## Notes

- Keep the documentation concise - this is reference documentation, not a tutorial
- The ASCII diagram matches the one in the issue description for consistency
- The example `pyproject.toml` shows a generic project pattern, not mcp-coder specifically
