**Workflow:**

1. Launch a new engineer subagent → `/plan_review`
2. Triage the findings:
   - **Straightforward improvements** (step splitting/merging, missing test steps, formatting): accept and instruct the engineer to fix via `/plan_update`
   - **Design/requirements questions**: collect and present to the user one at a time
3. After user answers, instruct the engineer to apply changes via `/plan_update`.
4. Update `pr_info/plan_review_log_{n}.md` with this round's findings, decisions, and changes.
5. Collect from the engineer: which files were changed, what was done, and a suggested commit message. Then launch the **commit agent** with this context.
6. **If no plan was changed this round, go to step 7.** Otherwise, launch a fresh engineer subagent (new context) and repeat from step 1.
7. Add a `## Final Status` section to the log. Commit and push the log via the **commit agent**.
8. Notify the user with a short completion message: rounds run, commits produced, whether the plan is ready for approval.

**Review Log Format** (each round appended to `pr_info/plan_review_log_{n}.md`):

```
## Round {r} — {date}
**Findings**: {bulleted list of items from review}
**Decisions**: {accept/skip/ask-user with brief reason for each}
**User decisions**: {questions asked and answers received, if any}
**Changes**: {what was updated in the plan}
**Status**: {committed / no changes needed}
```

**Subagent instructions:** Remind subagents to follow CLAUDE.md (MCP tools, no `cd` prefix, approved commands only).

**Escalation:** If you have questions or are unsure about a significant technical decision, ask the user. For borderline improvements, default to simpler plans rather than asking — only escalate when the change affects scope or architecture.
