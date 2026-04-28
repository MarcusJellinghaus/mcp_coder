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
| `_LABEL_WIDTH`        | `22`                                             | Global minimum label slot. Sections (e.g. MCP CONFIG WARNINGS) may widen dynamically when their longest label exceeds this; see `label_width` kwarg in `_format_row` / `_format_row_prefix`. |
| `_VALUE_COLUMN_INDENT`| `len(_format_row_prefix('', '', indent=2))`      | Derived constant: position of the first value-column character at indent=2. Used by free-form continuation lines (e.g. install-hint) so they line up under the value column without hand-counting spaces. |

### Two private helpers (replacing all ad-hoc `:<20s` / `:<18s` formatting)

```python
_format_row_prefix(label: str, marker: str, *, indent: int, label_width: int = _LABEL_WIDTH) -> str
_format_row(label: str, marker: str, value: str, *, indent: int, label_width: int = _LABEL_WIDTH) -> str
```

* `_format_row_prefix` renders the column-aligned prefix only — the
  `indent + label_field + marker_field + trailing_space` portion of a row,
  WITHOUT rstrip. It is the building block used wherever the prefix alone
  is required (notably `textwrap.wrap` continuation indent in Step 2). It
  is also the layout single-source-of-truth that `_format_row` composes
  on top of.
* `_format_row` is defined as a composition on top of `_format_row_prefix`:
  `(_format_row_prefix(label, marker, indent=indent, label_width=label_width) + value).rstrip()`.
  One row helper handles both labeled and label-less rows by passing
  `label=''`. There is no separate `_format_freeform_row` — a wrapper that
  delegates to `_format_row(label="", ...)` does not earn its own name once
  the layouts are identical.
* A code comment near `_format_row` warns that labels >`label_width` overrun
  (since `:<{label_width}s` does not truncate). For sections whose label
  set is unknown ahead of time, the caller should compute
  `max(_LABEL_WIDTH, max(len(label) for label, _ in items))` and pass it
  via `label_width=` so the section's value column shifts consistently.

### `_pad` bump

`_pad(title)` target width changed from **60 → 75** so long section titles
(e.g. `MCP SERVERS (via langchain-mcp-adapters — for completeness)`) still get
trailing `=` characters.

### `_collect_mcp_warnings` return-type change

* Old: `list[str]` (pre-formatted lines).
* New: `list[tuple[str, str]]` (label, value) — caller renders via `_format_row`.

The only caller (`execute_verify`) is updated together.

### Migration scope

**Every** tabular row in `verify.py` is routed through one of the helpers.
Partial migration would break cross-section alignment. Sites:

1. `_format_section` — top-level rows, branch-protection child rows, and the
   `strict_mode` no-marker branch.
2. `_format_mcp_section` — server name rows in both modes (wrap and per-tool).
3. `_format_claude_mcp_section` — server name rows.
4. `_print_environment_section` — Python version / Executable / Virtualenv /
   PYTHONPATH / package versions.
5. `_print_project_section` — pyproject.toml / Language / `format_code` /
   `check_type_hints`.
6. `_collect_mcp_warnings` + caller — MCP CONFIG WARNINGS rendering. The
   caller computes a per-section `label_width` (clamped to `_LABEL_WIDTH`
   minimum) so labels like `langchain-mcp-adapters / PYTHONPATH` (35 chars)
   don't overrun.
7. `_run_mcp_edit_smoke_test` — all 3 return paths.
8. `execute_verify` — CONFIG section, PROMPTS section, LLM PROVIDER (Active
   provider), Test prompt success/failure paths, and the
   `server health check skipped (langchain-mcp-adapters not installed)`
   no-marker fallback rows in the MCP servers branch.

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
| `tests/cli/commands/test_verify_orchestration.py`     | Update string-pinned assertions; `TestMcpConfigWarnings` (lines 1093, 1117-1120) pins `list[str]` shape — migrate to `list[tuple[str, str]]` with new label format `"<server> / <env_var>"`. |
| `tests/cli/commands/test_verify_exit_codes.py`        | Update if/where it asserts exact row strings.                  |
| `tests/cli/commands/test_verify_exit_codes_github.py` | Update if/where it asserts exact row strings.                  |
| `tests/cli/commands/conftest.py` (new or extended)    | Hosts BOTH `_make_verify_mocks()` (so the Step 6 end-to-end smoke test can import it) AND the shared alignment-test helpers `_expected_value_column(indent, *, label_width)` and `_assert_value_at_column(line, expected_col)`. The alignment helpers are imported by Step 3's cross-row alignment test and by Step 6's Layer 1 / Layer 2 — keeping them in conftest.py avoids duplication across the three steps. `_make_verify_mocks()` does not exist in `test_verify_orchestration.py` today — Step 6 introduces it fresh, mirroring that file's `@patch` decorator stack and additionally patching `_collect_mcp_warnings` to return an empty list (so the dynamic-width MCP CONFIG WARNINGS section is excluded from Layer 2's captured output; per-section invariant lives in step_4.md). Existing orchestration tests are NOT migrated to use it now (adopt-not-rewrite). |

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

* **Two helpers, composed.** One row helper handles both labeled and
  label-less rows by passing `label=''`. A second `_format_row_prefix`
  exists for the textwrap continuation case (no rstrip) and is the layout
  single-source-of-truth that `_format_row` composes on top of. Both
  labeled and label-less rows align at the same value column index —
  fulfills the issue title literally; KISS wins over micro-optimizing a
  few characters of leading whitespace on CONFIG rows.
* **`label_width` is an opt-in kwarg, not the default.** Almost every caller
  passes the implicit `_LABEL_WIDTH=22`. The MCP CONFIG WARNINGS section is
  the one site that must thread a wider value through (labels of the form
  `langchain-mcp-adapters / PYTHONPATH` reach 35 chars). Adding the kwarg
  costs nothing at the unaware call sites.
* **Hardcoded `_pad` width 75.** No flag, no override.
* **No new test file until step 6.** Existing string-pinned tests already
  cover most surfaces; we update them in place. The new file holds only the
  alignment-invariant tests that genuinely don't belong elsewhere.

## Out-of-Scope

* No changes to `verify_*` domain functions (claude / langchain / mlflow /
  github / config). Their return shapes are stable.
* No reordering of rows or sections.
* No new public API.
