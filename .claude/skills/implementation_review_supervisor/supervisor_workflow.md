**Workflow:**

1. Launch a new engineer subagent → `/implementation_review`
2. `/discuss` the findings — triage each item, decide accept/skip
3. Tell the engineer to implement the accepted changes. If a major refactoring is needed, stop and talk to the user.
4. Update `pr_info/implementation_review_log_{n}.md` with this round's findings, decisions, and changes.
5. Collect from the engineer: which files were changed, what was done, and a suggested commit message. Then launch the **commit agent** with this context. The commit agent should verify only the expected files are modified before committing.
6. Launch the engineer → `/check_branch_status`
7. **If no code was changed this round, go to step 8.** Otherwise, launch a fresh engineer subagent (new context) and repeat from step 1.
8. Add a `## Final Status` section to the log. Commit and push the log via the **commit agent**.
9. Launch the engineer → `/check_branch_status` to verify CI, rebase need, and overall readiness. Include the result in the completion message.
10. Notify the user with a short completion message: rounds run, commits produced, whether any issues remain, and branch status (CI, rebase needed).

**Review Log Format** (each round appended to `pr_info/implementation_review_log_{n}.md`):

```
## Round {r} — {date}
**Findings**: {bulleted list of items from review}
**Decisions**: {accept/skip with brief reason for each}
**Changes**: {what was implemented}
**Status**: {committed / no changes needed}
```

**Subagent instructions:** Remind subagents to follow CLAUDE.md (MCP tools, no `cd` prefix, approved commands only).

**Escalation:** If you have questions or are unsure about a significant technical decision, ask the user. For borderline Accept/Skip findings, default to better code quality rather than asking — only escalate when the fix has meaningful scope or risk, not for trivial changes in either direction.
