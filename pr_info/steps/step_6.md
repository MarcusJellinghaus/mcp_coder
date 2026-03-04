# Step 6: Update Documentation

## Context
Read `pr_info/steps/summary.md` for full context. This final step updates the CLI reference documentation to reflect the new uncommitted changes feature.

## Objective
Update `docs/cli-reference.md` to document the `--committed-only` flag and the new default behavior of showing uncommitted changes.

## Location
**File**: `docs/cli-reference.md`
**Section**: `### git-tool compact-diff`

## Changes Required

### WHERE: Documentation Section
```
docs/cli-reference.md
└── ## Commands
    └── ## git-tool
        └── ### git-tool compact-diff
```

Find the section starting with `### git-tool compact-diff` (around line 750).

### WHAT: Update Documentation

#### 1. Update Synopsis
**Current**:
```bash
mcp-coder git-tool compact-diff [OPTIONS]
```

**After** (unchanged, but ensure it's present):
```bash
mcp-coder git-tool compact-diff [OPTIONS]
```

#### 2. Update Options List
**Current**:
```markdown
**Options:**
- `--project-dir PATH` - Project directory (default: current directory)
- `--base-branch BRANCH` - Base branch to diff against (default: auto-detected)
- `--exclude PATTERN` - Exclude paths matching pattern (repeatable)
```

**After** (add new option):
```markdown
**Options:**
- `--project-dir PATH` - Project directory (default: current directory)
- `--base-branch BRANCH` - Base branch to diff against (default: auto-detected)
- `--exclude PATTERN` - Exclude paths matching pattern (repeatable)
- `--committed-only` - Show only committed changes (exclude uncommitted changes from output)
```

#### 3. Update Description
**Current**:
```markdown
**Description:** Produces a diff between the current branch and its base branch, then applies a two-pass pipeline to replace moved code blocks with concise summary comments. This reduces token usage when reviewing large refactoring changes with an LLM.
```

**After**:
```markdown
**Description:** Produces a diff between the current branch and its base branch, then applies a two-pass pipeline to replace moved code blocks with concise summary comments. This reduces token usage when reviewing large refactoring changes with an LLM.

By default, also shows uncommitted changes (staged, unstaged, and untracked files) in full diff format after the compact diff of committed changes. Use `--committed-only` to suppress uncommitted changes and show only committed changes.

**Output Structure:**
- **Committed changes** - Shown first in compact format (moved code blocks suppressed)
- **Uncommitted changes** - Shown after in full format with subsections:
  - `=== STAGED CHANGES ===` - Files staged for commit
  - `=== UNSTAGED CHANGES ===` - Modified but not staged
  - `=== UNTRACKED FILES ===` - New files not tracked by git

**Notes:**
- Uncommitted changes are shown in full diff format (NOT subject to compact diff suppression)
- `--exclude` patterns apply to both committed and uncommitted changes
- Uncommitted section is automatically skipped if working directory is clean
- When no committed changes exist, shows "No committed changes" message before uncommitted section
```

#### 4. Update Examples
**Current**:
```bash
# Generate compact diff for current branch
mcp-coder git-tool compact-diff

# Exclude conversation files
mcp-coder git-tool compact-diff --exclude "pr_info/.conversations/**"

# Specify base branch explicitly
mcp-coder git-tool compact-diff --base-branch main

# Use in scripts
mcp-coder git-tool compact-diff --project-dir /path/to/project --exclude "*.lock"
```

**After** (add new examples):
```bash
# Generate compact diff with uncommitted changes (default)
mcp-coder git-tool compact-diff

# Show only committed changes (exclude uncommitted)
mcp-coder git-tool compact-diff --committed-only

# Exclude conversation files from both committed and uncommitted
mcp-coder git-tool compact-diff --exclude "pr_info/.conversations/**"

# Exclude multiple patterns (log files and lock files)
mcp-coder git-tool compact-diff --exclude "*.log" --exclude "*.lock"

# Specify base branch explicitly
mcp-coder git-tool compact-diff --base-branch main

# Use in scripts (committed only, specific project)
mcp-coder git-tool compact-diff --committed-only --project-dir /path/to/project

# Exclude temp files from uncommitted changes
mcp-coder git-tool compact-diff --exclude "*.tmp" --exclude "temp/**"
```

## Complete Updated Section

```markdown
### git-tool compact-diff

Generate a compact diff between the current branch and its base branch,
replacing moved code blocks with summary comments.

```bash
mcp-coder git-tool compact-diff [OPTIONS]
```

**Options:**
- `--project-dir PATH` - Project directory (default: current directory)
- `--base-branch BRANCH` - Base branch to diff against (default: auto-detected)
- `--exclude PATTERN` - Exclude paths matching pattern (repeatable)
- `--committed-only` - Show only committed changes (exclude uncommitted changes from output)

**Exit Codes:**

| Code | Meaning |
|------|---------|
| 0 | Success — compact diff printed to stdout |
| 1 | Could not detect base branch |
| 2 | Error (invalid repo, unexpected exception) |

**Examples:**
```bash
# Generate compact diff with uncommitted changes (default)
mcp-coder git-tool compact-diff

# Show only committed changes (exclude uncommitted)
mcp-coder git-tool compact-diff --committed-only

# Exclude conversation files from both committed and uncommitted
mcp-coder git-tool compact-diff --exclude "pr_info/.conversations/**"

# Exclude multiple patterns (log files and lock files)
mcp-coder git-tool compact-diff --exclude "*.log" --exclude "*.lock"

# Specify base branch explicitly
mcp-coder git-tool compact-diff --base-branch main

# Use in scripts (committed only, specific project)
mcp-coder git-tool compact-diff --committed-only --project-dir /path/to/project

# Exclude temp files from uncommitted changes
mcp-coder git-tool compact-diff --exclude "*.tmp" --exclude "temp/**"
```

**Description:** Produces a diff between the current branch and its base branch, then applies a two-pass pipeline to replace moved code blocks with concise summary comments. This reduces token usage when reviewing large refactoring changes with an LLM.

By default, also shows uncommitted changes (staged, unstaged, and untracked files) in full diff format after the compact diff of committed changes. Use `--committed-only` to suppress uncommitted changes and show only committed changes.

**Output Structure:**
- **Committed changes** - Shown first in compact format (moved code blocks suppressed)
- **Uncommitted changes** - Shown after in full format with subsections:
  - `=== STAGED CHANGES ===` - Files staged for commit
  - `=== UNSTAGED CHANGES ===` - Modified but not staged
  - `=== UNTRACKED FILES ===` - New files not tracked by git

**Notes:**
- Uncommitted changes are shown in full diff format (NOT subject to compact diff suppression)
- `--exclude` patterns apply to both committed and uncommitted changes
- Uncommitted section is automatically skipped if working directory is clean
- When no committed changes exist, shows "No committed changes" message before uncommitted section
```

## Validation

### Documentation Review
```bash
# View the updated documentation
cat docs/cli-reference.md | grep -A 50 "git-tool compact-diff"

# Check for proper markdown rendering (if using markdown viewer)
# Verify:
# - New --committed-only option listed
# - Updated description explains uncommitted changes
# - Output structure documented
# - Examples show new flag usage
```

### Help Text Verification
```bash
# Verify help text matches documentation
mcp-coder git-tool compact-diff --help

# Should show:
# - --committed-only flag
# - Description of what it does
# - Other options unchanged
```

## Definition of Done
- [ ] `--committed-only` option added to Options section
- [ ] Description updated to explain uncommitted changes feature
- [ ] Output Structure section added
- [ ] Notes section added with important details
- [ ] Examples updated with new use cases
- [ ] Examples show `--committed-only` flag usage
- [ ] Examples show exclude patterns on uncommitted changes
- [ ] Exit codes section unchanged (no new exit codes)
- [ ] Markdown formatting correct (proper headers, code blocks, lists)
- [ ] No typos or grammatical errors

## LLM Implementation Prompt

```
You are implementing Step 6 of the compact-diff uncommitted changes feature.

Read pr_info/steps/summary.md for full context.

Task: Update documentation to reflect new uncommitted changes feature.

File: docs/cli-reference.md
Section: ### git-tool compact-diff (around line 750)

Changes:
1. Add --committed-only option to the Options list:
   - `--committed-only` - Show only committed changes (exclude uncommitted changes from output)

2. Update Description section:
   - Keep existing description
   - Add paragraph explaining uncommitted changes are shown by default
   - Add "Output Structure" subsection explaining committed vs uncommitted sections
   - Add "Notes" subsection with important details

3. Update Examples section:
   - Add example: Show only committed changes with --committed-only
   - Add example: Exclude patterns apply to both committed and uncommitted
   - Add example: Exclude multiple patterns
   - Keep existing examples

4. Ensure proper markdown formatting:
   - Use **bold** for section headers
   - Use ``` for code blocks
   - Use - for bullet points
   - Use proper indentation

Reference the "Complete Updated Section" in this step file for exact wording.

Verify:
- Read updated section in markdown viewer
- Run: mcp-coder git-tool compact-diff --help
- Help text should match documentation
- All formatting renders correctly
```

## Final Validation (All Steps Complete)

### Run Full Test Suite
```bash
# Run all tests
pytest tests/ -v

# Expected: All tests pass, no regressions
```

### Manual End-to-End Testing
```bash
# Test 1: Default behavior (uncommitted shown)
echo "test" > test.py
mcp-coder git-tool compact-diff
# Expected: Shows both committed and uncommitted sections

# Test 2: Committed-only flag
mcp-coder git-tool compact-diff --committed-only
# Expected: Shows only committed section

# Test 3: Exclude patterns
echo "debug" > debug.log
mcp-coder git-tool compact-diff --exclude "*.log"
# Expected: test.py shown, debug.log NOT shown

# Test 4: Clean working directory
git add -A && git commit -m "test"
mcp-coder git-tool compact-diff
# Expected: No uncommitted section
```

### Integration Testing
```bash
# Test with real repository workflow
git checkout -b test-feature
echo "feature code" > feature.py
git add feature.py
git commit -m "Add feature"
echo "more changes" >> feature.py  # Uncommitted
mcp-coder git-tool compact-diff
# Expected: Shows committed compact diff + uncommitted full diff
```

## Success Criteria (All Steps)
- [ ] Step 1: Parser flag added and tested
- [ ] Step 2: Uncommitted changes tests written (TDD)
- [ ] Step 3: Uncommitted changes logic implemented
- [ ] Step 4: Exclude pattern tests written (TDD)
- [ ] Step 5: Exclude pattern logic implemented
- [ ] Step 6: Documentation updated
- [ ] All tests pass (100% of new tests, 0 regressions)
- [ ] Manual testing confirms expected behavior
- [ ] Documentation accurate and complete

## Next Steps (Post-Implementation)
1. Create PR with all changes
2. Request code review
3. Address review feedback
4. Merge to main branch
5. Update CHANGELOG if applicable
6. Close issue #477

## Rollback Plan
If issues found after merge:
1. Revert PR commit
2. All changes isolated to CLI layer (easy rollback)
3. No database migrations or breaking changes
4. Core library (`compact_diffs.py`) unchanged - zero risk

---

## Implementation Complete! 🎉
All 6 steps completed following TDD and KISS principles.
