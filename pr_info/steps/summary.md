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
- **Textual `Color.get_contrast_text()`** for foreground readability — no manual luminance math.
- **No "drop-next-result" flag** — adapter checks `pr_enabled` when result arrives.
- **Thin adapter** (~30 LOC): just `project_dir`, `pr_enabled`, `pr_in_flight`, `issue_in_flight`,
  `last_branch`. Pass-through methods to data layer with flag bookkeeping.
- **Flat widget API**: one `update_state(...)` method per render — no per-field updates.
- **Branch-change detection** is one line in the 2s tick callback in the app.

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
docs/icoder/icoder.md                     ← document the new info area
```

## Implementation order

1. **Data layer** — `services/branch_info.py` + tests + arch wiring
2. **Widget render** — `branch_info_bar.py` + CSS + render-only tests (constructed `BranchInfo`)
3. **Adapter** — `branch_info_service.py` + tests
4. **App integration** — timers, workers, button handlers, integration test
5. **Docs** — `docs/icoder/icoder.md`

Each step is one commit with all checks passing (pylint, pytest, mypy).

## Out of scope (per issue)

- PR-toggle persistence
- `/branchinfo` slash command
- Hour/day cache-age formatting
- Issue title truncation
- Sharing with `vscodeclaude/status.py`
