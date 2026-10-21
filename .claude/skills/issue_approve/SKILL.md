---
description: Approve issue to transition to next workflow status
disable-model-invocation: true
argument-hint: "<issue-number> [--repo owner/repo]"
allowed-tools:
  - mcp__mcp-workspace__github_issue_view
  - mcp__mcp-workspace__git
  - "Bash(mcp-coder gh-tool set-status *)"
  - "Bash(gh issue view *)"
  - "Bash(MSYS_NO_PATHCONV=1 gh issue comment *)"
  - mcp__mcp-workspace__read_file
---

# Approve Issue

Approve the current issue to transition it to the next status in the workflow.

## Resolve Issue Number

The user may provide an issue number as the argument (available as `$ARGUMENTS`).
If no issue number is provided:
1. Check if the issue number is known from prior `/issue_analyse` or `/issue_create` in this conversation
2. Read `.vscodeclaude_status.txt` and extract the issue number from the `Issue #NNN` line
3. If still unknown, ask the user

## Cross-Repo Issues

- If `--repo owner/repo` was given, compare it with `origin` (`mcp__mcp-workspace__git`,
  command `ls_remote`, args `["--get-url", "origin"]`). Normalise both: accept
  `https://github.com/owner/repo` and `git@github.com:owner/repo` forms, drop a trailing
  `.git`, compare case-insensitively.
- Match → ignore `--repo` entirely; follow the normal (workspace) path.
- No match (or no `origin`) → cross-repo: add `--repo owner/repo` to `gh` commands only —
  **never** to `set-status`, which has no `--repo` flag. Fetch with
  `gh issue view <issue_number> --repo owner/repo` via Bash —
  `mcp__mcp-workspace__github_issue_view` only reaches the current repository.

## Instructions

1. Fetch the issue to confirm it exists:
   Call `mcp__mcp-workspace__github_issue_view` with the issue number (or `gh issue view` for cross-repo).

   Note its status labels (labels prefixed `status-`) — step 3 uses them for the promotable
   check and the `--from-status` value.

2. Validate that the issue is ready for approval:
   - Issue has been analyzed/discussed
   - Requirements are clear
   - No blocking questions remain

   If any check fails, stop and report — do not approve.

3. **Promote.**

   | current | next |
   |---|---|
   | `status-01:created` | `status-02:awaiting-planning` |
   | `status-04:plan-review` | `status-05:plan-ready` |
   | `status-07:code-review` | `status-08:ready-pr` |

   - More than one status label → don't promote; report "nothing to approve (multiple
     status labels: X, Y)".
   - Current status not in the table (including no status label) → don't promote; report
     "nothing to approve".
   - Cross-repo → comment `/approve` (use MSYS_NO_PATHCONV to prevent Windows Git Bash path
     conversion) and report "approval requested, not confirmed". No polling.
     ```bash
     MSYS_NO_PATHCONV=1 gh issue comment <issue_number> --repo owner/repo --body "/approve"
     ```
   - Otherwise run from the project directory (no `--project-dir`, no output redirection —
     the result is printed on stderr):
     ```bash
     mcp-coder gh-tool set-status <next> --from-status <current> --issue <issue_number> --force
     ```
     `--force` only skips the clean-tree check, irrelevant for a label change.
     Do **not** also comment `/approve` — the Action would race this call.

4. **Report** the issue number and the outcome:

   | `set-status` result | Report |
   |---|---|
   | exit 0, `Updated issue #N to <next>` | `<current> → <next>` |
   | exit 0, `Skipped set-status to '…': current label is 'X', expected 'Y'` | "not approved (current status X)" |
   | non-zero exit | "approval failed: <error output>" — stop; no retry, no `/approve` fallback |

   Not-called outcomes are reported as stated in step 3.

**Note:** This skill has `disable-model-invocation` — it can only be run by the user typing `/issue_approve`. If you need this skill as a follow-up, tell the user: "Please run `/issue_approve` to proceed."
