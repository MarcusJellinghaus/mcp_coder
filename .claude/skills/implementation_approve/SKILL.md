---
description: Approve implementation and transition issue to PR-ready state
disable-model-invocation: true
allowed-tools:
  - "Bash(mcp-coder gh-tool set-status *)"
  - mcp__mcp-workspace__check_branch_status
---

# Approve Implementation

Approve the implementation and transition the issue to PR-ready state.

**Instructions:**
1. Run branch-status check:
Call `mcp__mcp-workspace__check_branch_status`.

2. If `branch-status` reports a base branch other than `main`, ask the user to confirm this is intentional before proceeding.

3. Only if the report's `Recommendations:` section lists a `Ready to merge` bullet, run the set-status command and confirm it succeeded:
The match is case-sensitive and must be on the standalone bullet — exactly `- Ready to merge` or `- Ready to merge (squash-merge safe)`. Do not use a case-insensitive or loose substring search: the blocking recommendation `- Not ready to merge (GitHub mergeable_state: ...)` contains the same words and must not satisfy the check.
```bash
mcp-coder gh-tool set-status status-08:ready-pr
```

**Note:** If the `Ready to merge` bullet is absent, report the blockers to the user and do not set the label. If the set-status command fails, report the error to the user. Do not use `--force` unless explicitly asked.

**Effect:** Changes issue status from `status-07:code-review` to `status-08:ready-pr`.

4. After the label is set, poll for the PR to be created and pass CI:
Call `mcp__mcp-workspace__check_branch_status`.
