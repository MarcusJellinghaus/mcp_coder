# Step 2 — `get_labels_config_path()` without parameters

## LLM prompt

Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`. Step 1 is already
committed. Write the test changes first, then the implementation. Run pylint, mypy, the fast
pytest set and `markers=["textual_integration"]` (see CLAUDE.md), format the code, and produce
exactly one commit.

## WHERE

Source:
- `src/mcp_coder/config/label_config.py`
- `src/mcp_coder/cli/commands/define_labels.py`
- `src/mcp_coder/cli/commands/set_status.py`
- `src/mcp_coder/cli/commands/coordinator/core.py`
- `src/mcp_coder/cli/commands/coordinator/issue_stats.py`
- `src/mcp_coder/workflow_utils/label_transitions.py`
- `src/mcp_coder/workflows/vscodeclaude/checks.py`, `config.py`, `issues.py`
- `src/mcp_coder/icoder/ui/widgets/branch_info_bar.py`
- `src/mcp_coder/icoder/ui/app.py`

Tests:
- `tests/config/test_label_config.py`
- `tests/cli/commands/test_define_labels_actions.py`
- `tests/cli/commands/test_set_status.py`
- `tests/icoder/test_branch_info_bar.py`
- `tests/workflow_utils/test_label_transitions.py`

## WHAT

### Tests first

`tests/config/test_label_config.py`:
- Remove `_get_labels_config_from_project` from the import.
- Replace every `get_labels_config_path(None)` with `get_labels_config_path()`.
- Delete class `TestConfigDiscovery` and class `TestGetLabelsConfigFromProject` entirely
  (`test_load_bundled_labels_config` already covers the bundled path).
- Add:
  ```python
  def test_get_labels_config_path_takes_no_parameters() -> None:
      """The bundled labels are the only source; no per-repo lookup exists."""
      assert not inspect.signature(get_labels_config_path).parameters
  ```
  (add `import inspect`; drop imports that become unused, e.g. `logging`, `Traversable`, if
  nothing else uses them).

`tests/cli/commands/test_define_labels_actions.py` (`generated` fixture, line ~290):
`load_labels_config(get_labels_config_path())`. The doc-snippet tests stay unchanged.

`tests/cli/commands/test_set_status.py` (class `TestExecuteSetStatus`):
- Delete `test_execute_set_status_no_args_malformed_config_fallback` and
  `test_execute_set_status_no_args_fallback_config`.
- Leave `test_execute_set_status_no_args_shows_labels` unchanged (its `resolve_project_dir`
  patch still resolves: the main path uses it).

`tests/icoder/test_branch_info_bar.py`: `_BarApp.compose` yields `BranchInfoBar()`. Keep
`_BarApp(tmp_path)` callers as they are or drop the parameter — whichever leaves no unused
code (simplest: drop `__init__`, change callers to `_BarApp()`, remove unused `Path` /
`tmp_path` uses).

`tests/workflow_utils/test_label_transitions.py`
(`test_update_workflow_label_repo_url_mode_with_validated_issue_number` docstring): replace the
sentences about the "remaining project_dir dependency ... label config ... fall back" with:
"Branch detection/linkage is skipped via validated_issue_number; labels always come from the
bundled config."

### Implementation

`label_config.py`:
```python
def get_labels_config_path() -> Traversable:
    """Return the bundled labels.json (mcp_coder/config/labels.json)."""
    from importlib import resources
    return resources.files("mcp_coder.config") / "labels.json"
```
- Delete `_get_labels_config_from_project` and `from .toml_utils import find_mcp_coder_table_lenient`.
- Module docstring: drop "Config resolution order" and the usage patterns with
  `project_dir` / `config_override`; say labels come from the bundled `labels.json` and show
  `load_labels_config(get_labels_config_path())`.
- `load_labels_config` docstring: replace "Use a plain Path for local overrides" with
  "a plain Path (e.g. a test fixture) or the Traversable from get_labels_config_path()".
- Keep `logger` only if still used; keep `Path` (used by `load_labels_config`).

Callers → `get_labels_config_path()`:
- `define_labels.py` (`execute_define_labels`).
- `coordinator/core.py`: `_filter_eligible_issues` and `get_eligible_issues`; in
  `get_eligible_issues` delete the comment
  "Uses bundled package config (coordinator operates without local project context)".
- `coordinator/issue_stats.py` (`execute_coordinator_issue_stats`, line ~310).
- `workflow_utils/label_transitions.py` (`update_workflow_label`, Step 4 comment block).
- `workflows/vscodeclaude/checks.py`, `config.py` (`_load_labels_config`),
  `issues.py` (`_load_labels_config`) — names unchanged.
- `set_status.py`:
  - `build_set_status_epilog`: `get_labels_config_path()`; drop the
    "Use package bundled config" comment; keep the `try/except`; fallback return becomes
    `"Status labels could not be loaded."`; update the docstring's "fallback message" wording
    if needed.
  - `execute_set_status` no-args branch (ALGORITHM below).
  - Step 2 of the main path: `get_labels_config_path()`.

`branch_info_bar.py`:
- `def __init__(self) -> None:` — remove `project_dir`, `self._project_dir` and the Args
  section; docstring "Initialize the bar." 
- `on_mount`: `load_labels_config(get_labels_config_path())`.
- Remove `from pathlib import Path` (no other use).

`icoder/ui/app.py` line ~119: `yield BranchInfoBar()`.

## HOW

Imports of `get_labels_config_path` stay in `define_labels`, `set_status`, `issue_stats`,
`vscodeclaude.checks` — tests patch them there. No new modules.

## ALGORITHM

`execute_set_status`, no-args branch:
```
if args.status_label is None:
    labels_config = load_labels_config(get_labels_config_path())
    print(format_status_labels(labels_config))
    return 0
```

## DATA

`get_labels_config_path() -> Traversable` (was `Path | Traversable`). Callers pass the result
straight to `load_labels_config`, which accepts both; no type change downstream.

## Done when

- `search_files` for `labels-config` in `src/` finds only `cli/commands/verify_project_keys.py`
  (handled in step 3).
- `search_files` for `get_labels_config_path\(.+\)` in `src/` and `tests/` finds nothing.
- pylint, mypy, fast pytest set and `textual_integration` pass.
