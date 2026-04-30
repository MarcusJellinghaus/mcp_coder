# Summary — verify: render API base URL and token fingerprint in GITHUB section

Consumes upstream additions in `mcp-workspace` (#176) — already shipped on `main`, picked up automatically via the plain git URL pin in `pyproject.toml`. **No `pyproject.toml` change in this PR.**

## Goal

Surface two diagnostic fields that `verify_github()` now provides, so users can answer the two top GHE-triage questions from the rendered output of `mcp-coder verify` alone (no `--debug` needed):

1. **"Which API host am I hitting?"** → new `API base URL` row at top of the GITHUB section.
2. **"Is the loaded token the one I expect?"** → fingerprint appended to the existing `from <source>` suffix line under `Token configured`.

## Architectural / Design Changes

**None in any meaningful sense — this is a rendering-only patch.**

- **No new module, function, class, or abstraction.** Two existing touchpoints in one file (`src/mcp_coder/cli/commands/verify.py`): the `_LABEL_MAP` dict and the `token_configured` suffix block inside `_format_section()`.
- **No change to symbol-selection logic.** `_format_section` continues to pick `[OK]`/`[ERR]`/`[WARN]` from `entry["ok"]` only. Upstream's new `severity` field is intentionally ignored — adding severity-aware branching would change behavior for *every* row in the GITHUB section, violating the "purely additive" constraint.
- **Dict insertion order is load-bearing (already true today).** `_format_section` iterates `result.items()` in order; upstream guarantees `api_base_url` is the first key. No sort, no reordering.
- **Backward compatibility is automatic.** Both new fields are read with `.get(...)`. Older `mcp-workspace` (without #176) renders identically to today.
- **Single source of truth for labels preserved.** New row uses a `_LABEL_MAP` entry, no ad-hoc strings in `_format_section()`.
- **Format-string ownership stays upstream.** `format_token_fingerprint` lives in `mcp-workspace`. Downstream renders the string verbatim and tests assert "fingerprint substring appears in suffix" — never the literal shape `ghp_...a3f9`.

## Files Created / Modified

### Modified — production code

| File | Change |
|---|---|
| `src/mcp_coder/cli/commands/verify.py` | Add `"api_base_url": "API base URL"` to `_LABEL_MAP`. Extend the `token_configured` suffix block to append `(<fingerprint>)` when `entry["token_fingerprint"]` is truthy. **~4 lines.** |

### Modified — tests

| File | Change |
|---|---|
| `tests/cli/commands/test_verify_format_section_basic.py` | (a) Add `"api_base_url"` to `TestGitHubLabelMappings._GITHUB_KEYS` tuple. (b) Add one parametrized test for `api_base_url` row rendering (success + fallback). (c) Add one parametrized test for the `token_fingerprint` suffix (with fingerprint, with `"****"`, without). |
| `tests/cli/commands/test_verify_orchestration.py` | Add one orchestration test: inline GitHub fixture with `api_base_url` and `token_fingerprint` populated; assert rendered output contains `"API base URL"` row and the fingerprint substring. No new fixture helper — inline dict (used once). |

### Created

| File | Purpose |
|---|---|
| `pr_info/steps/summary.md` | This file. |
| `pr_info/steps/step_1.md` | Implementation step (single commit). |

## Out of Scope (per issue Decisions table)

- `pyproject.toml` version bump (upstream pinned via plain git URL).
- `--debug` gating (rows render in default output).
- Severity-aware symbol logic (existing `ok`-based logic stays).
- Backward-compat dedicated test (existing field-less fixture covers it implicitly).
- Special-casing short tokens (`"****"` renders verbatim — Python truthiness handles it).

## Step Layout

**One step, one commit.** Both changes touch the same function (`_format_section`) in the same file, both are introduced by the same upstream issue, both are individually trivial (1 line + 3 lines). Splitting into separate commits adds ceremony without benefit. The issue's Decisions table itself scopes this as "One PR — `_LABEL_MAP` add + `token_configured` suffix extension + tests".

- **Step 1**: TDD — write the three failing tests, then add the four production lines, then verify pylint + pytest + mypy all green.
