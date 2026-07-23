"""Single source of truth for CLI command descriptions and categories.

This module is intentionally dependency-free: it imports nothing from within
``mcp_coder.cli`` (only stdlib/typing). Both the categorized help overview
(``cli/commands/help.py``) and the individual subparsers
(``cli/parsers.py`` / ``cli/gh_parsers.py``) read from these constants, so a
command's description cannot drift between the two.
"""

from __future__ import annotations

# Display-name -> canonical description. Each leaf subparser passes
# ``help=COMMAND_DESCRIPTIONS["<display-name>"]`` so the overview text and the
# per-command ``--help`` text are the same string.
COMMAND_DESCRIPTIONS: dict[str, str] = {
    "init": "Initialize project: create config and deploy Claude skills",
    "verify": "Verify CLI installation, LLM provider, and MLflow configuration",
    "create-plan": "Generate implementation plan for a GitHub issue",
    "review-plan": "Run automated review of an implementation plan",
    "implement": "Execute implementation workflow",
    "rebase": "Automatically rebase the current branch onto its base branch",
    "review-implementation": "Run automated review of an implementation",
    "create-pr": "Create pull request with AI-generated summary",
    "coordinator": "Monitor GitHub issues and dispatch automated workflows",
    "icoder": "Interactive terminal chat for LLM-assisted coding",
    "vscodeclaude launch": "Launch VSCode/Claude session for issues",
    "vscodeclaude status": "Show current VSCode/Claude sessions",
    "prompt": "Send prompt to configured LLM",
    "commit auto": "Auto-generate commit message using LLM",
    "check branch-status": "Check branch readiness status and optionally apply fixes",
    "check file-size": "Check file sizes against maximum line count",
    "gh-tool checkout-issue-branch": "Checkout or create a branch linked to a GitHub issue",
    "gh-tool set-status": "Update GitHub issue workflow status label",
    "gh-tool get-base-branch": "Detect base branch for current feature branch",
    "gh-tool define-labels": "Sync workflow status labels to GitHub",
    "gh-tool issue-stats": "Display issue statistics by workflow status",
    "git-tool compact-diff": "Generate compact git diff suppressing moved-code blocks",
}

# (category_title, ordered command names) - the single readable layout source.
COMMAND_CATEGORIES: list[tuple[str, list[str]]] = [
    ("SETUP", ["init", "verify"]),
    (
        "BACKGROUND DEVELOPMENT",
        [
            "create-plan",
            "review-plan",
            "implement",
            "rebase",
            "review-implementation",
            "create-pr",
            "coordinator",
        ],
    ),
    (
        "INTERACTIVE DEVELOPMENT",
        ["icoder", "vscodeclaude launch", "vscodeclaude status"],
    ),
    (
        "TOOLS",
        [
            "prompt",
            "commit auto",
            "check branch-status",
            "check file-size",
            "gh-tool checkout-issue-branch",
            "gh-tool set-status",
            "gh-tool get-base-branch",
            "gh-tool define-labels",
            "gh-tool issue-stats",
            "git-tool compact-diff",
        ],
    ),
]
