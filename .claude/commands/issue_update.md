---
allowed-tools: Bash(gh issue edit:*), Bash(gh issue view:*), Read, Glob, Grep
workflow-stage: issue-discussion
suggested-next: issue_approve
---

# Update GitHub Issue

Based on our prior `/issue_analyse` discussion, update the GitHub issue with refined content.

**Instructions:**
1. If no issue context is found from prior analysis, respond: "No issue context found. Please run `/issue_analyse <number>` first."

2. First, fetch the current issue content:
```bash
gh issue view <issue_number> --json title,body
```

3. Draft updated issue text with:
   - Clear, concise title
   - Well-structured body with implementation ideas
   - Preserve the original issue content at the bottom under:
     `# Original issue: [old title]\n[old body]`

4. Update the issue:
```bash
gh issue edit <issue_number> --title "NEW_TITLE" --body "NEW_BODY"
```

**Editing Base Branch:**
- To add a base branch: Insert `### Base Branch` section with the branch name
- To change a base branch: Update the content under the existing section
- To remove a base branch: Delete the entire `### Base Branch` section

The base branch must be a single line. Multiple lines will cause an error during branch creation.

**The updated issue should include:**
- Summary of the requirement
- Discussed implementation approach (concise)
- Any constraints or considerations identified
- Original issue content preserved
