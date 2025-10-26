# Step 4: Update Documentation

## Context
This step reviews and updates user-facing documentation to ensure it accurately reflects the simplified and more robust environment detection approach.

**Reference:** See `pr_info/steps/summary.md` for full architectural context.

## WHERE: Documentation Locations
- **README.md** - Main project documentation
- **Setup/Installation Guides** - Any docs mentioning virtual environment setup
- **`.mcp.json` Configuration Examples** - MCP server configuration files

## WHAT: Documentation Review Tasks

### Task 1: Review README.md

**Purpose:** Check if README mentions virtual environment requirements or setup

**Questions to answer:**
1. Does README.md mention that a venv is required?
2. Does it explain environment detection?
3. Does it mention platform-specific behavior (e.g., Linux vs Windows)?
4. Are setup instructions affected by our changes?

**Action if changes needed:**
- Update any outdated venv requirement statements
- Simplify setup instructions if applicable
- Remove platform-specific warnings if no longer relevant

### Task 2: Check Setup/Installation Documentation

**Purpose:** Ensure setup guides reflect the new simplified approach

**Files to check:**
- Any `INSTALL.md` or `SETUP.md` files
- Developer documentation in `docs/` folder
- Quick start guides
- Troubleshooting guides mentioning environment issues

**Action if changes needed:**
- Update environment setup instructions
- Simplify troubleshooting for environment detection
- Remove outdated error messages or warnings

### Task 3: Verify .mcp.json Configuration Examples

**Purpose:** Confirm that `.mcp.json` examples correctly use environment variables

**What to verify:**
- Examples use `${MCP_CODER_VENV_DIR}` correctly
- Examples use `${MCP_CODER_PROJECT_DIR}` correctly
- No hardcoded paths in examples
- Comments explain what these variables represent

**Expected findings:**
- According to summary.md: ".mcp.json already correctly uses ${MCP_CODER_VENV_DIR} - no changes needed"
- Verify this is accurate

### Task 4: Update Architecture Documentation (if exists)

**Purpose:** Document the architectural change in design docs

**Files to check:**
- `docs/architecture/` folder
- Design decision documents
- Technical specification docs

**Action if changes needed:**
- Document the move from filesystem detection to environment variables
- Explain the benefits (simplicity, reliability, universality)
- Note backward compatibility

## HOW: Execution Approach

### Step-by-Step Process

```
1. Search for documentation files
   → List all markdown files in project root and docs/
   → Identify which files mention environment or venv

2. Review each relevant file
   → Read current content
   → Identify outdated information
   → Determine if updates needed

3. Make targeted updates
   → Update only what needs changing
   → Keep changes minimal and clear
   → Preserve overall structure

4. Verify accuracy
   → Check updated docs match implementation
   → Ensure examples are correct
   → Test any code snippets if present
```

## ALGORITHM: Documentation Review Logic

```
FOR each documentation file:
    1. Read file content
    2. Search for keywords:
       - "virtual environment"
       - "venv"
       - "detect"
       - "MCP_CODER_VENV_DIR"
       - "environment setup"
    3. IF keywords found:
        a. Review context around keywords
        b. Check if information is accurate after changes
        c. IF outdated:
            - Mark for update
            - Draft updated text
        d. ELSE:
            - Mark as verified correct
    4. Continue to next file
END FOR

Summarize findings and changes made
```

## DATA: Documentation Files to Check

### Primary Files (Most Likely to Need Updates)
- `README.md` - Main project documentation
- `.mcp.json` - MCP configuration (verify only, likely correct)

### Secondary Files (Check if They Exist)
- `INSTALL.md` or `SETUP.md`
- `docs/GETTING_STARTED.md`
- `docs/TROUBLESHOOTING.md`
- `docs/architecture/ARCHITECTURE.md`
- Any Python environment or venv setup guides

### Example Code in Documentation
If documentation contains code examples for:
- Setting up virtual environments
- Detecting Python environments
- Using MCP_CODER_* environment variables

These should be reviewed for accuracy.

## Expected Changes

### Likely Updates Needed

1. **Simplified venv requirements**
   - Before: "Virtual environment required on Windows"
   - After: "Works with venv, conda, or system Python"

2. **Error message documentation**
   - Before: "RuntimeError if no venv found"
   - After: "Automatically detects environment, falls back to system Python"

3. **Platform-specific notes**
   - Before: "Linux allows system Python, Windows requires venv"
   - After: "Universal approach works on all platforms"

### Likely No Changes Needed

1. `.mcp.json` configuration examples (already correct per summary)
2. Basic setup instructions (if they just say "create a venv")
3. MCP server documentation (unchanged behavior from server perspective)

## Testing Documentation Changes

### Verification Steps

1. **Read updated docs as a new user would**
   - Are instructions clear?
   - Are examples correct?
   - Any outdated information remaining?

2. **Test code examples (if any)**
   - If docs show command-line examples, try them
   - If docs show Python code snippets, verify accuracy

3. **Check consistency**
   - Do all docs tell the same story?
   - Are environment variable names consistent?
   - Do examples match implementation?

## LLM Prompt for Implementation

```
Implement Step 4 from pr_info/steps/step_4.md with reference to pr_info/steps/summary.md.

Review and update documentation:
1. List all documentation files in the project (README.md, docs/, etc.)
2. Search for mentions of virtual environment, venv, environment detection
3. Review each file for outdated information
4. Make targeted updates only where needed
5. Verify .mcp.json examples are correct (should already be correct)

Use MCP tools exclusively:
- mcp__filesystem__list_directory to find doc files
- mcp__filesystem__read_file to read documentation
- mcp__filesystem__edit_file to make targeted updates

Report findings:
- Which files were checked
- Which files needed updates (and what was changed)
- Which files were verified correct as-is
```

## Success Criteria Checklist

- [ ] README.md reviewed for accuracy
- [ ] Setup/installation guides checked (if they exist)
- [ ] .mcp.json examples verified correct
- [ ] Architecture documentation updated (if it exists)
- [ ] All environment-related documentation is accurate
- [ ] No outdated venv requirement statements
- [ ] No platform-specific warnings that are no longer relevant
- [ ] Code examples in docs are correct
- [ ] Documentation tells consistent story

When all items are checked, Step 4 is complete!
