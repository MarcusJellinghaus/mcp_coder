# Implementation Review Log — Issue 830

Branch: `830-cli-verify-prompt-misleading-winerror-2-diagnostics-on-windows`
Started: 2026-04-16

## Round 1 — 2026-04-16

**Findings** (13 raised by review subagent):
1. Accept — `verification.py` `_check_servers` brittle `msg.startswith("unresolved placeholder")` category derivation
2. Accept — `verification.py` launch-error `value` duplicates `str(exc)` with `[Errno 2]`-style text
3. Accept — `_exceptions.py` `raise_connection_error` re-computes classification via `.startswith("ssl-error")`
4. Accept — `langchain/__init__.py` does not re-export `LLMMCPLaunchError` alongside other exceptions
5. Accept — `agent.py` `try/except` block duplicated between `run_agent` and `run_agent_stream`; empty-command fallback renders as double-space
6. Skip — `_check_servers` pre-flight `value` tone inconsistency (cosmetic)
7. Skip — `format_diagnostics` truststore hint removed loses hint for non-SSL OSError path
8. Accept — `test_langchain_agent_run.py` two near-identical `wraps_*_as_launch_error` tests
9. Accept — `test_mcp_health_check.py::test_server_failure_has_no_tool_names` mock dead-code after pre-flight short-circuit
10. Skip — `_preflight_mcp_server` env scan top-level only (symmetric with `_load_mcp_server_config`)
11. Skip — `_PLACEHOLDER_RE` permissive
12. Accept — `_check_servers` `except Exception` labels `asyncio.TimeoutError` as "failed to launch"
13. Accept — `test_timeout_handling` assertion tied to finding 12

**Decisions**:
- Accept: 4, 5, 8, 9, 12, 13
- Skip 1: plan-review round 2 already accepted the coupling under YAGNI — do not re-litigate
- Skip 2: issue 830 requires reporting path + class; surrounding class-name context de-emphasizes `[Errno 2]` acceptably
- Skip 3: speculative helper for a single caller — YAGNI (software_engineering_principles.md: "if a change only matters when someone makes a future mistake, skip it")
- Skip 6: cosmetic message tone
- Skip 7: reviewer's own analysis confirmed gating is correct; non-SSL OSError path now de-facto unreachable
- Skip 10/11: reviewer marked as no action / YAGNI

**Changes implemented**:
- `__init__.py`: re-exported `LLMMCPLaunchError`
- `agent.py`: extracted `_format_launch_error()` helper, de-duplicated both call sites, fixed empty-command fallback (now renders `<unknown>`)
- `verification.py`: branched on `isinstance(exc, asyncio.TimeoutError)` in `_check_servers`; timeouts now report `"MCP server 'x' timed out after Ns"` with `error="TimeoutError"`
- `test_langchain_agent_run.py`: parametrized `test_run_agent_wraps_*_as_launch_error` into one case
- `test_mcp_health_check.py`: fixed dead-mock `test_server_failure_has_no_tool_names` (use `sys.executable`); strengthened `test_timeout_handling` assertions

**Checks**: ruff PASS, pylint PASS, mypy PASS (1 pre-existing unrelated error in `tui_preparation.py`), pytest PASS (3714 tests).

**Status**: committed (see next commit)
Committed as `e3171f1` (5 files: `__init__.py`, `agent.py`, `verification.py`, `test_langchain_agent_run.py`, `test_mcp_health_check.py`).

## Round 2 — 2026-04-16

**Findings** (4 raised, all skip-candidates):
14. Skip — `__init__.py` import ordering (cosmetic; tools accept current order)
15. Skip — `verification.py` still uses `cfg.get('command', '')` fallback; unreachable under current control flow (pre-flight short-circuits empty/missing commands)
16. Skip — `_truststore_available()` is still called informationally in `format_diagnostics`; not dead, no action needed
17. Skip — `test_mixed_servers` mixed-mode semantic drift; coverage preserved by `test_launch_error_includes_resolved_path_and_class`

**Decisions**: Skip all 4 — purely cosmetic or note-level. No critical or accept findings.

**Changes**: None.

**Status**: No code changes — loop exit.

## Final Status

**Rounds run**: 2 (1 with changes, 1 clean exit)
**Commits produced by review**: 1 (`e3171f1` — 5 files, 66 insertions / 55 deletions)
**Review outcome**: Issue 830 implementation holds up against requirements and knowledge-base principles. All critical/accept findings resolved. Remaining skip-level notes are cosmetic or unreachable under current control flow.
**Checks at exit**: ruff PASS, pylint PASS, mypy PASS (1 pre-existing unrelated error in `tui_preparation.py`), pytest PASS (3714 tests).
