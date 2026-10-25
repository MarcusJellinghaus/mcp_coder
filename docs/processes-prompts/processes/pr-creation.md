# PR Creation

The `create-pr` workflow generates a PR summary, cleans up `pr_info/`, pushes the branch and opens the pull request.

## Labels

| Label | Category |
|---|---|
| `status-08:ready-pr` | bot_pickup |
| `status-09:pr-creating` | bot_busy |
| `status-10:pr-created` | human_action |

`status-08:ready-pr` → `status-09:pr-creating` → `status-10:pr-created`

## Actor

Fully automated. The coordinator dispatches `create-pr` on Jenkins (`WORKFLOW_MAPPING`).

**Output:** Pull request on GitHub with a generated summary.

**Process:**

- Generates PR summary from git diff using LLM
- Cleans up pr_info folder (deletes steps/, clears TASK_TRACKER.md tasks)
- Commits cleanup changes
- Pushes branch to remote
- Creates pull request on GitHub with generated summary
- Uses prompt 🔗 [PR Summary Generation](../../../src/mcp_coder/prompts/prompts.md#pr-summary-generation)

## Slash commands

None for the bot. The failure labels auto-launch [`/check_branch_status`](../../../.claude/skills/check_branch_status/SKILL.md).

## Failure exits

Recovery for all: fix the cause, then `mcp-coder gh-tool set-status status-08:ready-pr`.

| Label | Cause | Recovery |
|---|---|---|
| `status-09f:pr-creating-failed` | Any other error or crash | `mcp-coder gh-tool set-status status-08:ready-pr` |
| `status-09f-timeout:pr-creating-llm-timeout` | LLM timeout during summary generation | `mcp-coder gh-tool set-status status-08:ready-pr` |
| `status-09f-mcp:pr-creating-mcp-unavailable` | MCP server(s) failed to connect | `mcp-coder gh-tool set-status status-08:ready-pr` |

## Additional prompt details

#### Detailed PR Creation Process (Manual Reference)

**Note:** This section documents the manual process for reference. The `mcp-coder create-pr` command now automates all these steps.

##### 6.1 Create Summary (Manual Process - Now Automated)

**Process:**

- Generate comprehensive feature summary
- Document what was implemented and why
- Create PR description for external review
- Clean up PR_Info folder

**Tools:**

- Generate PR summary via LLM prompt
  - Reads PR_Info folder context
  - Includes full git diff for comprehensive summary
  - Cleans up development artifacts: deletes `steps/` subfolder and clears Tasks section from `TASK_TRACKER.md`
  - commit everything except `PR_Info/summary.md` with commit message

    ```
    pr_info\steps cleaned up
    ```

- could be automated
  - get base_branch (or assume main)
  - read PR_Info\pr_summary.md text into temp variable and delete file later.
  - delete PR_Info\pr_summary.md file
  - commit file cleanup
  - push
  - create PR
  - split pr_summary in header and text

TODO - compare against implemented function

**Final Clean State:**

<details>
<summary>📋 Expected TASK_TRACKER.md Template After Cleanup (click to expand)</summary>

After feature completion, the cleaned `TASK_TRACKER.md` should contain only the template structure:

```markdown
# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [development-process.md](./development-process.md) for detailed workflow, prompts, and tools.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in PR_Info/ folder

---

## Tasks

```

</details>
