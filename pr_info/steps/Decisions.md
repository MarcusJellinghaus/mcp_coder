# Plan Decisions — iCoder Branch Info Bar (#844)

Round-1 plan revisions confirmed by the user. Each entry: what was
decided + the change number from the round-1 review.

## Architecture & Helpers

- **PR lookup is a two-step call** (#1). `get_branch_with_pr_fallback`
  returns a branch name (NOT a PR number). Step A:
  `IssueBranchManager.get_branch_with_pr_fallback(issue, owner, repo)` →
  `Optional[str]` branch name. Step B:
  `PullRequestManager.find_pull_request_by_head(branch_name)` →
  `list[PullRequestData]`; first item's `.number` (or `None`). Renamed
  the public helper from `get_pr_for_branch` to `get_pr_for_issue` to
  match the actual lookup key.

- **Repo identity via `get_repository_identifier`** (#2). Use the helper
  re-exported from `mcp_workspace_git` rather than parsing `.git/config`
  manually. `RepoIdentifier.owner` / `.repo_name` / `.https_url` feed
  both the cache path resolver and `IssueBranchManager(repo_url=...)`.

- **Dirty detection via `is_working_directory_clean(project_dir)`** (#3).
  Negate the result. No direct subprocess shell-out. If we ever need the
  changed-file list, use `get_full_status(project_dir)` instead. This
  also drops `mcp_coder.utils` from the new module's tach `depends_on`.

- **Cache path via `_get_cache_file_path(repo_id)`** (#4). Don't hardcode
  `~/.mcp_coder/coordinator_cache/<owner-repo>.issues.json` in the data
  layer.

- **Status label color: inline mapping** (#5). No upstream
  `build_label_lookups` change. Widget builds `{lbl["name"]: lbl["color"]
  for lbl in cfg["workflow_labels"]}` at `on_mount`, sourced via
  `get_labels_config_path` + `load_labels_config` from
  `mcp_coder.config.label_config`.

## Module Wiring

- **Tach + import-linter wiring is deterministic** (#6). New
  `[[modules]]` entry for `mcp_coder.services` with explicit
  `depends_on = [mcp_workspace_git, mcp_workspace_github, constants?]`
  (no `utils` since dirty detection now goes through the shim, no
  `config` since label colors are resolved in the widget). Add to
  `mcp_coder.icoder.depends_on`. In `.importlinter`'s
  `layered_architecture`, place `mcp_coder.services | mcp_coder.checks`
  on the same layer line. No "TBD".

## Render & State

- **Render state consolidation: option (b) — `BranchInfoView`
  dataclass** (#7). Widget API becomes `update_state(view)` with a
  single immutable argument. `BranchInfo` stays UI-flag-free in the data
  layer (Step 1); `BranchInfoView` (frozen dataclass with `info`,
  `pr_number`, `pr_enabled`, `loading`, `failed`) wraps it for the
  widget. Chosen over moving UI flags into `BranchInfo` because the
  data layer should not carry UI concerns.

## Concurrency

- **PR-fetch race fix: monotonic generation token on the service** (#8).
  `BranchInfoService._pr_fetch_generation: int`, exposed read-only as
  `current_pr_fetch_generation`, incremented by `start_pr_fetch()` and
  by `set_pr_enabled(False)`. Workers capture their own gen and drop
  stale results. Chosen over the opaque-sentinel alternative because
  an int is trivially loggable/assertable. A new test
  (`test_pr_fetch_race_stale_result_dropped`) exercises the
  toggle-off / toggle-on / second-fetch scenario.

## UI Composition

- **`BranchInfoBar` is a sibling of (not inside) the status-bar
  `Horizontal`** (#9). Yielded as the next statement after the
  `with Horizontal(id="status-bar"):` block closes. Step 4 now contains
  the full pre/post snippet to make placement unambiguous.

## Test Patterns

- **Use Textual's `Pilot` API for button-press tests** (#10). No
  reference to private `app.message_queue`. Tests register handlers and
  observe captured message types.

- **Parameterized status-label test** (#10). Multiple `status-*`-prefixed
  labels: first one wins; document the workflow constraint in
  `labels.json` that only one such label should exist at a time.

## Step Boundaries

- **Step 5 folded into Step 4** (#11). The docs-only step was too small
  for its own commit per `planning_principles.md` ("merge tiny or
  intertwined steps"). `pr_info/steps/step_5.md` deleted; the doc edits
  now live as a "Documentation" sub-section of Step 4 and ship in the
  same commit. Implementation order trimmed to 4 steps in
  `summary.md`.
