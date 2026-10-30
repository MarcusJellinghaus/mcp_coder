# Development Process

You decide scope and merge; everything else can run unattended; failures come back to you as labelled issues.

mcp-coder turns GitHub issues into reviewed pull requests with LLM sessions; see the [README](../../README.md#why-a-structured-process) for what it is and why.

```mermaid
flowchart TD
    subgraph Legend
        direction LR
        L4["Status label: status tracked in GitHub"]
        L3(["Automated: executed by mcp-coder"])
        L2(["Interactive LLM session"])
        L1(["GitHub UI"])
        L4 ~~~ L3 ~~~ L2 ~~~ L1
    end
    Legend ~~~ S01

    S01["01 created"]
    H1(["/issue_analyse + /issue_approve<br/>/issue_analyse_supervisor"])
    S02["02 awaiting-planning"]
    A2(["create-plan"])
    S04["04 plan-review"]
    H3(["/plan_review + /plan_approve<br/>/plan_review_supervisor"])
    S05["05 plan-ready"]
    A4(["implement"])
    S07["07 code-review"]
    H5(["/implementation_review + /implementation_approve<br/>/implementation_review_supervisor"])
    S08["08 ready-pr"]
    A6(["create-pr"])
    S10["10 pr-created"]
    H7(["review and merge"])
    M(["Merged"])

    S14["14 plan-review-bot"]
    A8(["review-plan"])
    S17["17 code-review-bot"]
    A9(["review-implementation"])

    S71["71 merge-conflict"]
    S81["81 failing-ci"]
    S91["91 pr-review-comments"]
    F1(["fix-conflict"])
    F2(["fix-ci"])
    F3(["/pr_comment_triage"])

    S01 --> H1 --> S02 --> A2

    A2 -->|"manual review"| S04 --> H3 --> S05
    A2 -.->|"auto_review_plan"| S14 --> A8 --> S05
    A8 -.->|"needs human"| H3

    S05 --> A4

    A4 -->|"manual review"| S07 --> H5 --> S08
    A4 -.->|"auto_review_implementation"| S17 --> A9 --> S08
    A9 -.->|"needs human"| H5

    S08 --> A6 --> S10 --> H7 --> M

    S10 -->|"merge conflict"| S71 --> F1 --> S10
    S10 -->|"CI error"| S81 --> F2 --> S10
    S10 -->|"PR comment"| S91 --> F3 --> S10

    classDef state fill:#f9fafb,stroke:#9ca3af,color:#374151,font-size:13px
    classDef actHuman fill:#f87171,stroke:#b91c1c,color:#111,font-size:13px
    classDef actSupervisor fill:#fbbf24,stroke:#b45309,color:#111,font-size:13px
    classDef actAuto fill:#4ade80,stroke:#15803d,color:#111,font-size:13px
    class S01,S02,S04,S05,S07,S08,S10,S14,S17,S71,S81,S91,M,L4 state
    class H7,L1 actHuman
    class H1,H3,H5,F3,L2 actSupervisor
    class A2,A4,A6,A8,A9,F1,F2,L3 actAuto
```

After `create-plan` and `implement`, the review runs in one of two ways:

- **Interactive** (default): you work in an LLM session.
- **Automated** (dashed): `review-plan` / `review-implementation`, only if `auto_review_plan` / `auto_review_implementation` is on. If it needs a human, it hands over to the interactive review.

**Interactive LLM sessions** are you working with the LLM, step by step or through a supervisor skill. `mcp-coder vscodeclaude launch` opens them, but only for issues **assigned to you** (the GitHub user your token authenticates as) and sitting at a human-action label. An unassigned issue gets no session ([details](../coordinator-vscodeclaude.md#issue-selection)).

`/plan_review` and `/implementation_review` start a step-by-step session with the LLM (with `/discuss` and the update commands).

`/plan_review_supervisor` and `/implementation_review_supervisor` run the review through subagents and stop at "ready for approval".

Either way, the stage ends with `/plan_approve` or `/implementation_approve`.

`/issue_analyse_supervisor` works the same way for the issue. It runs the analysis through subagents and escalates scope and requirements questions to you. It can approve (→ 02) itself once no questions remain; otherwise approve with `/issue_approve`.

Full state machine incl. failure labels: [workflow matrix](https://htmlpreview.github.io/?https://github.com/MarcusJellinghaus/mcp_coder/blob/main/docs/processes-prompts/github_Issue_Workflow_Matrix.html).

## Processes

| Process | Trigger label | Actor | Slash commands | Doc |
|---|---|---|---|---|
| Issue discussion | `status-01:created` | Interactive LLM session | `/issue_analyse`, `/discuss`, `/issue_update`, `/issue_create`, `/issue_approve`, `/issue_analyse_supervisor` | [issue-discussion](processes/01-issue-discussion.md) |
| Plan creation | `status-02:awaiting-planning` | Automated (`create-plan`) | none | [plan-creation](processes/02-plan-creation.md) |
| Plan review | `status-04:plan-review` | Interactive LLM session | `/plan_review_supervisor`, `/plan_review`, `/discuss`, `/plan_update`, `/commit_push`, `/plan_approve` | [plan-review](processes/04-plan-review.md) |
| Implementation | `status-05:plan-ready` | Automated (`implement`) | `/implementation_finalise`, `/commit_push`, `/check_branch_status` | [implementation](processes/05-implementation.md) |
| Code review | `status-07:code-review` | Interactive LLM session | `/implementation_review_supervisor`, `/implementation_review`, `/discuss`, `/implementation_approve`, `/implementation_needs_rework`, `/implementation_new_tasks`, `/implementation_finalise`, `/commit_push` | [code-review](processes/07-code-review.md) |
| PR creation | `status-08:ready-pr` | Automated (`create-pr`) | none | [pr-creation](processes/08-pr-creation.md) |
| PR merge | `status-10:pr-created` | GitHub UI | `/check_branch_status` | [pr-merge](processes/10-pr-merge.md) |
| PR follow-up | `status-71`, `status-81`, `status-91` | Automated (71, 81); interactive LLM session (91) | `/pr_comment_triage`, `/check_branch_status`, `/rebase` | [pr-follow-up](processes/71-pr-follow-up.md) |
| Automated plan review | `status-14` (with `auto_review_plan`) | Automated (`review-plan`) | `/check_branch_status` | [automated-plan-review](processes/14-automated-plan-review.md) |
| Automated code review | `status-17` (with `auto_review_implementation`) | Automated (`review-implementation`) | `/check_branch_status`, `/implementation_finalise` | [automated-code-review](processes/17-automated-code-review.md) |
| Failure handling | any failure label | Interactive LLM session | `/check_branch_status` | [failure-handling](processes/failure-handling.md) |

## Links

- [Claude Code Cheat Sheet](claude_cheat_sheet.md)
- [Label Setup](../getting-started/label-setup.md) (prerequisite)
- [Workflow Matrix](https://htmlpreview.github.io/?https://github.com/MarcusJellinghaus/mcp_coder/blob/main/docs/processes-prompts/github_Issue_Workflow_Matrix.html)
