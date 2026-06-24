# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: `Response` refactor → typed actions ([step_1.md](./steps/step_1.md))

- [ ] Implementation (tests + production code): Action union in `core/types.py`, command files return `Response(actions=(...,))`, `app_core.py` typed-action dispatch, `app.py` `match` over `response.actions`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: `is_error` propagation across providers + `ToolResult.is_error` ([step_2.md](./steps/step_2.md))

- [ ] Implementation (tests + production code): `ToolResult.is_error`, `StreamEvent` docstring, claude/copilot/langchain provider edits, `_render_tool_output` returns `truncated`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: `format_tool_oneline()` pure function ([step_3.md](./steps/step_3.md))

- [ ] Implementation (tests + production code): pure tier-1 one-line formatter in `stream_renderer.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: `StreamEventRenderer` FIFO + `cleanup_pending()` ([step_4.md](./steps/step_4.md))

- [ ] Implementation (tests + production code): `_pending` FIFO + `cleanup_pending()`, `ToolResult.raw_name`/`duration_ms`, class docstring update
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: `OutputLog` registry data layer ([step_5.md](./steps/step_5.md))

- [ ] Implementation (tests + production code): `ContentUnit`, registry state + `append_unit`/`extend_open_unit`/`finalize_open_unit`/`update_unit_and_rerender`/`unit_at_line`/`last_unit`/`rendered_lines`, minimal `rebuild()`, `clear_recorded`→`clear_state` rename, extract `format_tool_compressed`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: `OutputLog` tier model + tier dispatch + `on_resize` ([step_6.md](./steps/step_6.md))

- [ ] Implementation (tests + production code): `_tool_display_default`, `effective_tier`/`toggle_unit_tier`/`set_tool_display_default`/`on_resize`, tier dispatch in `_render_unit_atomic`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: `DetailModal` widget ([step_7.md](./steps/step_7.md))

- [ ] Implementation (tests + production code): `detail_modal.py` `DetailModal(ModalScreen)` + `build_detail_text`, escape/enter/ctrl+c bindings
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: Click handler + `F2` binding ([step_8.md](./steps/step_8.md))

- [ ] Implementation (tests + production code): `OutputLog.on_click` + debounce timer + `on_unit_event` callback, `ICoderApp` `F2` binding + `action_open_last_unit_modal`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 9: `ICoderApp` migrates to `append_unit` flow + orphan cleanup ([step_9.md](./steps/step_9.md))

- [ ] Implementation (tests + production code): migrate user-input/tool/assistant-turn writes to `append_unit`/`extend_open_unit`, per-name FIFO, orphan cleanup on cancel + `StreamDone`, replay migration
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 10: `/display` + `--tool-display` + `RebuildOutput` action + `/help` ([step_10.md](./steps/step_10.md))

- [ ] Implementation (tests + production code): `display.py` command, `RebuildOutput` action, `AppCore.tool_display`, CLI `--tool-display` flag, `/help` F2 line, docs, snapshot tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: verify all steps complete, all quality gates green, snapshots inspected
- [ ] PR summary prepared
