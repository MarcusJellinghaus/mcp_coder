# Step 8: Documentation Updates

## LLM Prompt
```
Implement Step 8 of Issue #340. Reference: pr_info/steps/summary.md

Update documentation to reflect new functionality:
1. Document define-labels enhancements in repository-setup.md
2. Add exit codes and issue-stats to cli-reference.md
3. Remove references to workflows/ scripts

This is a documentation step - no code changes.
```

---

## WHERE

| File | Action |
|------|--------|
| `docs/repository-setup.md` | Modify |
| `docs/cli-reference.md` | Modify |

---

## WHAT

### Updates to `docs/repository-setup.md`

#### Section: "Workflow Labels Setup" - Add subsection

```markdown
### Issue Validation and Initialization

The `define-labels` command now includes automatic issue validation:

**Automatic initialization:**
- Issues without any workflow status label are initialized with `status-01:created`
- Use `--dry-run` to preview which issues would be initialized

**Validation checks:**
- **Errors:** Issues with multiple status labels (requires manual fix)
- **Warnings:** Bot processes exceeding their stale timeout threshold

**Example output:**
\`\`\`
Summary:
  Labels synced: Created=0, Updated=0, Deleted=0, Unchanged=10
  Issues initialized: 3
  Errors (multiple status labels): 1
    - Issue #45: status-01:created, status-03:planning
  Warnings (stale bot processes): 1
    - Issue #78: status-06:implementing for 150 minutes (threshold: 120)
\`\`\`
```

#### Section: Add "Stale Timeout Configuration"

```markdown
### Stale Timeout Configuration

Bot-busy labels can have configurable timeout thresholds in `labels.json`:

\`\`\`json
{
  "internal_id": "implementing",
  "name": "status-06:implementing",
  "category": "bot_busy",
  "stale_timeout_minutes": 120
}
\`\`\`

Default timeouts:
| Label | Timeout |
|-------|---------|
| status-03:planning | 15 minutes |
| status-06:implementing | 120 minutes |
| status-09:pr-creating | 15 minutes |
```

### Updates to `docs/cli-reference.md`

#### Update `define-labels` section

Add exit codes table:

```markdown
**Exit Codes:**

| Code | Meaning |
|------|---------|
| 0 | Success - no errors or warnings |
| 1 | Errors found - issues with multiple status labels |
| 2 | Warnings only - stale bot processes detected |
```

#### Add new command section

```markdown
### coordinator issue-stats

Display issue statistics grouped by workflow status category.

\`\`\`bash
mcp-coder coordinator issue-stats [OPTIONS]
\`\`\`

**Options:**
- `--filter CATEGORY` - Filter by category: `all` (default), `human`, `bot`
- `--details` - Show individual issue details with links
- `--project-dir PATH` - Project directory path (default: current directory)

**Examples:**
\`\`\`bash
# Show all categories
mcp-coder coordinator issue-stats

# Show only human action required
mcp-coder coordinator issue-stats --filter human

# Show bot issues with details
mcp-coder coordinator issue-stats --filter bot --details
\`\`\`

**Example Output:**
\`\`\`
=== Human Action Required ===
  status-01:created           5 issues
  status-04:plan-review       2 issues

=== Validation Errors ===
  No status label: 2 issues
  Multiple status labels: 1 issue

Total: 16 open issues (13 valid, 3 errors)
\`\`\`
```

---

## HOW

### Documentation Style Guidelines
- Use consistent heading levels
- Include code examples with proper fencing
- Add tables for structured data
- Keep descriptions concise

### Sections to Remove/Update
- Remove any references to `workflows/validate_labels.py`
- Remove any references to `workflows/issue_stats.py`
- Update command list if workflows scripts are mentioned

---

## ALGORITHM

### Documentation Update Process
```
1. Open docs/repository-setup.md
2. Find "Workflow Labels Setup" section
3. Add issue validation subsection
4. Add stale timeout configuration subsection
5. Open docs/cli-reference.md
6. Find define-labels section, add exit codes
7. Add coordinator issue-stats section after other coordinator commands
8. Search for and remove workflow script references
```

---

## DATA

### Cross-Reference Checklist

| Document | Section | Change |
|----------|---------|--------|
| repository-setup.md | Workflow Labels Setup | Add validation info |
| repository-setup.md | New section | Stale timeout config |
| cli-reference.md | define-labels | Add exit codes |
| cli-reference.md | New section | coordinator issue-stats |
| cli-reference.md | Command List table | Add issue-stats row |

---

## VERIFICATION

```bash
# Check markdown syntax
# (Use any markdown linter or preview tool)

# Verify no broken links
grep -r "workflows/validate_labels" docs/
grep -r "workflows/issue_stats" docs/

# Should return no results after cleanup
```

---

## NOTES

- Preserve existing documentation structure and style
- Don't remove historical context if it's still relevant
- Ensure examples are accurate and tested
- Update the command table at the top of cli-reference.md if it exists
