# Summary: Silence `openai._base_client` DEBUG HTTP request logs

## Issue
Reference: #945

At `--log-level DEBUG`, the OpenAI SDK emits one `openai._base_client - Sending HTTP Request: ...` line per call, cluttering logs. The lines come from the OpenAI SDK's own internal logger, **not** from httpx — so this fix lives in the application-level log suppression shim, not in `_http.py`.

## Architectural / Design Changes

This is **not** an architectural change. It is a one-line addition plus stylistic reorganization within the existing app-specific third-party log suppression block.

- **No new modules, classes, or abstractions.** The issue explicitly rejects extracting the suppression list into a data structure ("premature at 5 entries").
- **No upstream change to `mcp-coder-utils`.** The local shim in `src/mcp_coder/utils/log_utils.py` remains the established place for app-specific noise suppression.
- **Logger target is `openai._base_client` (not parent `openai`)** — preserves any other useful openai DEBUG output. Same precedent as `urllib3.connectionpool` and `github.Requester`.
- **Suppression only raises thresholds** (DEBUG → INFO/WARNING) and only takes effect after `setup_logging()` runs, so it cannot regress other code paths.
- **Forward-compat note:** `openai._base_client` is a private module path (leading underscore). Small risk if the OpenAI SDK restructures, but consistent with existing entries.

## Cosmetic Reorganization (specified by issue)

Production code (`log_utils.py`) — group existing entries by level, alphabetical within each group:
- Replace `# App-specific: suppress noisy third-party loggers` with `# App-specific third-party suppression, grouped by level`.
- `# INFO level` group: `github.Requester`, `openai._base_client` (new), `urllib3.connectionpool`.
- One blank line.
- `# WARNING level` group: `httpcore`, `httpx`.

Test code (`test_log_utils_shim.py`) — reorder tests to match production grouping: `github → openai → urllib3 → httpcore → httpx`.

## Files to be Modified

| File | Change |
|------|--------|
| `src/mcp_coder/utils/log_utils.py` | Add `openai._base_client` at INFO; reorganize comment headers; reorder by level (INFO/WARNING) with blank-line separator; alphabetical within each group. |
| `tests/utils/test_log_utils_shim.py` | Add `test_openai_base_client_suppressed_after_setup`; reorder all per-logger tests to `github → openai → urllib3 → httpcore → httpx`. |

## Files / Folders to be Created

None. (The two `pr_info/steps/*.md` planning files are scaffolding, not project code.)

## Implementation Approach

Single commit / single step — the test change and production change are tightly coupled (the new test asserts behavior introduced by the production change), and the test reordering is a stylistic follow-on in the same file. Splitting would create artificial intermediate states.

- **TDD note:** Test-first ordering still applies *within* the single commit. Write the failing test first, then add the production line, then verify all tests pass.

## Quality Gates

After the edit, all three MCP checks must pass:
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_pytest_check` (with `-n auto` and the unit-test marker exclusions per `CLAUDE.md`)
- `mcp__tools-py__run_mypy_check`
