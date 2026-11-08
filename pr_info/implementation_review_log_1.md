# review-implementation review log 1

## Round 1 — 2026-11-08
**Findings**:
Reviewing the contract now; next I'll check how `PythonToolkit` reports `format@apply` results.Checking the test fixtures and test coverage now.`src/mcp_coder/utils/toolkit_runner.py:173` — low — If `tool` or `tool.mcp-coder` holds a non-table value (e.g. `tool.mcp-coder = "x"`), the chained `.get` raises `AttributeError` instead of `ValueError`. That error gets past every caller's `except ValueError` (`check_formatter_config`, `run_formatters`, `_toolkit_rows`), so a malformed config crashes the run instead of reporting a config error. Fix: check each level with `isinstance(..., dict)` and raise `ValueError` naming the file.
`src/mcp_coder/workflows/implement/core.py:250` — low — The final-check gate (`progress.completed > 0 and implement_config.check_type_hints`) is written once around `get_binding` and again in the `if` at line 257. Since `final_binding` stays `()` unless the first condition holds, the second `if` can be just `if final_binding:`.
**Decisions**:
Verdict(decision='tasks', tasks=['In src/mcp_coder/utils/toolkit_runner.py around line 173, check that `tool` and `tool.mcp-coder` are each a dict (isinstance) before calling `.get` on them. If either is not a table, raise ValueError naming the pyproject.toml file, so callers that catch ValueError (check_formatter_config, run_formatters, _toolkit_rows) report a config error instead of crashing with AttributeError. Add a unit test where `tool.mcp-coder` is set to a non-table value (e.g. a string) and assert that ValueError is raised.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-08
**Findings**:
Reviewing the toolkit format path and the remaining workflow diffs.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
