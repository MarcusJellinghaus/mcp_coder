---
description: Approve implementation and transition issue to PR-ready state
disable-model-invocation: true
allowed-tools:
  - "Bash(mcp-coder gh-tool set-status *)"
  - "Bash(mcp-coder check branch-status *)"
---

# Approve Implementation

Approve the implementation and transition the issue to PR-ready state.

**Instructions:**
1. Run branch-status check with `--wait-for-pr` first:
```bash
mcp-coder check branch-status --ci-timeout 400 --pr-timeout 600 --llm-truncate --wait-for-pr
```

2. Only if the branch-status check passes (exit code 0), run the set-status command to update the issue label:
```bash
mcp-coder gh-tool set-status status-08:ready-pr
```

3. Confirm the status change was successful.
**Note:** If the branch-status check fails, report the failures to the user and do not set the label. If the set-status command fails, report the error to the user. Do not use `--force` unless explicitly asked.

**Effect:** Changes issue status from `status-07:code-review` to `status-08:ready-pr`.
