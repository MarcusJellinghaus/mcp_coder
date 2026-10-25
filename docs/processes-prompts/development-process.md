# Development Process

You decide scope and merge; everything else can run unattended; failures come back to you as labelled issues.

mcp-coder turns GitHub issues into reviewed pull requests with LLM sessions; see the [README](../../README.md) for what it is and why.

```mermaid
flowchart LR
    S01["01 created"]
    S02["02 awaiting-planning"]
    S04["04 plan-review"]
    S05["05 plan-ready"]
    S07["07 code-review"]
    S08["08 ready-pr"]
    S10["10 pr-created"]
    S71["71 conflict"]
    S81["81 CI failed"]
    S91["91 review feedback"]
    M(["Merged"])

    S01 -->|"/issue_analyse … /issue_approve"| S02
    S02 -->|create-plan| S04
    S04 -->|/plan_approve| S05
    S05 -->|implement| S07
    S07 -->|/implementation_approve| S08
    S08 -->|create-pr| S10
    S10 -->|merge| M

    S10 --> S71 -->|fix-conflict| S10
    S10 --> S81 -->|fix-ci| S10
    S10 --> S91 -->|/pr_comment_triage| S10

    S02 -.->|"auto_review_plan"| S05
    S05 -.->|"auto_review_implementation"| S08

    classDef human fill:#f87171,stroke:#b91c1c,color:#111
    classDef supervisor fill:#fbbf24,stroke:#b45309,color:#111
    classDef auto fill:#4ade80,stroke:#15803d,color:#111
    class M,S10 human
    class S01,S04,S07,S91 supervisor
    class S02,S05,S08,S71,S81 auto
```

Dashed edges: review can run headless (`review-plan` / `review-implementation`) when `auto_review_plan` / `auto_review_implementation` is on.

Legend: red = human required (merge, 10); yellow = human or supervisor skill (01, 04, 07, 91); green = fully automated (coordinator / vscodeclaude / Jenkins) (02, 05, 08, 71, 81).

Renders on GitHub. Full state machine incl. failure labels: [workflow matrix](github_Issue_Workflow_Matrix.html).

## Processes

| Process | Trigger label | Actor | Slash commands | Doc |
|---|---|---|---|---|
| Issue discussion | `status-01:created` | Human or supervisor skill | `/issue_analyse`, `/discuss`, `/issue_update`, `/issue_create`, `/issue_approve`, `/issue_analyse_supervisor` | [issue-discussion](processes/issue-discussion.md) |
| Plan creation | `status-02:awaiting-planning` | Automated (`create-plan`) | none | [plan-creation](processes/plan-creation.md) |
| Plan review | `status-04:plan-review` | Human or supervisor skill | `/plan_review_supervisor`, `/plan_review`, `/discuss`, `/plan_update`, `/commit_push`, `/plan_approve`, `/issue_approve` | [plan-review](processes/plan-review.md) |
| Implementation | `status-05:plan-ready` | Automated (`implement`) | `/implementation_finalise`, `/commit_push`, `/check_branch_status` | [implementation](processes/implementation.md) |
| Code review | `status-07:code-review` | Human or supervisor skill | `/implementation_review_supervisor`, `/implementation_review`, `/discuss`, `/implementation_approve`, `/implementation_needs_rework`, `/implementation_new_tasks`, `/implementation_finalise`, `/commit_push`, `/issue_approve` | [code-review](processes/code-review.md) |
| PR creation | `status-08:ready-pr` | Automated (`create-pr`) | none | [pr-creation](processes/pr-creation.md) |
| PR merge | `status-10:pr-created` | Human | `/check_branch_status` | [pr-merge](processes/pr-merge.md) |
| PR follow-up | `status-71`, `status-81`, `status-91` | Automated (71, 81); human or supervisor skill (91) | `/pr_comment_triage`, `/check_branch_status`, `/rebase` | [pr-follow-up](processes/pr-follow-up.md) |
| Automated review | `status-14`, `status-17` (with `auto_review_plan` / `auto_review_implementation`) | Automated (`review-plan`, `review-implementation`) | `/check_branch_status`, `/implementation_finalise` | [automated-review](processes/automated-review.md) |
| Failure handling | any failure label | Human or supervisor skill | `/check_branch_status` | [failure-handling](processes/failure-handling.md) |

## Links

- [Claude Code Cheat Sheet](claude_cheat_sheet.md)
- [Label Setup](../getting-started/label-setup.md) (prerequisite)
- [Workflow Matrix](github_Issue_Workflow_Matrix.html)
