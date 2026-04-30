# Plan Decisions — iCoder Branch Info Bar (#844)

Round-1 plan revisions confirmed by the user. Each entry: what was
decided + the change number from the round-1 review.

## Round 2 (consistency + Boy Scout)

- **`fetch_pr` exception policy: propagate, don't swallow** (R2-#2). Step
  3 previously had two contradictory phrasings; resolved by deleting the
  "catches all exceptions internally" wording. The adapter is a
  passthrough; the worker (Step 4) catches and updates the failed set.
- **`_apply_branch_state` is the single rendering entrypoint** (R2-#3).
  Step 4's ALGORITHM block now uses `_apply_branch_state` everywhere
  (the stray `apply_pr` reference was a leftover from an earlier
  draft). Both 2s-tick and refresh-PR paths call
  `call_from_thread(_apply_branch_state, ...)`.
- **`pr_fetch_generation` ownership: Step 3 forward-points to Step 4**
  (R2-#4). `summary.md` keeps the field in the adapter description (it
  describes the final shape — useful as a top-level overview); Step 3
  adds a one-line note that race-protection state is added in Step 4.
- **Add cache-miss test in Step 1** (R2-#5). Test 4b covers
  `get_all_cached_issues` returning an empty dict (cache file missing
  or no entries) — `BranchInfo` returns with all issue/cache fields
  `None`, no exception.
- **Add 2s-tick race test in Step 4** (R2-#6). Test #10 mirrors test
  #6/#9 but launches the PR worker via `_tick_branch_quick` rather
  than the refresh-PR button, confirming the generation-token guard
  covers the auto-fetch path too.
- **Boy Scout: drop underscore prefix on cache helpers in the shim's
  public surface** (R2-#7, user-approved). Rename `_get_cache_file_path`
  → `get_cache_file_path` and `_load_cache_file` → `load_cache_file`
  in `src/mcp_coder/mcp_workspace_github.py`'s import block + `__all__`.
  Upstream private names in `mcp_coder_utils` stay private — only the
  shim exposes the public alias. Existing call site in
  `tests/cli/commands/coordinator/test_core.py` updated. Rationale:
  underscore prefix violated the public-API convention for re-exports.

## Round 3 (consistency + clarity)

- **Step 4 `compose()` snippet uses `self._project_dir`** (R3-#1). The
  earlier draft yielded `BranchInfoBar(project_dir)` from inside
  `compose()` where no local `project_dir` is in scope. Fixed by
  storing `self._project_dir: Path` in `__init__` (a plain attribute,
  not buried inside the service) and consuming it from both
  `BranchInfoService(self._project_dir)` and
  `yield BranchInfoBar(self._project_dir)`. Snippet is now
  copy-pasteable.
- **Initialize `_last_branch_info` in Step 4's `__init__` block**
  (R3-#2). The HOW section says `_apply_branch_state` "stores `info`
  on `self`", but the init block didn't declare the attribute. Added
  `self._last_branch_info: BranchInfo | None = None` alongside
  `_last_pr_number`.
- **Boy Scout rename completion: all four cache-shim re-exports**
  (R3-#3). Round 2 promoted `_get_cache_file_path` and
  `_load_cache_file` to public. The same shim file
  (`src/mcp_coder/mcp_workspace_github.py`) also re-exports
  `_save_cache_file` and `_log_stale_cache_entries` with the
  underscore prefix; the same public-API rationale applies. Step 1 now
  renames all four for consistency:
  `_save_cache_file` → `save_cache_file` and
  `_log_stale_cache_entries` → `log_stale_cache_entries`. Existing
  call sites (all in
  `tests/cli/commands/coordinator/test_core.py` — verified via
  `mcp__workspace__search_files`) are listed in Step 1's WHERE block;
  the rename itself happens in the implementation step.
- **Tighten Step 4 test #6 to focus on the refresh-PR button path**
  (R3-#4). Test #6 originally tested toggle-off mid-fetch via the
  refresh-PR button; test #10 (added in Round 2) covers the same race
  via the 2s-tick path. Kept both — both launch paths are worth
  covering — and rewrote test #6's name and body so its
  complementarity to test #10 is explicit. The generation-token
  assertion is now specific: assert that the worker's captured
  generation no longer equals `service.pr_fetch_generation` at the
  moment the result would have been applied, so
  `_apply_branch_state` is never called with `pr_number=42`.

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
