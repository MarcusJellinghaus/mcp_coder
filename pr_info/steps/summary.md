# Summary — Issue #41: Validate `.mcp.json` is well-formed (hard fail on broken config)

## Goal

`mcp-coder verify` must emit a **single, clear, upstream diagnostic** when `.mcp.json`
itself is malformed, instead of failing later with confusing indirect errors. A broken
config is currently swallowed silently (`_collect_mcp_warnings` catches
`json.JSONDecodeError` and returns `[]`), so no direct signal is produced.

## Scope (from the issue)

Fold a `.mcp.json` validity check into the existing `verify` flow — **no new subcommand,
no new CLI args**. Two cheap, hand-written checks (no schema, no `mcp-config` dependency):

1. `.mcp.json` is parseable JSON.
2. Top-level `mcpServers` key is present and is an object.

Severity rules:

| Condition | Row | Exit |
|---|---|---|
| Valid JSON + `mcpServers` is a non-empty object | `[OK]` | 0 |
| `mcpServers` is an **empty** object `{}` | `[WARN]` "config present but no servers defined" | 0 |
| Unparseable JSON | `[ERR]` "invalid JSON (...)" | **1** |
| `mcpServers` missing / not an object | `[ERR]` "mcpServers missing or not an object" | **1** |
| `mcp_config_resolved is None` | (section skipped entirely) | unaffected |

Explicitly **out of scope**: the `claude mcp list` connectivity half (already delivered),
per-server `command` checks (dropped — false-positives on `sse`/`http` URL servers), and
adding the `mcp-config` dependency.

## Design / architectural changes

The change is **localized to one module**: `src/mcp_coder/cli/commands/verify.py`. No new
modules, no new dependencies, no public API surface.

### Before
- `_collect_mcp_warnings(path) -> list[(label, value)]` reads and parses `.mcp.json`,
  swallows `(OSError, json.JSONDecodeError)` → `[]` (the silent swallow), and returns
  `${...}` placeholder findings.
- `execute_verify` runs the Claude/LangChain MCP **health checks** first, then renders the
  "MCP CONFIG WARNINGS" placeholder section afterwards (`3a-bis`), re-reading the file.
- `_compute_exit_code` hard-fails on `config_has_error` and `claude_mcp_ok`.

### After
- **New pure helper** `_validate_mcp_config(path) -> (ok, message, warnings)` parses the
  file **exactly once** and owns all error handling. `ok` is a tri-state
  (`True` / `None` = WARN / `False` = hard fail) mirroring the existing
  `claude_mcp_ok` / `tools_exposed_ok` idiom. It also returns the `${...}` placeholder
  findings so the file is never parsed twice.
- **`_collect_mcp_warnings` is deleted** — replaced, not refactored. Its second silent
  swallow is removed with it.
- `execute_verify` calls `_validate_mcp_config` **once**, **before** the Claude/LangChain
  MCP health checks, prints a new `MCP CONFIG` validity row first (the clearest, earliest
  signal), and reuses the returned `warnings` for the existing placeholder section in
  place. It computes `mcp_config_ok = (ok is not False)` and threads it through.
- **`_compute_exit_code` gains an `mcp_config_ok: bool | None = None` parameter**;
  `False` → exit 1, alongside `config_has_error` / `claude_mcp_ok`.

### KISS rationale
- A plain 3-tuple return (`bool | None`, `str`, `list`) instead of a dataclass/enum — it
  reads like the neighbouring tri-state flags already in this file.
- One function replaces one function (net zero function count); no signature juggling to
  pass parsed data between helpers.
- Placeholder-warnings rendering stays where it is (`3a-bis`), now fed from a shared
  variable — smallest possible diff, identical output.

## Files created / modified

| Path | Action |
|---|---|
| `pr_info/steps/summary.md` | **create** (this file) |
| `pr_info/steps/step_1.md` | **create** |
| `pr_info/steps/step_2.md` | **create** |
| `src/mcp_coder/cli/commands/verify.py` | **modify** — add `mcp_config_ok` param (Step 1); add `_validate_mcp_config`, wire it in, delete `_collect_mcp_warnings` (Step 2) |
| `tests/cli/commands/test_verify_exit_codes.py` | **modify** — `mcp_config_ok` exit-code cases (Step 1) |
| `tests/cli/commands/test_verify_orchestration.py` | **modify** — replace `TestMcpConfigWarnings` `_collect_mcp_warnings` tests with `_validate_mcp_config` tests + validity-row/ordering tests (Step 2) |
| `tests/cli/commands/conftest.py` | **modify** — re-point the `_collect_mcp_warnings` mock to `_validate_mcp_config` (Step 2) |
| `tests/cli/commands/test_verify_alignment.py` | **check (low priority)** — its Layer-2 smoke test (`TestExecuteVerifyAlignmentSmoke`) drives `execute_verify` via `_make_verify_mocks`, so the new always-on `MCP CONFIG` row now renders in captured output; alignment still passes (the `.mcp.json` row aligns at the standard value column), but the stale `_collect_mcp_warnings` reference in its module docstring should be checked/updated (Step 2) |

No folders or modules are created or removed.

## Step overview (one commit each)

1. **Step 1 — exit-code plumbing.** Add `mcp_config_ok` parameter to `_compute_exit_code`
   (TDD: exit-code tests first). Independent, additive, no parsing touched.
2. **Step 2 — validity check + wiring.** Add `_validate_mcp_config`, print the validity row
   first, reuse its warnings for the existing placeholder section, delete
   `_collect_mcp_warnings`, and pass `mcp_config_ok` into `_compute_exit_code`.

## Verification (every step)

Run all three MCP checks and fix before proceeding:
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_pytest_check` with
  `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
- `mcp__mcp-tools-py__run_mypy_check`
