# Summary — iCoder Branch Info Bar (#844)

## Goal

Add a persistent two-row info area below the existing 3-zone status bar in the
iCoder TUI showing: current branch + dirty state, linked GitHub issue (number,
title, status pill), optional PR number (toggleable), and cache-age stamp.
Three controls: `↻ Refresh issue`, `↻ Refresh PR`, `PR:on|off`.

## Architecture & Design

### New top-level package: `mcp_coder/services/`

A new application-layer package for cross-cutting read-only data services that
several consumers (iCoder now, vscodeclaude/web later) can share.

**Layering**: Same level as `mcp_coder.checks` — depends on
`mcp_workspace_git` and `mcp_workspace_github` shims, used by `mcp_coder.icoder`.
This requires updates to `tach.toml` (new `[[modules]]` entry) and
`.importlinter` (`layered_architecture` contract).

### Three layers per the issue

```
mcp_coder/services/branch_info.py        ← pure data, no Textual, takes project_dir as arg
icoder/services/branch_info_service.py   ← adapter: in-flight flags, pr_enabled, last_branch
icoder/ui/widgets/branch_info_bar.py     ← render-only widget, no I/O, loads labels.json once
```

### Cadence wiring (lives in App)

The app owns timers and worker dispatch (mirrors existing `_stream_llm`):

- `set_interval(2, ...)` → branch+dirty fetch; if branch changed and toggle on, kick PR fetch
- `set_interval(30, ...)` → issue refresh from shared `~/.mcp_coder/coordinator_cache/`
- Button presses (refresh-issue, refresh-PR, toggle-PR) post Textual messages handled in app
- All fetches run in `run_worker(thread=True)`; widget updates via `call_from_thread`

### KISS choices applied

- **Single `BranchInfo` dataclass** with `Optional` fields (no separate error dataclass);
  data layer catches GH errors internally and returns partial data, hard failures raise.
- **Single `BranchInfoView` dataclass** wraps `BranchInfo` + `pr_number` +
  `pr_enabled` + `loading`/`failed` frozensets — the widget's `update_state`
  takes one immutable argument. Keeps the data-layer `BranchInfo`
  UI-flag-free.
- **Textual `Color.get_contrast_text()`** for foreground readability — no manual luminance math.
- **PR-fetch race protection**: monotonic `pr_fetch_generation: int` on the
  service, incremented on each `start_pr_fetch()` and on
  `set_pr_enabled(False)`. Workers capture their generation and drop stale
  results — replaces the simpler "check `pr_enabled` on return" approach
  which has a race window for fast toggle sequences.
- **Thin adapter** (~30 LOC): `project_dir`, `pr_enabled`, `pr_in_flight`,
  `issue_in_flight`, `last_branch`, `pr_fetch_generation`. Pass-through
  methods to data layer with flag bookkeeping.
- **Flat widget API**: one `update_state(view)` method per render — no per-field updates.
- **Branch-change detection** is one line in the 2s tick callback in the app.

### Helpers used (no manual reimplementation)

- `is_working_directory_clean(project_dir)` from `mcp_workspace_git` — for
  dirty detection. No subprocess shell-out.
- `get_repository_identifier(project_dir)` from `mcp_workspace_git` —
  returns `Optional[RepoIdentifier]` with `owner`, `repo_name`,
  `https_url`. No `.git/config` parsing.
- `_get_cache_file_path(repo_id)` from `mcp_workspace_github` — for the
  coordinator cache JSON path. No hardcoded
  `~/.mcp_coder/coordinator_cache/<owner-repo>.issues.json`.
- `IssueBranchManager.get_branch_with_pr_fallback(...)` →
  `PullRequestManager.find_pull_request_by_head(branch_name)` for the
  two-step issue→branch→PR lookup. The first call returns a branch name
  (NOT a PR number).
- `get_labels_config_path(project_dir)` + `load_labels_config(path)` from
  `mcp_coder.config.label_config` — widget builds the name→color mapping
  inline at mount; no upstream `build_label_lookups` change.

## Files to create

```
src/mcp_coder/services/__init__.py
src/mcp_coder/services/branch_info.py
src/mcp_coder/services/py.typed
src/mcp_coder/icoder/services/branch_info_service.py
src/mcp_coder/icoder/ui/widgets/branch_info_bar.py
tests/services/__init__.py
tests/services/test_branch_info.py
tests/icoder/test_branch_info_service.py
tests/icoder/test_branch_info_bar.py
```

## Files to modify

```
tach.toml                                 ← add mcp_coder.services module entry
.importlinter                             ← add mcp_coder.services to layered_architecture
src/mcp_coder/icoder/ui/app.py            ← compose widget, wire timers + button handlers
src/mcp_coder/icoder/ui/styles.py         ← compact-button CSS, info-bar styles
docs/icoder/icoder.md                     ← document the new info area (Step 4)
```

## Implementation order

1. **Data layer** — `services/branch_info.py` + tests + arch wiring
2. **Widget render** — `branch_info_bar.py` + `BranchInfoView` dataclass +
   CSS + render-only tests (constructed `BranchInfoView`)
3. **Adapter** — `branch_info_service.py` + tests
4. **App integration + docs** — timers, workers, button handlers, PR-fetch
   generation token, integration tests, **plus** `docs/icoder/icoder.md`
   "Branch Info" section (folded in from former Step 5 per
   `planning_principles.md` "merge tiny or intertwined steps")

Each step is one commit with all checks passing (pylint, pytest, mypy).
Total: **4 commits** (down from 5 — the docs-only Step 5 was folded into
Step 4).

## Out of scope (per issue)

- PR-toggle persistence
- `/branchinfo` slash command
- Hour/day cache-age formatting
- Issue title truncation
- Sharing with `vscodeclaude/status.py`
