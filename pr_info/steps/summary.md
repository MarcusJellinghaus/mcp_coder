# Issue #925 — Align Value Column Across Verify Output

## Goal

Make the value column in `mcp-coder verify` start at the same horizontal
position on every row, regardless of whether a status marker is present
(`[OK]` / `[WARN]` / `[ERR]` / no marker) or which marker it is.

## Architectural / Design Changes

### New module-scope constants in `verify.py`

| Name                  | Value                                            | Why                                                                |
|-----------------------|--------------------------------------------------|--------------------------------------------------------------------|
| `_MARKER_SLOT_WIDTH`  | `max(len(v) for v in STATUS_SYMBOLS.values())`   | Future-proof against new markers (e.g. `[INFO]`, `[CRIT]`).        |
| `_LABEL_WIDTH`        | `22`                                             | Exact fit for the longest current label (`workspace / PYTHONPATH`).|

### Two private helpers (replacing all ad-hoc `:<20s` / `:<18s` formatting)

```python
_format_row(label: str, marker: str, value: str, *, indent: int) -> str
_format_freeform_row(marker: str, value: str, *, indent: int) -> str
```

* `_format_row` renders a labeled tabular row: `indent + label(22) + marker_slot(6) + value`.
  Empty `marker` is padded to 6 chars so the value column is invariant.
* `_format_freeform_row` renders label-less rows used only by the CONFIG section
  (free-form hints / parse errors / multi-word values that don't split into key/value).
  No leading 22-char label slot is wasted.
* A code comment near `_format_row` warns that labels >22 chars overrun (since
  `:<22s` does not truncate); accepted trade-off.

### `_pad` bump

`_pad(title)` target width changed from **60 → 75** so long section titles
(e.g. `MCP SERVERS (via langchain-mcp-adapters — for completeness)`) still get
trailing `=` characters.

### `_collect_mcp_warnings` return-type change

* Old: `list[str]` (pre-formatted lines).
* New: `list[tuple[str, str]]` (label, value) — caller renders via `_format_row`.

The only caller (`execute_verify`) is updated together.

### Migration scope

**Every** tabular row in `verify.py` is routed through one of the two helpers.
Partial migration would break cross-section alignment. Sites:

1. `_format_section` — top-level rows, branch-protection child rows, and the
   `strict_mode` no-marker branch.
2. `_format_mcp_section` — server name rows in both modes (wrap and per-tool).
3. `_format_claude_mcp_section` — server name rows.
4. `_print_environment_section` — Python version / Executable / Virtualenv /
   PYTHONPATH / package versions.
5. `_print_project_section` — pyproject.toml / Language / `format_code` /
   `check_type_hints`.
6. `_collect_mcp_warnings` + caller — MCP CONFIG WARNINGS rendering.
7. `_run_mcp_edit_smoke_test` — all 3 return paths.
8. `execute_verify` — CONFIG section, PROMPTS section, LLM PROVIDER (Active
   provider), and Test prompt success/failure paths.

### Public API

None. All helpers are private (`_`-prefixed). No compatibility shims.

## Files Created or Modified

### Created

| Path                                              | Purpose                                              |
|---------------------------------------------------|------------------------------------------------------|
| `tests/cli/commands/test_verify_alignment.py`     | Alignment-invariant tests (within-section + cross). |
| `pr_info/steps/summary.md`                        | This file.                                           |
| `pr_info/steps/step_1.md` … `step_6.md`           | Per-step implementation prompts.                     |

### Modified

| Path                                                  | What changes                                                   |
|-------------------------------------------------------|----------------------------------------------------------------|
| `src/mcp_coder/cli/commands/verify.py`                | New constants + helpers + migrate every tabular row + `_pad` 60→75 + `_collect_mcp_warnings` return type. |
| `tests/cli/commands/test_verify_format_section.py`    | Update string-pinned assertions to new label/marker widths.    |
| `tests/cli/commands/test_verify_command.py`           | Update string-pinned assertions.                               |
| `tests/cli/commands/test_verify_integration.py`       | Update string-pinned assertions.                               |
| `tests/cli/commands/test_verify_orchestration.py`     | Update if/where it asserts exact row strings.                  |
| `tests/cli/commands/test_verify_exit_codes.py`        | Update if/where it asserts exact row strings.                  |
| `tests/cli/commands/test_verify_exit_codes_github.py` | Update if/where it asserts exact row strings.                  |

(Source touched: **one** file. The bulk of the diff is test fixture updates.)

## Implementation Order (one commit per step)

| Step | Scope                                                                  |
|------|------------------------------------------------------------------------|
| 1    | Add constants + helpers, bump `_pad` 60→75, migrate `_format_section`. |
| 2    | Migrate `_format_mcp_section` + `_format_claude_mcp_section`.          |
| 3    | Migrate `_print_environment_section` + `_print_project_section`.       |
| 4    | Change `_collect_mcp_warnings` return type + migrate caller + migrate `_run_mcp_edit_smoke_test`. |
| 5    | Migrate `execute_verify` inline rows (CONFIG, PROMPTS, LLM PROVIDER, Test prompt). |
| 6    | Add alignment-invariant tests (within-section + cross-section).        |

After each step, all three quality gates must pass: pylint, pytest, mypy.

## KISS Choices

* **Two helpers, not one.** A single helper with `if label:` branching would
  collapse 12 lines into 8 but obscures intent at every call site.
* **No `label_width` parameter.** The issue's draft signature includes one;
  every caller uses 22, so we just use the `_LABEL_WIDTH` constant inside the
  helper. Add a parameter the day a second value is actually needed.
* **Hardcoded `_pad` width 75.** Same reason — no flag, no override.
* **No new test file until step 6.** Existing string-pinned tests already
  cover most surfaces; we update them in place. The new file holds only the
  alignment-invariant tests that genuinely don't belong elsewhere.

## Out-of-Scope

* No changes to `verify_*` domain functions (claude / langchain / mlflow /
  github / config). Their return shapes are stable.
* No reordering of rows or sections.
* No new public API.
