# Step 7: Documentation updates

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 7: Update all documentation files to reflect the new config discovery, new CLI flags, and GitHub Action generation capability. Run all code quality checks after changes.

## WHERE

- `docs/getting-started/label-setup.md`
- `docs/repository-setup/github.md`
- `docs/repository-setup/README.md`
- `docs/cli-reference.md`

## WHAT

### `docs/getting-started/label-setup.md`

1. **Config discovery section**: Replace the two-location system (`workflows/config/labels.json` + bundled) with the new three-level resolution:
   - `--config PATH`
   - `[tool.mcp-coder] labels-config` in `pyproject.toml`
   - Bundled package defaults
2. **Remove** `mkdir -p workflows/config` instructions
3. **Add pyproject.toml example**:
   ```toml
   [tool.mcp-coder]
   labels-config = "config/labels.json"
   ```
4. **Command options table**: Add `--init`, `--validate`, `--config`, `--generate-github-actions`, `--all`
5. **Usage examples**: Update to show new flags
6. **GitHub Actions section**: Note that workflows can now be generated with `--generate-github-actions`
7. **Update** the label configuration file format section to mention `default`, `promotable`, `failure` fields

### `docs/repository-setup/github.md`

1. **Customizing Labels section**: Replace `workflows/config/labels.json` reference with `pyproject.toml` config
2. **Issue Validation and Initialization section**: Note that init is now opt-in via `--init`
3. **GitHub Actions Setup section**: Add note about `--generate-github-actions` as alternative to manual setup
4. **Remove** `workflows/config/labels.json` from the customization instructions

### `docs/repository-setup/README.md`

1. **Files table**: Change the `workflows/config/labels.json` row:
   - Old: `workflows/config/labels.json | G | No | No | Only if customizing default labels`
   - New: Remove this row entirely (config now via `pyproject.toml`)
2. **Quick Setup Checklist**: Update the "Install GitHub Actions workflows" item to mention `--generate-github-actions`

### `docs/cli-reference.md`

1. **`gh-tool define-labels` section**: Replace current description and options with:
   - Updated description matching the new help text
   - Full options table with all new flags
   - Updated examples showing `--init`, `--validate`, `--config`, `--generate-github-actions`, `--all`
   - Updated exit codes (unchanged but verify)

## HOW

Direct Markdown edits. No code changes.

## ALGORITHM

N/A — documentation only.

## DATA

N/A.

## Tests

No tests — documentation only step. Verify by reading the updated files for consistency.

## Verification

- No broken links within docs (check cross-references)
- All examples use correct flag names
- No remaining references to `workflows/config/labels.json`
- Pylint, mypy, pytest all green (no code changes, but verify nothing broke)
