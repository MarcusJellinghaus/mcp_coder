# Step 4: Update Documentation

## Overview

Create new consolidated documentation and update cross-references throughout the project. Include documentation of the config file locations.

## WHERE

- **Create**: `docs/getting-started/LABEL_SETUP.md`
- **Modify**: `README.md`
- **Modify**: `pr_info/DEVELOPMENT_PROCESS.md`
- **Modify**: `docs/configuration/CONFIG.md`
- **Delete**: `docs/configuration/LABEL_WORKFLOW_SETUP.md` (in Step 5)

## WHAT

### New file: `docs/getting-started/LABEL_SETUP.md`

Content structure:
1. **Introduction** - What workflow labels are and why they matter
2. **Prerequisites** - GitHub token configuration
3. **Label Configuration** - Document the two config file locations:
   - Local override: `workflows/config/labels.json` (project-specific)
   - Bundled fallback: `mcp_coder/config/labels.json` (package default)
4. **Using the define-labels command** - CLI usage with examples
5. **GitHub Actions Setup** - `label-new-issues.yml` and `approve-command.yml`
6. **Label Reference** - Brief description of status labels
7. **Cross-references** - Link to DEVELOPMENT_PROCESS.md

### Label Configuration Section (important new content):

```markdown
## Label Configuration

The `define-labels` command uses a two-location configuration system:

### Configuration Priority

1. **Local project config** (checked first):
   ```
   your-project/workflows/config/labels.json
   ```
   Use this to customize labels for your specific project.

2. **Bundled package config** (fallback):
   ```
   mcp_coder/config/labels.json
   ```
   Used when no local config exists. Provides sensible defaults.

### Customizing Labels

To use custom labels for your project:

1. Create the config directory:
   ```bash
   mkdir -p workflows/config
   ```

2. Copy the default config as a starting point:
   ```bash
   # Find the bundled config location
   python -c "from mcp_coder.utils.github_operations.label_config import get_labels_config_path; print(get_labels_config_path(None))"
   
   # Or create your own based on the structure
   ```

3. Edit `workflows/config/labels.json` with your custom labels

4. Run `mcp-coder define-labels --dry-run` to preview changes
```

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

### Modifications to `docs/configuration/CONFIG.md`:

Update the link to label documentation:

**Old:**
```markdown
- [LABEL_WORKFLOW_SETUP.md](LABEL_WORKFLOW_SETUP.md) - GitHub Actions for issue labels
```

**New:**
```markdown
- [Label Setup Guide](../getting-started/LABEL_SETUP.md) - GitHub workflow labels and setup
```

## HOW

### Directory creation:
The `docs/getting-started/` directory may need to be created:
```bash
mkdir -p docs/getting-started
```

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
   - **IMPORTANT**: Add "Label Configuration" section documenting the two config locations:
     - Local: `workflows/config/labels.json` (project-specific override)
     - Bundled: `mcp_coder/config/labels.json` (package default fallback)
   - Include instructions for customizing labels
   - Keep the GitHub Actions YAML examples
   - Add cross-reference to `pr_info/DEVELOPMENT_PROCESS.md`

2. Update `README.md`:
   - Add a "Setup" section (if not exists) or add to existing setup content
   - Document the `define-labels` command with brief description and options
   - Link to the new setup guide

3. Update `pr_info/DEVELOPMENT_PROCESS.md`:
   - Change the prerequisites link from `docs/configuration/LABEL_WORKFLOW_SETUP.md` to `docs/getting-started/LABEL_SETUP.md`
   - Update any references from `python workflows/define_labels.py` to `mcp-coder define-labels`

4. Update `docs/configuration/CONFIG.md`:
   - Update the link from `LABEL_WORKFLOW_SETUP.md` to `../getting-started/LABEL_SETUP.md`
   - Update the description if needed

Do not delete the old documentation file yet - that happens in Step 5.
```

## Verification

- [ ] New guide created at `docs/getting-started/LABEL_SETUP.md`
- [ ] New guide includes "Label Configuration" section with two-location explanation
- [ ] README.md updated with Setup section
- [ ] README.md documents `define-labels` command
- [ ] DEVELOPMENT_PROCESS.md link updated
- [ ] CONFIG.md link updated
- [ ] All internal links work correctly
- [ ] No broken references to old file paths
