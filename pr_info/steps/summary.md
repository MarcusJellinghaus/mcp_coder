# Summary — #1466 labels-config: remove the per-repo labels config

## Goal

Remove the custom labels source. `[tool.mcp-coder] labels-config` (in `pyproject.toml` or
`mcp-coder.toml`) and `gh-tool define-labels --config` go away. Every label command and
workflow uses the bundled `mcp_coder/config/labels.json`. A leftover `labels-config` key is
ignored at run time; `mcp-coder verify` reports it as a retired PROJECT key-warning row.

## Architectural / design changes

- **One labels source.** `mcp_coder.config.label_config.get_labels_config_path()` takes no
  parameters and always returns the bundled resource (`importlib.resources` Traversable).
  The three-level resolution (`--config` → project TOML → bundled) is gone, and with it
  `_get_labels_config_from_project` and label_config's dependency on
  `toml_utils.find_mcp_coder_table_lenient`. The helper itself stays in `toml_utils`
  (`prompts`, `format_code` still use it).
- **`load_labels_config(path)` unchanged** — still accepts a `Path` (tests load fixtures
  through it) or a Traversable.
- **No project-dir plumbing for labels.** Callers stop passing `project_dir` / `None`:
  coordinator, vscodeclaude, `set-status`, `issue-stats`, `update_workflow_label`, icoder's
  `BranchInfoBar`. `BranchInfoBar.__init__` loses its `project_dir` parameter.
  `set-status` without arguments loads the bundled file directly (no project-dir resolution,
  no reload-after-failure fallback). `IssueManager.project_dir` stays (branch detection,
  linkage).
- **CLI surface.** `gh-tool define-labels --config` is removed (argparse then rejects it as
  an unrecognized argument). `define-labels` keeps its runtime `validate_labels_config` call.
- **verify.** `labels-config` leaves `_SCHEMA` and `_SETTINGS` in `verify_project_keys`, so it
  is neither a "did you mean" candidate nor part of the "defined in both" check. `_classify`
  returns one retired warning per file that has the key, next to the retired `implement`
  handling. Rows stay warnings only → exit code unchanged.
- **Accepted behaviour change.** `define-labels` deletes `status-*` labels missing from the
  bundled set in every repo (custom labels were never used).

## Steps

1. `step_1.md` — remove `gh-tool define-labels --config` (parser, execute, cli-reference bullet).
2. `step_2.md` — `get_labels_config_path()` without parameters; all callers, `set-status`
   no-args path, `BranchInfoBar`, docstrings.
3. `step_3.md` — `verify` reports a leftover `labels-config` as retired.
4. `step_4.md` — docs.

## Files modified

### Source (`src/mcp_coder/`)
- `config/label_config.py`
- `cli/gh_parsers.py`
- `cli/commands/define_labels.py`
- `cli/commands/set_status.py`
- `cli/commands/verify_project_keys.py`
- `cli/commands/coordinator/core.py`
- `cli/commands/coordinator/issue_stats.py`
- `workflow_utils/label_transitions.py`
- `workflows/vscodeclaude/checks.py`
- `workflows/vscodeclaude/config.py`
- `workflows/vscodeclaude/issues.py`
- `icoder/ui/widgets/branch_info_bar.py`
- `icoder/ui/app.py`

### Tests (`tests/`)
- `cli/test_gh_parsers.py`
- `cli/commands/test_define_labels.py`
- `cli/commands/test_define_labels_summary.py`
- `cli/commands/test_define_labels_actions.py`
- `cli/commands/test_set_status.py`
- `cli/commands/test_verify_project_keys.py`
- `config/test_label_config.py`
- `icoder/test_branch_info_bar.py`
- `workflow_utils/test_label_transitions.py`

### Docs
- `docs/cli-reference.md`
- `docs/getting-started/label-setup.md`
- `docs/repository-setup/github.md`
- `docs/repository-setup/python.md`
- `docs/architecture/architecture.md`

No files are created or deleted (apart from these plan files).

## Acceptance (from the issue)

- The only `labels-config` occurrence in `src/` is the retired-key warning in
  `verify_project_keys`; `get_labels_config_path` takes no parameters.
- `mcp-coder gh-tool define-labels --config x` fails with argparse "unrecognized arguments"
  (parser unit test).
- `labels-config` in `pyproject.toml` or `mcp-coder.toml` → `verify` shows the retired row
  naming that file; exit code unchanged.
- `docs/` and root `README.md` no longer mention `labels-config` or `define-labels --config`.
- `tests/docs/` and `tests/cli/commands/test_define_labels_actions.py` pass.
