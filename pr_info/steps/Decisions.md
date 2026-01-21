# Decisions Log

## Discussion Date: 2026-01-21

### Decision 1: Slash Command `allowed-tools` Syntax
**Question:** Which syntax to use for the `allowed-tools` frontmatter in slash commands?
**Decision:** Keep as planned: `Bash(mcp-coder set-status:*)`

### Decision 2: Label Validation Scope
**Question:** Should we validate labels against local config only or make a GitHub API call?
**Decision:** Validate against local config file only (fast, no API call). If the GitHub API call to update labels fails (e.g., label doesn't exist on repo), surface that error to the user.

### Decision 3: Help Text Label Descriptions
**Question:** Should we hardcode label descriptions in `--help` or generate dynamically from config?
**Decision:** Generate dynamically from `labels.json` config file (DRYer approach).

### Decision 4: Branch Detection Edge Case Tests
**Question:** Should we add edge case tests for branch name patterns with different delimiters?
**Decision:** Skip - rely on existing tests for `extract_issue_number_from_branch()` utility.

### Decision 5: Error Message for Missing GitHub Token
**Question:** Should `set-status` provide a custom friendlier error message when GitHub token is not configured?
**Decision:** Use existing IssueManager error - keep it simple, consistent with other commands.

### Decision 6: Error Message When Label Doesn't Exist on GitHub
**Question:** Should we catch and reformat GitHub API errors when a label doesn't exist on the repo?
**Decision:** Yes - catch the error and provide a helpful hint: "Label 'X' not found on GitHub. Run `mcp-coder define-labels` to create workflow labels."

### Decision 7: Test Count
**Question:** How many unit tests should Step 1 target?
**Decision:** Aim for 6-8 focused tests, but let TDD drive the actual count as needed.

---

## Discussion Date: 2026-01-21 (Plan Review)

### Decision 8: Explicit Error Handling for Missing Label on GitHub
**Question:** Should the plan include explicit pseudocode for catching the "label not found" GitHub error?
**Decision:** Yes - add explicit try/except block with error detection logic to step_2.md pseudocode.

### Decision 9: Debug Logging for Epilog Generation Failures
**Question:** Should we add debug-level logging when the epilog generation fails silently?
**Decision:** Yes - add `logger.debug(f"Failed to build epilog: {e}")` before returning fallback message.
