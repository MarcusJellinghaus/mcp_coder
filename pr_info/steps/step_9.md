# Step 9: Update Documentation

## Context
See `pr_info/steps/summary.md` for full architectural context.

This step updates user-facing documentation to reflect the new CLI command structure.

## Objective
Update documentation files to reference `mcp-coder create-pr` instead of the old standalone script.

---

## Part A: Update README.md

### WHERE
**File:** `README.md`

**Location:** After "🚀 Quick Start" section, add new CLI Commands section

### WHAT - Add CLI Commands Section

```markdown
### CLI Commands

#### Create Pull Request

Automate PR creation with AI-generated summaries after feature implementation.

```bash
# Create PR (uses current directory)
mcp-coder create-pr

# Specify project directory
mcp-coder create-pr --project-dir /path/to/project

# Use API method instead of CLI
mcp-coder create-pr --llm-method claude_code_api

# Get help
mcp-coder create-pr --help
```

**Prerequisites:**
- Clean working directory (no uncommitted changes)
- All tasks complete in `pr_info/TASK_TRACKER.md`
- On feature branch (not main)
- GitHub credentials configured
```

### WHERE EXACTLY
Insert after the "Session Storage and Continuation" section and before "Git Operations" section.

---

## Part B: Update DEVELOPMENT_PROCESS.md

### WHERE
**File:** `pr_info/DEVELOPMENT_PROCESS.md`

**Location:** Section "### 6. PR Creation Workflow"

### WHAT - Update Tool Reference

**Find:**
```markdown
**Tool:** `workflows\create_pr` (fully automated)
```

**Replace with:**
```markdown
**Tool:** `mcp-coder create-pr` (fully automated)
```

### Additional Updates in Same Section

**Find:**
```markdown
**Note:** This section documents the manual process for reference. The `workflows/create_pr` tool now automates all these steps.
```

**Replace with:**
```markdown
**Note:** This section documents the manual process for reference. The `mcp-coder create-pr` command now automates all these steps.
```

---

## Part C: Delete Obsolete Documentation

### WHERE
**File to delete:** `workflows/docs/create_PR_workflow.md`

### WHY
This file documents the old standalone script `workflows/create_PR.py` which no longer exists. The file is obsolete and will cause confusion.

### HOW
```bash
# Delete the file
rm workflows/docs/create_PR_workflow.md
```

Or use the file system tool to delete.

---

## VALIDATION

### Check Documentation Updates
```bash
# Verify README.md has new CLI section
grep "mcp-coder create-pr" README.md

# Verify DEVELOPMENT_PROCESS.md updated
grep "mcp-coder create-pr" pr_info/DEVELOPMENT_PROCESS.md

# Verify old file deleted
ls workflows/docs/create_PR_workflow.md 2>/dev/null || echo "✓ File deleted"
```

### Manual Review
- [ ] README.md CLI section is clear and concise
- [ ] DEVELOPMENT_PROCESS.md references are consistent
- [ ] No references to old `workflows/create_pr` script remain
- [ ] Obsolete documentation file removed

---

## LLM Prompt for This Step

```
I'm implementing Step 9 of the create_PR to CLI command conversion.

Context: See pr_info/steps/summary.md for architecture.

Task: Update documentation files.

Step 9 Details: Read pr_info/steps/step_9.md

Instructions:
1. Update README.md - Add CLI Commands section with create-pr examples
2. Update pr_info/DEVELOPMENT_PROCESS.md - Change tool references from workflows\create_pr to mcp-coder create-pr
3. Delete workflows/docs/create_PR_workflow.md - Obsolete documentation
4. Verify updates with grep commands
5. Commit with message: "Update documentation for create-pr CLI command"

Keep updates concise - brief examples and tool reference changes only.
```

---

## Verification Checklist

### Part A - README.md
- [ ] CLI Commands section added
- [ ] `mcp-coder create-pr` examples included
- [ ] Prerequisites listed
- [ ] Section placed after Quick Start

### Part B - DEVELOPMENT_PROCESS.md
- [ ] Tool reference updated to `mcp-coder create-pr`
- [ ] Note about automation updated
- [ ] No references to old script remain

### Part C - Obsolete File
- [ ] `workflows/docs/create_PR_workflow.md` deleted
- [ ] Verified file doesn't exist

### Final Checks
- [ ] All grep validations pass
- [ ] Manual review completed
- [ ] Commit created

---

## Dependencies

### Required Before This Step
- ✅ Steps 1-5 completed (CLI command implemented)
- ✅ Command is functional

### Blocks
- Step 10 (final validation)

---

## Notes

- **Concise updates:** Brief examples, not verbose
- **User-facing docs only:** Internal docs already in pr_info/
- **Remove confusion:** Delete obsolete documentation
- **Quick task:** Should take ~20 minutes
