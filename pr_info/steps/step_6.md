# Step 6 — Categorize at CI sites: CI-analysis propagates, CI-fix absorbs

**Reference:** See [summary.md](./summary.md) (Decisions 9 & 10). The final two autonomous sites.
CI-analysis surfaces timeout/MCP-unavailable as `llm_timeout`/`mcp_unavailable`; CI-fix keeps
absorbing them into its 4-attempt loop → `ci_fix_needed`. Depends on Steps 2, 4 & 5.

## WHERE
- `src/mcp_coder/workflows/implement/ci_operations.py` — `_run_ci_analysis`, `_run_ci_fix`,
  `check_and_fix_ci`.
- `src/mcp_coder/workflows/implement/core.py` — wrap the `check_and_fix_ci` call (Step 5.6).
- Tests: `tests/workflows/implement/test_ci_operations.py`, `test_core.py`.

## WHAT
- `_run_ci_analysis(...) -> Optional[str]` — **stops swallowing** `LLMTimeoutError` /
  `McpServersUnavailableError`; they propagate out of `check_and_fix_ci`.
- `_run_ci_fix(...) -> bool` — keeps swallowing both (its existing broad `except Exception` already
  returns `False`, i.e. one failed attempt); add an intent comment. This IS Decision 10 — no logic
  change.
- `check_and_fix_ci(...) -> bool` — lets the analysis exceptions propagate (no new catch).
- `core.py` — wrap `check_and_fix_ci(...)`; on the two exceptions, categorize
  `llm_timeout`/`mcp_unavailable`.

## HOW
- In `_run_ci_analysis`, before the generic `except Exception`, add
  `except (LLMTimeoutError, McpServersUnavailableError): raise`.
- In `core.py` Step 5.6:
  `try: ci_success = check_and_fix_ci(...) except (LLMTimeoutError, McpServersUnavailableError) as
  e: _handle_workflow_failure(WorkflowFailure(category=REASON_TO_CATEGORY[llm_failure_reason(e)],
  ...)); return 1`.
- Because `_run_ci_fix` swallows the same exceptions, a fix-phase timeout/MCP-unavailable never
  reaches this wrapper — it becomes one failed attempt → `ci_fix_needed` on exhaustion.

## ALGORITHM
```
# _run_ci_analysis
except (LLMTimeoutError, McpServersUnavailableError):
    raise                      # abort -> categorized in core.py
except Exception:
    return None                # existing: soft-fail analysis
# _run_ci_fix  (unchanged)
except Exception:
    return False               # absorb -> one failed attempt (Decision 10)
```

## DATA
- No signature changes.
- Analysis-phase timeout/MCP-unavailable → `LLM_TIMEOUT` / `MCP_UNAVAILABLE` label (terminal).
- Fix-phase timeout/MCP-unavailable → absorbed → `CI_FIX_EXHAUSTED` (`ci_fix_needed`) after 4 tries.

## TESTS (write first)
- `_run_ci_analysis` raising `LLMTimeoutError` propagates through `check_and_fix_ci` to `core.py`,
  which sets the `llm_timeout` label; same for `McpServersUnavailableError` → `mcp_unavailable`.
- `_run_ci_fix` raising either exception is absorbed as one failed attempt; four exhausted attempts
  → `ci_fix_needed` (no `llm_timeout`/`mcp_unavailable` abort).

## LLM PROMPT
> Implement Step 6 from `pr_info/steps/step_6.md` (see `pr_info/steps/summary.md`). Make
> `_run_ci_analysis` re-raise `LLMTimeoutError` / `McpServersUnavailableError` (stop swallowing them)
> and wrap the `check_and_fix_ci` call in `core.py` (Step 5.6) to categorize them as
> `llm_timeout` / `mcp_unavailable` via `REASON_TO_CATEGORY`. Leave `_run_ci_fix` absorbing both
> (Decision 10 — add only an intent comment). Write tests first proving analysis-phase aborts are
> categorized while fix-phase failures are absorbed into the 4-attempt loop → `ci_fix_needed`.
> pylint/pytest(`-n auto`)/mypy green, one commit.
