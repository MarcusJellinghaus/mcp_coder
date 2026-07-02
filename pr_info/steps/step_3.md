# Step 3 — Timeout sweep: inactivity budgets for every blocking caller

**Reference:** See [summary.md](./summary.md) (Architectural change 2, Requirement 1). After Step 2
the blocking `timeout` param already means *inactivity*; this step makes each site's value a
**conscious, documented** inactivity budget and introduces the new constant for the unattended
sites. No behavior change beyond the numbers/names — pure config + comments.

## WHERE
- `src/mcp_coder/workflows/implement/constants.py` — add `LLM_INACTIVITY_TIMEOUT_SECONDS`; remove
  the stale `# Note: CI fix uses ... 3600s` comment; handle now-unused
  `LLM_IMPLEMENTATION_TIMEOUT_SECONDS`.
- `src/mcp_coder/workflows/implement/task_processing.py` — implement task (`process_single_task`)
  and mypy-fix (`check_and_fix_mypy`) use `LLM_INACTIVITY_TIMEOUT_SECONDS`.
- `src/mcp_coder/workflows/implement/ci_operations.py` — CI-fix (`_run_ci_fix`) uses
  `LLM_INACTIVITY_TIMEOUT_SECONDS`; CI-analysis keeps `LLM_CI_ANALYSIS_TIMEOUT_SECONDS = 300`,
  re-documented as an inactivity budget.
- `src/mcp_coder/workflows/create_plan/core.py`, `src/mcp_coder/workflows/create_pr/core.py`,
  `src/mcp_coder/workflows/implement/core.py` (finalisation + task-tracker-prep) — doc comments
  noting the numbers are now inactivity budgets below the CI step cap.
- Tests: `tests/workflows/implement/test_constants.py`, plus any test asserting the timeout value
  passed to `prompt_llm` at these sites.

## WHAT
```
LLM_INACTIVITY_TIMEOUT_SECONDS = 300  # 5-minute inactivity budget for unattended claude -p calls
```
Repoint the **three unattended sites** (implement task, mypy-fix, CI-fix) from
`LLM_IMPLEMENTATION_TIMEOUT_SECONDS` to `LLM_INACTIVITY_TIMEOUT_SECONDS`.

## HOW
- `LLM_IMPLEMENTATION_TIMEOUT_SECONDS` must **not** be relabeled. After repointing it is unused;
  either delete it or add it to `vulture_whitelist.py` — do not change its value or meaning.
- Keep every other caller's existing number (create-plan `600`, create-pr, finalisation `600`,
  task-tracker-prep `600`, CI-analysis `300`) and add a one-line comment per site: "inactivity
  budget (was wall-clock), kept below the CI step cap." No overall wall-clock cap anywhere.

## ALGORITHM
_None — configuration + comment changes only._

## DATA
- New module constant `LLM_INACTIVITY_TIMEOUT_SECONDS: int = 300`.
- No change to any function signature or return value.

## TESTS (write first)
- `test_constants.py`: `LLM_INACTIVITY_TIMEOUT_SECONDS == 300`; document its meaning.
- Update tests that assert the timeout argument at the repointed sites (implement task, mypy-fix,
  CI-fix) to expect `LLM_INACTIVITY_TIMEOUT_SECONDS`.
- If `LLM_IMPLEMENTATION_TIMEOUT_SECONDS` is deleted, remove its assertions; if whitelisted, add
  the vulture entry.

## LLM PROMPT
> Implement Step 3 from `pr_info/steps/step_3.md` (see `pr_info/steps/summary.md`). Add
> `LLM_INACTIVITY_TIMEOUT_SECONDS = 300` in `workflows/implement/constants.py` and repoint the
> three unattended `prompt_llm` sites (implement task in `task_processing.py`, mypy-fix in
> `task_processing.py`, CI-fix `_run_ci_fix` in `ci_operations.py`) to it. Re-document CI-analysis
> 300 and the create-plan/create-pr/finalisation/task-tracker-prep timeouts as inactivity budgets;
> remove the stale CI comment in `constants.py`. Do NOT relabel `LLM_IMPLEMENTATION_TIMEOUT_SECONDS`
> — delete it if unused or vulture-whitelist it. Add no wall-clock cap. Update the affected timeout
> tests first (TDD). pylint/pytest(`-n auto`)/mypy green, one commit.
