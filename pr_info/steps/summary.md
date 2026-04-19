# Issue #853: Improve gh-tool define-labels CLI

## Summary

Make `define-labels` operations opt-in, add config discovery via `pyproject.toml`, add new label metadata fields (`default`, `promotable`, `failure`), and generate GitHub Action workflow files from config.

## Architectural / Design Changes

### 1. Config Discovery (Breaking Change)

**Before:** `get_labels_config_path()` checks `{project_dir}/workflows/config/labels.json` then falls back to bundled config.

**After:** New resolution order:
1. `--config PATH` (explicit, passed as `config_override` parameter)
2. `[tool.mcp-coder] labels-config` in `pyproject.toml` (relative to project root)
3. Bundled package defaults (`mcp_coder/config/labels.json`)

The `workflows/config/labels.json` convention is dropped entirely. The function signature adds an optional `config_override` parameter, keeping backward compatibility for existing callers (`issue_stats.py`, `set_status.py`, `coordinator/core.py`).

### 2. Label Metadata Fields

Three new optional boolean fields on label entries in `labels.json`:
- `"default": true` — marks the initial label for new issues (exactly one required)
- `"promotable": true` — marks labels eligible for `/approve` promotion (promotion target = next label in `workflow_labels` list)
- `"failure": true` — marks failure state labels (used to validate promotion targets)

These fields replace hardcoded label names in both Python code and GitHub Action workflows.

### 3. Config Validation (Always Runs)

New `validate_labels_config()` function in `label_config.py` validates:
- Exactly one `default: true` label exists
- Each `promotable: true` label has a next label in the list
- No `promotable` label promotes to a `failure: true` label

This runs before any operation (separate from `--validate` which checks GitHub issues).

### 4. Opt-in Operations

**Before:** `define-labels` always runs label sync + issue initialization + issue validation.

**After:** Only label sync and config validation always run. Three operations become opt-in:
- `--init` — assign default label to issues without status
- `--validate` — check issues for errors/warnings
- `--generate-github-actions` — write workflow YAML files
- `--all` — shorthand for all three

**API call optimization:** When neither `--init` nor `--validate` is set, skip creating `IssueManager` and calling `list_issues()`.

### 5. GitHub Action Generation

New capability to generate `label-new-issues.yml` and `approve-command.yml` from config data. Templates are inline f-strings in `define_labels.py` — the default label name and promotion map are derived from `default: true` and `promotable: true` fields.

### 6. Summary Output

Shows "skipped" for operations not requested instead of showing zeros.

## Files to Modify

| File | Change |
|------|--------|
| `src/mcp_coder/config/labels.json` | Add `default`, `promotable`, `failure` fields |
| `src/mcp_coder/config/labels_schema.md` | Document new fields |
| `src/mcp_coder/utils/github_operations/label_config.py` | New config discovery, `validate_labels_config()` |
| `src/mcp_coder/cli/gh_parsers.py` | Add `--init`, `--validate`, `--config`, `--generate-github-actions`, `--all` flags |
| `src/mcp_coder/cli/commands/define_labels.py` | Gate operations, GitHub Action generation, updated summary |
| `docs/getting-started/label-setup.md` | Update config discovery, document new flags |
| `docs/repository-setup/github.md` | Update config discovery, document generation |
| `docs/repository-setup/README.md` | Remove `workflows/config/labels.json` reference |
| `docs/cli-reference.md` | Update `define-labels` section |

## Test Files to Modify / Create

| File | Change |
|------|--------|
| `tests/workflows/config/test_labels.json` | Add `default`, `promotable`, `failure` fields |
| `tests/workflows/test_label_config.py` | Tests for new discovery + validation |
| `tests/cli/test_parsers.py` | Add `TestDefineLabelsParser` for new CLI flags |
| `tests/cli/commands/test_define_labels.py` | Tests for flag gating, `--all` expansion |
| `tests/cli/commands/test_define_labels_execute.py` | Update Namespace mocks with new flags |
| `tests/cli/commands/test_define_labels_config.py` | May need fixture updates |
| `tests/cli/commands/test_define_labels_format.py` | Test "skipped" summary output |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Add `default`, `promotable`, `failure` fields to `labels.json` + schema docs + test fixture | Data model |
| 2 | Config validation (`validate_labels_config`) in `label_config.py` + tests | Config validation |
| 3 | New config discovery (drop `workflows/config/`, add `pyproject.toml` + `config_override`) + tests | Config discovery |
| 4 | CLI flags in `gh_parsers.py` (`--init`, `--validate`, `--config`, `--generate-github-actions`, `--all`) + help text | CLI arguments |
| 5 | Gate init/validate in `define_labels.py`, use `default: true` label, updated summary output + tests | Operation gating |
| 6 | GitHub Action generation (`--generate-github-actions`) in `define_labels.py` + tests | Workflow generation |
| 7 | Documentation updates across 4 doc files | Docs |
