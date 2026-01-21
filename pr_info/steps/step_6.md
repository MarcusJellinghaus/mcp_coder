# Step 6: Update DEVELOPMENT_PROCESS.md with Slash Commands

## Reference
- **Summary**: `pr_info/steps/summary.md`
- **Decisions**: `pr_info/steps/Decisions.md` (#16)

## LLM Prompt
```
Implement Step 6 from pr_info/steps/summary.md:
Update docs/processes_prompts/DEVELOPMENT_PROCESS.md to include all available 
slash commands mapped to their workflow stages. Ensure the new slash commands 
(/plan_approve, /implementation_approve, /implementation_needs_rework) are 
properly documented and update references from /implementation_tasks to 
/implementation_new_tasks.
```

## WHERE
- **File to modify**: `docs/processes_prompts/DEVELOPMENT_PROCESS.md`

## WHAT - Changes Required

### 1. Update Section 3 (Plan Review Workflow)

Add `/plan_approve` to the workflow steps. After the "Iterate until complete" step, add:

```markdown
6. **Approve the plan:**
   <details>
   <summary>📋 Approve Implementation Plan</summary>

   > **Slash Command:** `/plan_approve` ([`.claude/commands/plan_approve.md`](../../.claude/commands/plan_approve.md))
   >
   > **Additional capability:** Sets issue status to `status-05:plan-ready` via `mcp-coder set-status`.

   Use this command after plan review is complete to transition the issue to implementation-ready state.

   </details>
```

Update the existing "Approve" note to reference the slash command as an alternative to the GitHub `/approve` comment.

### 2. Update Section 5 (Code Review Workflow)

**Update the "Major Issues Found" section** to include the full workflow with slash commands:

```markdown
- **Major Issues Found:** Create additional implementation steps, then transition for rework
  <details>
  <summary>📋 Full Rework Workflow</summary>

  1. **Create new tasks:** `/implementation_new_tasks` - draft additional implementation steps
  2. **Commit changes:** `/commit_push` - commit the updated plan
  3. **Transition status:** `/implementation_needs_rework` - set status to plan-ready
  4. **Re-implement:** Run `mcp-coder implement` to process new steps

  </details>
```

**Update reference** from `/implementation_tasks` to `/implementation_new_tasks` in the expandable section.

**Add `/implementation_approve` to the approval step:**

```markdown
- **Approve:** Use `/implementation_approve` to transition to `status:ready-pr`
  <details>
  <summary>📋 Approve Implementation</summary>

  > **Slash Command:** `/implementation_approve` ([`.claude/commands/implementation_approve.md`](../../.claude/commands/implementation_approve.md))
  >
  > **Additional capability:** Sets issue status to `status-08:ready-pr` via `mcp-coder set-status`.

  Use this command after code review is complete to transition the issue to PR-ready state.

  </details>
```

### 3. Add Slash Command Reference Table

Add a new section after the "Key Characteristics" section or in an appendix:

```markdown
### Slash Command Quick Reference

| Workflow Stage | Commands |
|----------------|----------|
| **Issue Discussion** | `/issue_analyse`, `/discuss`, `/issue_update`, `/issue_create`, `/issue_approve` |
| **Plan Review** | `/plan_review`, `/discuss`, `/plan_update`, `/commit_push`, `/plan_approve` |
| **Implementation** | `/implementation_finalise` |
| **Code Review** | `/implementation_review`, `/discuss`, `/implementation_new_tasks`, `/commit_push`, `/implementation_approve`, `/implementation_needs_rework` |
| **Utility** | `/rebase` |
```

### 4. Update All References to `/implementation_tasks`

Search and replace all occurrences of `/implementation_tasks` with `/implementation_new_tasks` throughout the document.

## HOW - Integration Points

This is documentation only - no code changes.

## ALGORITHM - No code logic

Documentation update only.

## DATA - No data structures

Documentation update only.

## Verification

After implementation:
1. All links in the document are valid
2. Slash command names match actual file names in `.claude/commands/`
3. Workflow descriptions are consistent with the actual slash command functionality
