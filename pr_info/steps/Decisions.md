# Decisions

## 1. Merge Steps 1 and 2 into a single step

Steps 1 (handler + unit tests) and 2 (parser + dispatch + integration tests) were merged into a single Step 1. The handler and its wiring are tightly coupled — splitting them across commits adds no value.

## 2. Guard against `number == 0` from `get_issue()`

Added an explicit guard in the algorithm: after calling `IssueManager.get_issue()`, check if `issue_data["number"] == 0` and return exit code 1 with an error message. This handles the case where an issue is not found (the manager returns a default dict with `number=0`).

## 3. Settings wildcard permission for `gh-tool`

The settings update should change the existing specific permission `"Bash(mcp-coder gh-tool get-base-branch)"` to a wildcard `"Bash(mcp-coder gh-tool:*)"`, matching the existing `git-tool` pattern. This covers all current and future `gh-tool` subcommands with a single entry.
