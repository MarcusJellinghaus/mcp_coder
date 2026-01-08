# Step 4: Update Documentation

## Overview

Create new consolidated documentation and update cross-references throughout the project.

## WHERE

- **Create**: `docs/getting-started/LABEL_SETUP.md`
- **Modify**: `README.md`
- **Modify**: `pr_info/DEVELOPMENT_PROCESS.md`
- **Delete**: `docs/configuration/LABEL_WORKFLOW_SETUP.md` (in Step 5)

## WHAT

### New file: `docs/getting-started/LABEL_SETUP.md`

Content structure:
1. **Introduction** - What workflow labels are and why they matter
2. **Prerequisites** - GitHub token configuration
3. **Using the define-labels command** - CLI usage with examples
4. **GitHub Actions Setup** - `label-new-issues.yml` and `approve-command.yml`
5. **Label Reference** - Brief description of status labels
6. **Cross-references** - Link to DEVELOPMENT_PROCESS.md

### Modifications to `README.md`:

Add a "Setup" section (or update existing) with:
```markdown
## Setup

### Workflow Labels

To set up GitHub workflow labels for issue tracking:

```bash
mcp-coder define-labels --dry-run  # Preview changes
mcp-coder define-labels            # Apply labels
```

See [Label Setup Guide](docs/getting-started/LABEL_SETUP.md) for complete setup instructions.
```

Add to CLI commands section:
```markdown
### Label Management

- `mcp-coder define-labels` - Sync workflow status labels to GitHub repository
  - `--project-dir PATH` - Project directory (default: current)
  - `--dry-run` - Preview changes without applying
```

### Modifications to `pr_info/DEVELOPMENT_PROCESS.md`:

Update the prerequisites link:

**Old:**
```markdown
**📋 Prerequisites:** Set up GitHub Actions for auto-labeling and `/approve` command. See [Label Workflow Setup](../docs/configuration/LABEL_WORKFLOW_SETUP.md).
```

**New:**
```markdown
**📋 Prerequisites:** Set up GitHub Actions for auto-labeling and `/approve` command. See [Label Setup Guide](../docs/getting-started/LABEL_SETUP.md).
```

Update command references:

**Old:**
```markdown
python workflows/define_labels.py
```

**New:**
```markdown
mcp-coder define-labels
```

## HOW

### Directory creation:
The `docs/getting-started/` directory may need to be created.

## ALGORITHM

N/A - Documentation changes only.

## DATA

N/A - No code data structures.

## LLM Prompt

```
Please implement Step 4 of the implementation plan in `pr_info/steps/step_4.md`.

Context: See `pr_info/steps/summary.md` for the overall plan.

Task: Update documentation:

1. Create `docs/getting-started/LABEL_SETUP.md`:
   - Move and expand content from `docs/configuration/LABEL_WORKFLOW_SETUP.md`
   - Update command from `python workflows/define_labels.py` to `mcp-coder define-labels`
   - Add introduction explaining the workflow label system
   - Document `--dry-run` and `--project-dir` options
   - Keep the GitHub Actions YAML examples
   - Add cross-reference to `pr_info/DEVELOPMENT_PROCESS.md`

2. Update `README.md`:
   - Add a "Setup" section (if not exists) or add to existing setup content
   - Document the `define-labels` command with brief description and options
   - Link to the new setup guide

3. Update `pr_info/DEVELOPMENT_PROCESS.md`:
   - Change the prerequisites link from `docs/configuration/LABEL_WORKFLOW_SETUP.md` to `docs/getting-started/LABEL_SETUP.md`
   - Update any references from `python workflows/define_labels.py` to `mcp-coder define-labels`

Do not delete the old documentation file yet - that happens in Step 5.
```

## Verification

- [ ] New guide created at `docs/getting-started/LABEL_SETUP.md`
- [ ] README.md updated with Setup section
- [ ] README.md documents `define-labels` command
- [ ] DEVELOPMENT_PROCESS.md link updated
- [ ] All internal links work correctly
- [ ] No broken references to old file paths
