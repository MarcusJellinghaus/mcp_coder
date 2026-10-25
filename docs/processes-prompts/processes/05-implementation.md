# Implementation

The `implement` workflow works through the plan step by step, with quality checks and a commit after each step.

## Labels

| Label | Category |
|---|---|
| `status-05:plan-ready` | bot_pickup |
| `status-06:implementing` | bot_busy |
| `status-07:code-review` | human_action |
| `status-17:code-review-bot` | bot_pickup |

`status-05:plan-ready` → `status-06:implementing` → `status-07:code-review`

With `auto_review_implementation` on (default off, see [configuration](../../configuration/config.md)), success goes to `status-17:code-review-bot` instead. See [Code review](07-code-review.md).

## Actor

Fully automated. The coordinator dispatches `implement` on Jenkins (`WORKFLOW_MAPPING`).

**Quality gates:**

- All code changes are validated through **pylint** → **pytest** → **mypy**, by the LLM and by routine when implementation is done.
- Formatting with the project's configured formatter.
- Git commits only after all checks pass.

**Iteration:**

- The plan contains several steps; implementation loops over them.
- Each step starts with a fresh context.

**Output:** Implemented code with all quality checks passed.

**Process:**

- Updates `TASK_TRACKER.md` with implementation steps
- Implements each step from the tracker
- Runs quality checks (pylint → pytest → mypy) after each step
- Formats code with the project's configured formatter
- Commits changes with descriptive messages
- Uses prompts ([prompts.md](../../../src/mcp_coder/prompts/prompts.md)):
  - [Implementation Prompt Template](../../../src/mcp_coder/prompts/prompts.md#implementation-prompt-template-using-task-tracker)
  - [Task Tracker Update](../../../src/mcp_coder/prompts/prompts.md#task-tracker-update-prompt)
  - [Mypy Fix](../../../src/mcp_coder/prompts/prompts.md#mypy-fix-prompt)

**Alternative paths:**

- Plan issues discovered → return to `status-04:plan-review`.
- Critical blocker, fundamental redesign needed → return to `status-02:awaiting-planning`.

## Slash commands

| Command | Purpose | Resulting label |
|---|---|---|
| [`/implementation_finalise`](../../../.claude/skills/implementation_finalise/SKILL.md) | Finish open tasks after a failed run | — |
| [`/commit_push`](../../../.claude/skills/commit_push/SKILL.md) | Format, review, commit and push in one command | — |
| [`/check_branch_status`](../../../.claude/skills/check_branch_status/SKILL.md) | Check CI, rebase need, tasks and labels (auto-launched by the failure labels) | — |

## Failure exits

Recovery for all: fix the cause, then `mcp-coder gh-tool set-status status-05:plan-ready`.

| Label | Cause | Recovery |
|---|---|---|
| `status-06f:implementing-failed` | General implementation failure | `mcp-coder gh-tool set-status status-05:plan-ready` |
| `status-06f-ci:ci-fix-needed` | CI exhausted 3 fix attempts | `mcp-coder gh-tool set-status status-05:plan-ready` |
| `status-06f-timeout:llm-timeout` | LLM API timeout during implementation | `mcp-coder gh-tool set-status status-05:plan-ready` |
| `status-06f-prep:task-tracker-prep-failed` | Task tracker preparation failed | `mcp-coder gh-tool set-status status-05:plan-ready` |
| `status-06f-mcp:mcp-unavailable` | MCP server unavailable during implementation | `mcp-coder gh-tool set-status status-05:plan-ready` |
| `status-06f-nochange:no-changes-after-retries` | LLM produced no file changes after 3 retry attempts | `mcp-coder gh-tool set-status status-05:plan-ready` |
| `status-06f-blocked:implementation-blocked` | Agent wrote `pr_info/.blocked.txt` — it could not verify the work and refused to claim it | `mcp-coder gh-tool set-status status-05:plan-ready` |
