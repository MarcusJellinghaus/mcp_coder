# Implementation Summary: MLflow Unified Verify + DB Checks

**Issue:** #543 — mlflow: unified test prompt in verify, DB checks for SQLite, fix deprecated filesystem backend

---

## Overview

Three focused enhancements to the `verify` command and MLflow integration:

1. **Unified test prompt** — move the LLM test call out of `verify_langchain()` into `execute_verify()` so both Claude and LangChain providers are tested identically via `ask_llm()`
2. **SQLite DB verification** — after the test prompt is sent, query the MLflow SQLite database directly (raw `sqlite3`, no MLflow import) to confirm the run was actually logged
3. **Remove deprecated test** — delete `test_real_mlflow_initialization` which uses the deprecated `file:///` filesystem backend with real MLflow

---

## Architectural / Design Changes

### Before

```
execute_verify()
  ├── verify_claude()          # checks CLI only, no LLM call
  ├── verify_langchain()       # internally sends "Reply with OK" via ask_langchain()
  └── verify_mlflow()          # checks file existence / URI format only
```

### After

```
execute_verify()
  ├── verify_claude()          # unchanged: checks CLI only
  ├── verify_langchain()       # checks config + packages only (no LLM call)
  ├── ask_llm("Reply with OK", provider=active_provider, timeout=30)  ← NEW, unified
  └── verify_mlflow(since=timestamp)  # NEW: also queries SQLite DB
        └── query_sqlite_tracking()  ← NEW module: mlflow_db_utils.py
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Test prompt location | `execute_verify()` | Single orchestration point; both providers treated identically |
| SQLite query approach | Raw `sqlite3`, new `mlflow_db_utils.py` | No MLflow import cycle; `mlflow_logger.py` already imports mlflow |
| DB result type | `TrackingStats` dataclass | Typed, simple, stdlib-only |
| Timestamp filtering | `datetime` passed as `since=` | Confirms *this* run was logged, not just any historical run |
| Failure semantics | `overall_ok = False` if enabled + SQLite + `since` provided + not logged; test prompt gates `overall_ok` only when MLflow is enabled | Verify command must be trustworthy |
| MLflow disabled output | `tracking_data` key with `ok=None`, value `"skipped (MLflow disabled)"` | Shows status without false failure |
| HTTP backends | No DB-level checks | HTTP backends don't expose a local file path |
| Test prompt display | Inline `print` in `=== LLM PROVIDER ===` block | Consistent with existing `Active provider` line; no new section needed |
| Deprecated test removal | Delete `test_real_mlflow_initialization` | Redundant with `test_sqlite_backend_with_tilde_expansion`; triggers FutureWarning |
| Integration test marker | `llm_integration` | Consistent with existing `claude_cli_integration`, `langchain_integration` pattern |

---

## Files Created or Modified

### New Files
| File | Purpose |
|------|---------|
| `src/mcp_coder/llm/mlflow_db_utils.py` | Raw `sqlite3` queries; `TrackingStats` dataclass; no MLflow dependency |
| `tests/llm/test_mlflow_db_utils.py` | Unit tests for `query_sqlite_tracking()` |
| `tests/integration/test_verify_llm_integration.py` | End-to-end `llm_integration` test via `execute_verify()` |

### Modified Files
| File | What Changes |
|------|-------------|
| `src/mcp_coder/llm/mlflow_logger.py` | `verify_mlflow(since=)` signature; add `tracking_data` result key; call `query_sqlite_tracking()` for SQLite backends |
| `src/mcp_coder/cli/commands/verify.py` | `execute_verify()`: capture timestamp, call `ask_llm()`, print result, pass `since=` to `verify_mlflow()`; add `"tracking_data"` to `_LABEL_MAP`; remove orphan `"test_prompt"` from `_LABEL_MAP`; show MLflow enabled/disabled status; gate test prompt on MLflow config in `_compute_exit_code` |
| `src/mcp_coder/llm/providers/langchain/verification.py` | Remove test prompt block from `verify_langchain()`; remove `test_prompt` key from returned dict; update `overall_ok` logic |
| `pyproject.toml` | Register `llm_integration` pytest marker |
| `.claude/CLAUDE.md` | Add `and not llm_integration` to recommended pytest exclusion pattern |
| `tests/integration/test_mlflow_integration.py` | Remove `test_real_mlflow_initialization` |
| `tests/llm/test_mlflow_verify.py` | Add tests for `since=` parameter and `tracking_data` key |
| `tests/cli/commands/test_verify_orchestration.py` | Update mock helpers (remove `test_prompt` from langchain mocks); add `ask_llm` patch in relevant tests |
| `tests/cli/commands/test_verify_integration.py` | Update `_make_langchain_result()` helper (remove `test_prompt` key) |
| `tests/llm/providers/langchain/test_langchain_verification.py` | Remove/rewrite 5 test-prompt-related tests; update `overall_ok` assertions |

---

## Step Overview

| Step | Title | Commits |
|------|-------|---------|
| Step 1 | New `mlflow_db_utils.py` module with `TrackingStats` and `query_sqlite_tracking()` | 1 |
| Step 2 | Update `verify_mlflow()` to accept `since=` and add `tracking_data` DB check | 1 |
| Step 3 | Move test prompt to `execute_verify()`; remove it from `verify_langchain()` | 1 |
| Step 4 | Register `llm_integration` marker; remove deprecated test; add E2E integration test | 1 |

---

## Architecture Constraints Respected

- **`mlflow_logger_no_cycles`** (import-linter): `mlflow_logger.py` must not import `logging_utils` or `cli.commands.prompt` — the new `mlflow_db_utils.py` import is within `mcp_coder.llm` and is not forbidden
- **`subprocess_isolation`** (import-linter): `sqlite3` is stdlib, not `subprocess` — no contract applies
- **Layered architecture**: `mlflow_db_utils.py` lives in `mcp_coder.llm` (domain layer) — consistent with `mlflow_logger.py` and `mlflow_metrics.py`
- **Tach**: `mcp_coder.llm` depends only on `mcp_coder.utils`, `mcp_coder.config`, `mcp_coder.constants` — the new file stays within `mcp_coder.llm`, no new cross-layer dependency introduced
