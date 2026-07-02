# Summary: add `_LABEL_MAP` entry for the `network_proxy` GitHub check (#993)

## Problem

`verify_github()` (from `mcp-workspace`) emits a `network_proxy` `CheckResult`
(proxy / PAC / TCP-reachability diagnostics, `severity="warning"`). The
`mcp-coder verify` renderer surfaces it automatically via `_format_section`,
but `_LABEL_MAP` in `src/mcp_coder/cli/commands/verify.py` has no entry for it,
so it currently renders with the raw key `network_proxy` as its label instead
of a human-readable one.

## Goal

Give `network_proxy` a human-readable label (`Network / proxy`) in the GITHUB
section and lock the behavior in with tests.

## Architectural / design changes

**None.** This is a pure data change plus test coverage. Specifically:

- `_LABEL_MAP` is a flat `key -> label` lookup dict. `_format_section`
  iterates `result.items()` (the dict returned by `verify_github()`) and calls
  `_LABEL_MAP.get(key, key)` — falling back to the raw key when no label
  exists. Adding one entry to `_LABEL_MAP` is the entire functional change.
- **Render order is unchanged and is NOT controlled by `_LABEL_MAP`.** Row
  order comes from the insertion order of the dict returned by
  `verify_github()` (upstream already inserts `network_proxy` right after
  `api_base_url`). `_LABEL_MAP` placement is cosmetic (source tidiness only).
- **Marker behavior is unchanged.** `_format_section` derives the `[OK]` /
  `[ERR]` / `[WARN]` marker from `ok` alone and ignores `severity`. Because
  `network_proxy` sets `ok=(tcp_probe == "ok")`, a failed probe renders red
  `[ERR]` even though its `severity="warning"` never fails `overall_ok`. This
  is consistent with other warning-severity rows (e.g. `auto_delete_branches`)
  and is intentionally left as-is. Severity-aware markers are out of scope.
- **Value stays on a single line** — no sub-field expansion.

## KISS decisions

- The rendering assertion is folded into the **existing**
  `test_format_section_renders_github_labels` test rather than adding a new
  test method — same coverage, one less thing to maintain.
- The `test_all_github_keys_in_label_map` docstring is made **count-agnostic**
  (drop the hardcoded "9 GitHub check keys") rather than bumping the number.
  The number was already stale; removing it eliminates the drift at the root
  instead of resetting the clock.

## Scope decisions

| Topic | Decision |
|-------|----------|
| Failure symbol | Accept `[ERR]` when the probe fails — no severity-aware rendering. |
| Value layout | Single line; do not expand sub-fields onto indented lines. |
| Label text | `Network / proxy`. |
| `_LABEL_MAP` placement | After `api_base_url` (source tidiness; no render effect). |
| Dependency | Already satisfied — installed `mcp-workspace` exposes `network_proxy`. No version bump. |

## Files created / modified

**Modified:**

- `src/mcp_coder/cli/commands/verify.py` — add one entry to `_LABEL_MAP`.
- `tests/cli/commands/test_verify_format_section_basic.py` — add
  `network_proxy` to the `_GITHUB_KEYS` tuple, make the
  `test_all_github_keys_in_label_map` docstring count-agnostic, and extend
  `test_format_section_renders_github_labels` with a `network_proxy` rendering
  assertion.

**Created:**

- `pr_info/steps/summary.md` (this file)
- `pr_info/steps/step_1.md`

No new folders or modules.

## Acceptance criteria

- `mcp-coder verify` shows a labeled `Network / proxy` row in the GITHUB section.
- No raw `network_proxy` key visible in the output.
- Tests asserting the GitHub key set include `network_proxy` and pass.

## Steps

- **step_1** — Add the `network_proxy` label mapping and its test coverage
  (single commit, TDD).
