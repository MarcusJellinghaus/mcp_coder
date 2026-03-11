# Issue #508: Extend `mcp-coder verify` — Summary

## Goal

Extend `mcp-coder verify` from a single Claude CLI check into a three-section
health check: **Basic Verification** (Claude CLI), **LLM Provider** (langchain),
and **MLflow** (logging).

## Architectural Changes

### Before

```
cli/commands/verify.py  →  calls claude_cli_verification.py (prints directly, returns exit code)
```

Single responsibility: verify Claude CLI. Output formatting and domain logic
are mixed inside `claude_cli_verification.py`.

### After

```
cli/commands/verify.py          # Orchestrator: calls 3 domain functions, formats output, computes exit code
cli/utils.py                    # + _get_status_symbols() (shared)
cli/parsers.py                  # + add_verify_parser() with --check-models flag

llm/providers/claude/claude_cli_verification.py   # Refactored: returns dict (no printing)
llm/providers/langchain/verification.py           # NEW: verify_langchain() → dict
llm/mlflow_logger.py                              # + verify_mlflow() → dict
```

**Key principle:** Domain functions return plain dicts. The CLI layer formats
output with `[OK]`/`[NO]` symbols. This keeps verification logic testable
independently of terminal output.

### Design Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Return type | Plain `dict[str, dict]` | No dataclass needed — 3 consumers, stable shape |
| Test prompt | Calls existing `ask_langchain()` | Validates the real code path, no duplication |
| API key env vars | `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY` | Matches existing backend resolution logic |
| API key masking | First 4 + last 4 chars (`sk-ab...7x2f`) | Enough to identify key without exposing it |
| MLflow probe | MLflow SDK (`set_tracking_uri` + `get_experiment_by_name`) | Most thorough — validates full connection |
| Exit code | Active provider determines pass/fail | If `provider=langchain` works, Claude CLI missing is informational |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/utils.py` | Add `_get_status_symbols()` (moved in Step 2) |
| `src/mcp_coder/cli/parsers.py` | Add `add_verify_parser()` with `--check-models` (Step 1) |
| `src/mcp_coder/cli/main.py` | Replace inline verify parser with `add_verify_parser()` call |
| `src/mcp_coder/cli/commands/verify.py` | Rewrite as orchestrator + formatter |
| `src/mcp_coder/llm/providers/claude/claude_cli_verification.py` | Refactor to return dict |

## Files Created

| File | Purpose |
|------|---------|
| `src/mcp_coder/llm/providers/langchain/verification.py` | `verify_langchain()` domain function |
| `tests/llm/providers/langchain/test_langchain_verification.py` | Tests for langchain verification |
| `tests/llm/test_mlflow_verify.py` | Tests for MLflow verification |
| `tests/cli/commands/test_verify_orchestration.py` | Tests for verify orchestrator + exit code logic |

## Files Updated (add function)

| File | Addition |
|------|----------|
| `src/mcp_coder/llm/mlflow_logger.py` | Add `verify_mlflow()` function |

## Implementation Steps

1. **Step 1** — Add verify parser to `parsers.py` with `--check-models` flag
2. **Step 2** — Extract `_get_status_symbols()` to `cli/utils.py`, refactor Claude CLI verification to return structured dict
3. **Step 3** — Create `verify_langchain()` domain function with tests
4. **Step 4** — Create `verify_mlflow()` domain function with tests
5. **Step 5** — Rewrite `cli/commands/verify.py` as orchestrator + formatter
