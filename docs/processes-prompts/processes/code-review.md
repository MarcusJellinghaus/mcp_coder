# Code Review

A human or a supervisor skill reviews the implementation and decides: approve, rework, or redesign.

## Labels

| Label | Category |
|---|---|
| `status-07:code-review` | human_action |

`status-07:code-review` → `status-08:ready-pr` (approve)

Other exits:

- → `status-05:plan-ready`: rework (new tasks, then re-implement)
- minor fixes: stay on `status-07:code-review`
- fundamental problems: → `status-04:plan-review` or `status-01:created` via `mcp-coder gh-tool set-status`

## Actor

Human or supervisor skill. vscodeclaude auto-launches `/implementation_review_supervisor` for this label. The supervisor ends at "ready for approval". The label change is a separate command.

Escalations from `status-17` arrive here — see [Automated review](automated-review.md).

**Tools:** MCP code quality checks

## Slash commands

| Command | Purpose | Resulting label |
|---|---|---|
| [`/implementation_review_supervisor`](../../../.claude/skills/implementation_review_supervisor/SKILL.md) | Autonomous review: runs `/implementation_review`, triages findings against `.claude/knowledge_base/`, has subagents fix accepted findings, repeats in rounds, writes `pr_info/implementation_review_log_*.md`. Escalates only when unsure or a major refactoring is needed. Use for the vscodeclaude flow or when the knowledge base can triage most findings | — |
| [`/implementation_review`](../../../.claude/skills/implementation_review/SKILL.md) | Human-supervised review: Claude presents findings, you decide what to act on. Use for full control over every finding | — |
| [`/discuss`](../../../.claude/skills/discuss/SKILL.md) | Go through open findings step by step | — |
| [`/implementation_finalise`](../../../.claude/skills/implementation_finalise/SKILL.md) | Finish open tasks | — |
| [`/implementation_new_tasks`](../../../.claude/skills/implementation_new_tasks/SKILL.md) | Draft additional implementation steps and update the task tracker | — |
| [`/commit_push`](../../../.claude/skills/commit_push/SKILL.md) | Commit and push the updated plan or fixes | — |
| [`/implementation_approve`](../../../.claude/skills/implementation_approve/SKILL.md) | Approve; only when `/check_branch_status` reports `Ready to merge` | `status-08:ready-pr` |
| [`/implementation_needs_rework`](../../../.claude/skills/implementation_needs_rework/SKILL.md) | Send back for rework; next step is implementation, not plan review | `status-05:plan-ready` |

Rework chain: `/implementation_new_tasks` → `/commit_push` → `/implementation_needs_rework`, then `mcp-coder implement` processes the new steps.

## Failure exits

None — human stage.

## Additional prompt details

#### Code Review Prompt

Or use the code review prompt directly:
<details>
<summary>📋 Code Review Prompt (click to expand and copy)</summary>

> **Slash Command:** `/implementation_review` ([`.claude/skills/implementation_review/SKILL.md`](../../../.claude/skills/implementation_review/SKILL.md))
>
> **Additional capability:** Checks git status and confirms branch before review.

````
## Code Review Request

Run this command to get the changes to review:
```
git diff --unified=5 --no-prefix %BASE_BRANCH%...HEAD -- . ":(exclude)pr_info/.conversations/**"
```

No need to run all checks; do not use pylint warnings. Feel free to further analyse any mentioned files and/or the file structure.

### Focus Areas:
- Logic errors or bugs
- Tests for `__main__` functions should be removed (not needed)
- Unnecessary debug code or print statements
- Code that could break existing functionality
- Compliance with existing architecture principles, see `docs/architecture/architecture.md`

### Output Format:
1. **Summary** - What changed (1-2 sentences)
2. **Critical Issues** - Must fix before merging
3. **Suggestions** - Nice to have improvements
4. **Good** - What works well

Do not perform any action. Just present the code review.
````

</details>

#### ABC Discussion Prompt

**Review the result of the pull request review**
<details>
<summary>📋 ABC Discussion Prompt (click to expand and copy)</summary>

```
Can we go through all open suggested changes and questions step by step?
You explain, ask and I answer until we discussed all topics?
Please offer, whenever possible, simple options like 
- A
- B
- C

We will use the discussion later to add more tasks to the implementation plan files under `pr_info/steps`
```

</details>

#### Commit message after plan extension

Commit the changes with the extended implementation plan with

```
  Implementation plan extended based on code review findings
```

#### Detailed Code Review Process

**Objective:** Review and document the completed feature

After all implementation steps are complete:

##### 5.1 Run more detailed checks / additional checks and update tasks

Run certain checks in an automated way and deal with possibly highlighted issues:

- Pylint warnings
- (custom checks - to be developed)
- Check pytest runtime
- Update architecture document
  ( to be further extended )
- double-check also results of CI pipeline

##### 5.2 PR Review

**Process:**

- Review the entire pull request for the feature via an LLM prompt
- Review of LLM review output, decide on next steps based on findings

**Tools:**
