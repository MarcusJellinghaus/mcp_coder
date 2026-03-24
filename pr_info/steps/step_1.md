# Step 1: Define Data Structure and Compact Help Output

> **Reference**: See `pr_info/steps/summary.md` for overall design.

## Goal

Define the shared command metadata as structured data and implement `get_compact_help_text()`. Update tests first (TDD).

## WHERE

- `src/mcp_coder/cli/commands/help.py`
- `tests/cli/commands/test_help.py`

## WHAT

### Data types (NamedTuples)

```python
from typing import NamedTuple

class Command(NamedTuple):
    name: str          # e.g. "commit auto"
    description: str   # e.g. "Auto-generate commit message"

class Category(NamedTuple):
    name: str          # e.g. "SETUP"
    description: str   # e.g. "Configure your project and verify the environment."
    commands: list[Command]
```

### Module-level data

```python
COMMAND_CATEGORIES: list[Category] = [
    Category(
        name="SETUP",
        description="Configure your project and verify the environment.",
        commands=[
            Command("init", "Create default configuration file"),
            Command("verify", "Verify CLI installation and configuration"),
            Command("define-labels", "Sync workflow status labels to GitHub"),
        ],
    ),
    Category(
        name="BACKGROUND DEVELOPMENT",
        description="Plan, implement, and create PRs for GitHub issues.",
        commands=[
            Command("create-plan", "Generate implementation plan for a GitHub issue"),
            Command("implement", "Execute implementation workflow"),
            Command("create-pr", "Create pull request with AI-generated summary"),
        ],
    ),
    Category(
        name="COORDINATION",
        description="Orchestrate workflows across repositories.",
        commands=[
            Command("coordinator test", "Trigger integration test"),
            Command("coordinator run", "Monitor and dispatch workflows"),
            Command("coordinator vscodeclaude", "Manage VSCode/Claude sessions"),
            Command("coordinator vscodeclaude status", "Show issue and VSCode/Claude session status"),
            Command("coordinator issue-stats", "Display issue statistics"),
        ],
    ),
    Category(
        name="TOOLS",
        description="Day-to-day development utilities.",
        commands=[
            Command("prompt", "Execute prompt via Claude API"),
            Command("commit auto", "Auto-generate commit message"),
            Command("commit clipboard", "Use clipboard commit message"),
            Command("set-status", "Update GitHub issue workflow status label"),
            Command("check branch-status", "Check branch readiness status"),
            Command("check file-size", "Check file sizes against maximum"),
            Command("gh-tool get-base-branch", "Detect base branch for feature branch"),
            Command("git-tool compact-diff", "Generate compact diff"),
        ],
    ),
]
```

### New function

```python
def get_compact_help_text() -> str:
    """Render compact help: category headers + aligned commands."""
```

## ALGORITHM (get_compact_help_text)

```
max_width = max command name length across all categories
lines = ["mcp-coder - AI-powered software development automation toolkit", "", "Usage: mcp-coder <command> [options]"]
for each category:
    lines += [blank, category.name]
    for each command:
        lines += [f"  {name:<{max_width}}  {description}"]
lines += [blank, "Run 'mcp-coder help' for detailed usage."]
lines += ["Run 'mcp-coder <command> --help' for command-specific options."]
return "\n".join(lines)
```

## DATA

- `COMMAND_CATEGORIES`: `list[Category]` — module-level constant
- `get_compact_help_text()` returns `str` — the formatted compact help text

## HOW (Integration)

- `Command` and `Category` are added as top-level types in `help.py`
- `COMMAND_CATEGORIES` is a module-level constant in `help.py`
- No imports change yet in `main.py` (that's step 3)

## Tests to Write First

In `tests/cli/commands/test_help.py`, add:

1. **`test_command_categories_contains_all_commands`** — verify `COMMAND_CATEGORIES` has 4 categories, check all expected command names are present
2. **`test_compact_help_has_all_category_headers`** — output contains "SETUP", "BACKGROUND DEVELOPMENT", "COORDINATION", "TOOLS"
3. **`test_compact_help_has_all_commands`** — output contains every command name from `COMMAND_CATEGORIES`
4. **`test_compact_help_no_category_descriptions`** — output does NOT contain category description strings
5. **`test_compact_help_column_alignment`** — all description columns start at the same position
6. **`test_compact_help_has_usage_line`** — contains "Usage: mcp-coder <command> [options]"
7. **`test_compact_help_has_footer`** — contains "Run 'mcp-coder help' for detailed usage."

## LLM Prompt

```
Implement Step 1 of issue #565 (see pr_info/steps/summary.md and pr_info/steps/step_1.md).

TDD approach:
1. Read the current test_help.py and help.py files
2. Write new tests in test_help.py for the data structure and get_compact_help_text()
3. Add Command/Category NamedTuples, CATEGORIES data, and get_compact_help_text() to help.py
4. Run all three code quality checks (pylint, pytest, mypy) and fix any issues
5. Commit when all checks pass

Do NOT modify main.py or remove existing functions yet — that happens in later steps.
```
