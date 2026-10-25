# Plan Review

Review and approve the implementation plan before any code is written. This is a human stage, supported by a supervisor skill.

## Labels

| Label | Category |
|---|---|
| `status-04:plan-review` | human_action |
| `status-05:plan-ready` | bot_pickup |

`status-04:plan-review` → `status-05:plan-ready`

Major restart → `status-02:awaiting-planning`, after deleting the plan files.

## Actor

Human, or a supervisor skill. Tier: human or supervisor skill.

- vscodeclaude auto-launches `/plan_review_supervisor`.
- The supervisor ends at "ready for approval". `/plan_approve` is a separate step.

## Slash commands

| Command | Purpose | Resulting label |
|---|---|---|
| [`/plan_review_supervisor`](../../../.claude/skills/plan_review_supervisor/SKILL.md) | Run the review through subagents, end at "ready for approval" | — |
| [`/plan_review`](../../../.claude/skills/plan_review/SKILL.md) | Review the plan in `pr_info/steps`; checks git status and confirms the branch first | — |
| [`/discuss`](../../../.claude/skills/discuss/SKILL.md) | Step-by-step discussion, one question at a time | — |
| [`/plan_update`](../../../.claude/skills/plan_update/SKILL.md) | Update the plan files and log decisions | — |
| [`/commit_push`](../../../.claude/skills/commit_push/SKILL.md) | Commit and push the updated plan | — |
| [`/plan_approve`](../../../.claude/skills/plan_approve/SKILL.md) | Approve the plan | `status-05:plan-ready` |
| [`/issue_approve`](../../../.claude/skills/issue_approve/SKILL.md) | Approve from `status-04` | `status-05:plan-ready` |

Iterate review, discussion and update until no more changes are required, then approve.

## Failure exits

None — human stage.

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
