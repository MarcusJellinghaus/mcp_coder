# Plan Review

Review and approve the implementation plan before any code is written. The review is interactive by default (a human or a supervisor skill) and can optionally run automated.

## Labels

How `create-plan` ends decides which review runs: `status-04` by default, `status-14` with `auto_review_plan` on.

| Label | Category | Review |
|---|---|---|
| `status-04:plan-review` | human_action | Interactive |
| `status-14:plan-review-bot` | bot_pickup | Automated |
| `status-14i:plan-reviewing` | bot_busy | Automated |
| `status-05:plan-ready` | bot_pickup | — |

- Interactive: `status-04:plan-review` → `status-05:plan-ready`
- Automated: `status-14:plan-review-bot` → `status-14i:plan-reviewing` → `status-05:plan-ready` (success), `status-04:plan-review` (needs a human) or `status-14f-*` (failure)

Major restart → `status-02:awaiting-planning`, after deleting the plan files.

## Actor

**Interactive (`status-04`):** a human, or a supervisor skill. Tier: human or supervisor skill.

- vscodeclaude auto-launches `/plan_review_supervisor`.
- The supervisor ends at "ready for approval". `/plan_approve` is a separate step.
- Escalations from the automated review arrive here.

**Automated (`status-14`):** fully automated. The coordinator dispatches `review-plan` on Jenkins, only with `auto_review_plan` on (default off, see [configuration](../../configuration/config.md)). It reviews and fixes the plan in rounds and moves the issue to `status-05` once converged. When it needs a human, it hands over to `status-04`. How it runs: [Automated plan review](14-automated-plan-review.md).

## Slash commands

These apply to the interactive review (`status-04`). The automated review needs none, apart from `/check_branch_status` after a failure label.

| Command | Purpose | Resulting label |
|---|---|---|
| [`/plan_review_supervisor`](../../../.claude/skills/plan_review_supervisor/SKILL.md) | Run the review through subagents, end at "ready for approval" | — |
| [`/plan_review`](../../../.claude/skills/plan_review/SKILL.md) | Review the plan in `pr_info/steps`; checks git status and confirms the branch first | — |
| [`/discuss`](../../../.claude/skills/discuss/SKILL.md) | Step-by-step discussion, one question at a time | — |
| [`/plan_update`](../../../.claude/skills/plan_update/SKILL.md) | Update the plan files and log decisions | — |
| [`/commit_push`](../../../.claude/skills/commit_push/SKILL.md) | Commit and push the updated plan | — |
| [`/plan_approve`](../../../.claude/skills/plan_approve/SKILL.md) | Approve the plan | `status-05:plan-ready` |

Iterate review, discussion and update until no more changes are required, then approve.

## Failure exits

**Interactive (`status-04`):** none — human stage.

**Automated (`status-14`):** `status-14f:plan-review-failed`, `status-14f-timeout:plan-review-llm-timeout` and `status-14f-mcp:plan-review-mcp-unavailable`. Recovery: `mcp-coder gh-tool set-status status-14:plan-review-bot`. Causes: [Automated plan review](14-automated-plan-review.md#failure-exits).

## Additional prompt details

<details>
<summary>📋 Commit updated implementation plan with message</summary>

```
Updated implementation plan
```

</details>

<details>
<summary>📋 Requirements Update Note</summary>

```
In case of after updating the pyproject.toml requirements, 
put something in the project plan to stop and tell me, 
so that I can install the requirements. 
This is important so that unit tests can work.
```

Alternatively, update the pyproject.toml already at this stage, and install the dependencies (if required).
</details>

<details>
<summary>📋 Consistency Review</summary>

```
Please clean up the project plan. Ensure that it is consistent.
```

or

```
Please review the project plan for a new feature in the folder PR_Info\steps.
Please review for consistency.
Please tell me all inconsistencies you find and how you want to fix them.
```

</details>

<details>
<summary>📋 Change Summary Request</summary>

```
Please summarise the changes you want to do to the project plan for confirmation as 
(one-liner bullet points)
```

Use in case of uncertainty.
</details>
