# Issue Discussion

Turn a raw idea into a refined, approved issue. This is a human stage: you decide scope and requirements.

## Labels

| Label | Category |
|---|---|
| `status-01:created` | human_action |
| `status-02:awaiting-planning` | bot_pickup |

`status-01:created` → `status-02:awaiting-planning`

A major restart from a later stage lands back on `status-01:created` (`mcp-coder gh-tool set-status status-01:created`).

## Actor

Human, or a supervisor skill. Tier: human or supervisor skill.

- vscodeclaude auto-launches `/issue_analyse`, then `/discuss` (from `labels.json`).
- `/issue_analyse_supervisor` runs the analysis through subagents and approves (→ `status-02`). It escalates scope and requirements questions to you.

## Slash commands

| Command | Purpose | Resulting label |
|---|---|---|
| [`/issue_analyse`](../../../.claude/skills/issue_analyse/SKILL.md) | Fetch the issue and analyse requirements and feasibility | — |
| [`/discuss`](../../../.claude/skills/discuss/SKILL.md) | Step-by-step discussion, one question at a time | — |
| [`/issue_update`](../../../.claude/skills/issue_update/SKILL.md) | Update the issue on GitHub, preserving the original content | — |
| [`/issue_create`](../../../.claude/skills/issue_create/SKILL.md) | Create a GitHub issue from the discussion | `status-01:created` |
| [`/issue_approve`](../../../.claude/skills/issue_approve/SKILL.md) | Approve the issue | `status-02:awaiting-planning` |
| [`/issue_analyse_supervisor`](../../../.claude/skills/issue_analyse_supervisor/SKILL.md) | Run the analysis through subagents, then approve | `status-02:awaiting-planning` |

## Failure exits

None — human stage.

## Additional prompt details

<details>
<summary>📋 Add analysis to Issue Text (click to expand and copy)</summary>

```
Let's draft the initial analysis text, with some very limited, concise implementation ideas to be added to the initial issue text.
The implementation plan should be developed later. Focus on the issue and include the discussed details.
Please provide the issue text as markdown artifact, so that I can easily update the issue on GitHub by adding the analysis text.
```

</details>
