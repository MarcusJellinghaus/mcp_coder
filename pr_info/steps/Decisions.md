# Decisions

## Plan update after implementation block (Jenkins Executor #2301)

1. **Drop the ruff version check from Step 1.** The `uvx ruff@latest version` comparison,
   the tool-env upgrade and the `.blocked.txt` fallback are removed — they need Bash, which
   the implementation session doesn't have. The reformat uses the ruff bundled with
   mcp-tools-py. CI's `ruff-format` row is the version-drift guard: if it fails after the
   reformat, upgrade ruff in mcp-tools-py and re-run `run_format_code`.
   (Marcus: "mcp coder installs mcp-tools-py, and they come with ruff — I think we can drop
   the version check"; confirmed "yes, apply both".)

2. **Move `mcp_coder verify` out of Step 1's required checks.** It is a shell-only command;
   `run_format_code(check_only=True)` already exercises formatter resolution. It stays as a
   manual check for Marcus after the PR is up. (Marcus: "yes, apply both".)
