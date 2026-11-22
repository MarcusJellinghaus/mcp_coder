# Step 8 — Implement: auth at finalisation and the CI step

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_8.md` only. Steps 1–7
> are done. Write the tests first, then the code. Run pylint, pytest (`-n auto`, fast unit
> markers), mypy; run `run_format_code`; run `check_file_size`. Make one commit.

## WHERE

- `src/mcp_coder/workflows/implement/core.py`: the Step 5.5 (`run_finalisation`) and Step 5.6
  (`check_and_fix_ci`) blocks in `run_implement_workflow.body`.
- Tests: extend `tests/workflows/implement/test_core_auth.py` (created in step 7).

## WHAT / ALGORITHM

```
# Step 5.5 — auth only; timeout/MCP handling around finalisation is unchanged (out of scope)
try:
    finalisation_success = run_finalisation(project_dir, provider, mcp_config, settings_file)
except LLMAuthError as exc:
    return fail("auth", stage="Finalisation", message=exception_summary(exc))

# Step 5.6 — extend the existing tuple
except (LLMAuthError, LLMTimeoutError, McpServersUnavailableError) as exc:
    reason = llm_failure_reason(exc) or "general"
    message = exception_summary(exc) if reason == "auth" else "LLM failure during CI failure analysis"
    return fail(reason, stage="CI pipeline analysis", message=message)
```

## HOW

- Import `LLMAuthError` from `mcp_coder.llm.interface` (it is already imported in step 7
  if `core.py` needed it; otherwise add it), and `exception_summary` from
  `mcp_coder.workflow_utils.failure_handling`.
- Rewrite the CI comment above the `try` to describe the new behaviour without counting
  reasons: "The shared CI step re-raises the typed LLM failures from the analysis phase, and
  auth from the fix phase too; categorize them here."
- The stage label "CI pipeline analysis" also covers fix-phase auth. This is accepted.

## DATA

- `fail("auth", stage="Finalisation" | "CI pipeline analysis", message="LLMAuthError: Run `claude`, then `/login`. …")`
  → label `implementing_failed`, category "Auth".

## Tests (first) — `test_core_auth.py`

- `run_finalisation` raises `LLMAuthError(AUTH_MESSAGE)` → the workflow returns 1 via `_fail`
  with reason `auth`, stage "Finalisation", and the message with the hint. It is not the
  `run_guarded` "Crashed" net, and `check_and_fix_ci` is not called.
- `check_and_fix_ci` raises `LLMAuthError(AUTH_MESSAGE)` → `_fail` with reason `auth`,
  stage "CI pipeline analysis", and the message containing the hint. This covers both the
  CI analysis and the CI fix phase, which both surface here once step 9 re-raises.
- `check_and_fix_ci` raising `LLMTimeoutError` still gives the message
  `"LLM failure during CI failure analysis"` (regression guard).
