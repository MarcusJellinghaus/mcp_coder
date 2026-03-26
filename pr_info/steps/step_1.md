# Step 1: Update Help Categories

## Context
See `pr_info/steps/summary.md` for full issue context and architecture overview.

## Goal
Update `COMMAND_CATEGORIES` in `help.py` to reflect the new command structure. This is self-contained — help.py is just data, decoupled from parsers/routing.

## LLM Prompt
```
Implement Step 1 of issue #570 (CLI restructure). Read pr_info/steps/summary.md for context, then read pr_info/steps/step_1.md for detailed instructions. Update the help categories and their tests. Do not modify any other files. Run all code quality checks after changes.
```

## WHERE
- `src/mcp_coder/cli/commands/help.py` — modify COMMAND_CATEGORIES
- `tests/cli/commands/test_help.py` — update test expectations

## WHAT

### help.py — Update `COMMAND_CATEGORIES`

**Old structure** (4 categories):
- SETUP: init, verify, define-labels
- BACKGROUND DEVELOPMENT: create-plan, implement, create-pr
- COORDINATION: coordinator test, coordinator run, coordinator vscodeclaude, coordinator vscodeclaude status, coordinator issue-stats
- TOOLS: prompt, commit auto/clipboard, set-status, check branch-status/file-size, gh-tool get-base-branch, git-tool compact-diff

**New structure** (4 categories, per issue):
- SETUP: init, verify
- BACKGROUND DEVELOPMENT: create-plan, implement, create-pr, coordinator
- INTERACTIVE DEVELOPMENT: vscodeclaude launch, vscodeclaude status
- TOOLS: prompt, commit auto/clipboard, set-status, check branch-status/file-size, gh-tool define-labels/issue-stats/get-base-branch, git-tool compact-diff, help

### test_help.py — Update expectations

1. `test_command_categories_contains_all_commands`:
   - Change expected count from 4 categories to 4 (same count, different names)
   - Update `expected_commands` list to match new structure
   - Remove: `define-labels`, `coordinator test`, `coordinator run`, `coordinator vscodeclaude`, `coordinator vscodeclaude status`, `coordinator issue-stats`
   - Add: `coordinator`, `vscodeclaude launch`, `vscodeclaude status`, `gh-tool define-labels`, `gh-tool issue-stats`, `help`

2. `test_compact_help_has_all_category_headers`:
   - Replace `"COORDINATION"` with `"INTERACTIVE DEVELOPMENT"`

3. `test_detailed_help_has_all_category_headers`:
   - Same replacement

## HOW
Direct edits to the `COMMAND_CATEGORIES` list and test assertions. No imports change.

## DATA

New `COMMAND_CATEGORIES` value:
```python
COMMAND_CATEGORIES: list[Category] = [
    Category(
        name="SETUP",
        description="Configure your project and verify the environment.",
        commands=[
            Command("init", "Create default configuration file"),
            Command("verify", "Verify CLI installation and configuration"),
        ],
    ),
    Category(
        name="BACKGROUND DEVELOPMENT",
        description="Plan, implement, and create PRs for GitHub issues.",
        commands=[
            Command("create-plan", "Generate implementation plan for a GitHub issue"),
            Command("implement", "Execute implementation workflow"),
            Command("create-pr", "Create pull request with AI-generated summary"),
            Command("coordinator", "Monitor and dispatch workflows across repositories"),
        ],
    ),
    Category(
        name="INTERACTIVE DEVELOPMENT",
        description="Manage local workspaces and VSCode sessions.",
        commands=[
            Command("vscodeclaude launch", "Launch VSCode/Claude session for issues"),
            Command("vscodeclaude status", "Show current VSCode/Claude sessions"),
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
            Command("gh-tool define-labels", "Sync workflow status labels to GitHub"),
            Command("gh-tool issue-stats", "Display issue statistics"),
            Command("gh-tool get-base-branch", "Detect base branch for feature branch"),
            Command("git-tool compact-diff", "Generate compact diff"),
            Command("help", "Show help information"),
        ],
    ),
]
```
