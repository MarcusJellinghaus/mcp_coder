# Step 3 — Timeout sweep: inactivity budgets for every blocking caller

**Reference:** See [summary.md](./summary.md) (Architectural change 2, Requirement 1). After Step 2
the blocking `timeout` param already means *inactivity*; this step makes each site's value a
**conscious, documented** inactivity budget and introduces the new constant for the tool-using
sites. No behavior change beyond the numbers/names — pure config + comments.

**Two categories (state this rationale in the plan):**
- **Tool-using autonomous sites** (implement, mypy-fix, CI-fix) run `claude` with MCP tools; a single
  silent MCP tool call (e.g. a multi-minute `run_pytest`) can produce no stdout line for well over
  300s. These use the new `LLM_INACTIVITY_TIMEOUT_SECONDS = 600`.
- **Pure-LLM sites** (CI-analysis `300`, commit-msg `120`) call the LLM with no MCP tools; an LLM
  emits a token quickly, so a lower inactivity budget is safe. These keep their existing values.

Every value is an **inactivity/silence** budget (max seconds with no stdout line from `claude`), NOT
wall-clock, and is kept **below** the external CI step/build cap so mcp-coder kills a hung call before
the external watchdog SIGKILLs it.

## WHERE
- `src/mcp_coder/workflows/implement/constants.py` — add `LLM_INACTIVITY_TIMEOUT_SECONDS = 600`
  (commented); remove the stale `# Note: CI fix uses ... 3600s` comment at `constants.py:36`; handle
  now-unused `LLM_IMPLEMENTATION_TIMEOUT_SECONDS` (do **not** relabel/mutate — 3600 wall-clock must
  not leak into the streaming sites). Keep `LLM_CI_ANALYSIS_TIMEOUT_SECONDS = 300`,
  `LLM_FINALISATION_TIMEOUT_SECONDS = 600`, `LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS = 600` —
  re-document each as an inactivity budget.
- `src/mcp_coder/workflows/implement/task_processing.py` — implement task (`process_single_task`)
  and mypy-fix (`check_and_fix_mypy`) use `LLM_INACTIVITY_TIMEOUT_SECONDS`. Remove the now-unused
  `LLM_IMPLEMENTATION_TIMEOUT_SECONDS` import.
- `src/mcp_coder/workflows/implement/ci_operations.py` — CI-fix (`_run_ci_fix`) uses
  `LLM_INACTIVITY_TIMEOUT_SECONDS`; CI-analysis keeps `LLM_CI_ANALYSIS_TIMEOUT_SECONDS = 300`,
  re-documented as an inactivity budget. Remove the now-unused `LLM_IMPLEMENTATION_TIMEOUT_SECONDS`
  import.
- `src/mcp_coder/workflows/create_plan/core.py` — BOTH hard-coded `timeout=600` calls AND
  `PROMPT_3_TIMEOUT` (`create_plan/core.py:53`): lower `PROMPT_3_TIMEOUT` 900 → 600 for uniformity;
  document all create-plan timeouts as inactivity budgets.
- `src/mcp_coder/workflows/create_pr/core.py` — actual value is `timeout=300` (not 600): document as
  an inactivity budget.
- `src/mcp_coder/workflows/implement/core.py` (finalisation `LLM_FINALISATION_TIMEOUT_SECONDS = 600`
  + task-tracker-prep `LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS = 600`) — doc comments noting the
  numbers are now inactivity budgets below the CI step cap.
- `src/mcp_coder/utils/workflow_utils/commit_operations.py` — commit-msg
  `LLM_COMMIT_TIMEOUT_SECONDS = 120` (`commit_operations.py:19`): keep 120 (pure-LLM), re-document as
  an inactivity budget. (This site was missing from the plan.)
- Tests: `tests/workflows/implement/test_constants.py`, plus any test asserting the timeout value
  passed to `prompt_llm` at these sites, and any heartbeat-related test asserts referencing the old
  blocking wall-clock behavior (remove those).

## WHAT
```
# Inactivity/silence budget (max seconds with no stdout line from `claude`), NOT wall-clock.
# 600s gives headroom for a long *silent* MCP tool call (e.g. a multi-minute run_pytest) at the
# tool-using autonomous sites (implement, mypy-fix, CI-fix). Kept below the external CI step/build
# cap so mcp-coder kills a hung call before the external watchdog SIGKILLs it.
LLM_INACTIVITY_TIMEOUT_SECONDS = 600
```
Repoint the **three tool-using sites** (implement task, mypy-fix, CI-fix) from
`LLM_IMPLEMENTATION_TIMEOUT_SECONDS` to `LLM_INACTIVITY_TIMEOUT_SECONDS`.

## HOW
- `LLM_IMPLEMENTATION_TIMEOUT_SECONDS` (3600 wall-clock) must **not** be relabeled or mutated — it
  must not leak into the streaming sites. After repointing it is unused; either delete it or add it
  to `vulture_whitelist.py`. Its now-unused imports in `task_processing.py` and `ci_operations.py`
  must both be removed.
- Enumerate and re-document **every** blocking caller with a per-site inactivity-budget comment
  ("inactivity budget (was wall-clock), kept below the CI step cap"):
  * create-plan `core.py`: both hard-coded `timeout=600` calls **and** `PROMPT_3_TIMEOUT` — lower
    `PROMPT_3_TIMEOUT` 900 → 600 for uniformity.
  * create-pr `core.py`: `timeout=300`.
  * finalisation `LLM_FINALISATION_TIMEOUT_SECONDS = 600`, task-tracker-prep
    `LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS = 600`: keep 600.
  * CI-analysis `LLM_CI_ANALYSIS_TIMEOUT_SECONDS = 300`: keep 300 (pure-LLM, no MCP tools).
  * commit-msg `LLM_COMMIT_TIMEOUT_SECONDS = 120`: keep 120 (pure-LLM).
- **Rationale for the split:** tool-using sites need >300s headroom for silent MCP tool calls;
  pure-LLM sites (CI-analysis, commit-msg) can stay lower because an LLM emits a token quickly.
- No overall wall-clock cap anywhere.

## ALGORITHM
_None — configuration + comment changes only._

## DATA
- New module constant `LLM_INACTIVITY_TIMEOUT_SECONDS: int = 600`.
- `create_plan/core.py` `PROMPT_3_TIMEOUT` lowered 900 → 600.
- No change to any function signature or return value.

## TESTS (write first)
- `test_constants.py`: `LLM_INACTIVITY_TIMEOUT_SECONDS == 600`; document its meaning.
- Update tests that assert the timeout argument at the repointed sites (implement task, mypy-fix,
  CI-fix) to expect `LLM_INACTIVITY_TIMEOUT_SECONDS`.
- `create_plan` test asserting `PROMPT_3_TIMEOUT` → expect `600`.
- If `LLM_IMPLEMENTATION_TIMEOUT_SECONDS` is deleted, remove its assertions; if whitelisted, add
  the vulture entry.
- Remove any heartbeat-related test asserts that reference the old blocking wall-clock behavior.

## LLM PROMPT
> Implement Step 3 from `pr_info/steps/step_3.md` (see `pr_info/steps/summary.md`). Add
> `LLM_INACTIVITY_TIMEOUT_SECONDS = 600` in `workflows/implement/constants.py` (with the commented
> inactivity-budget rationale) and repoint the three tool-using `prompt_llm` sites (implement task in
> `task_processing.py`, mypy-fix in `task_processing.py`, CI-fix `_run_ci_fix` in `ci_operations.py`)
> to it. Re-document every other blocking caller as an inactivity budget: create-plan `core.py` (both
> `timeout=600` calls; lower `PROMPT_3_TIMEOUT` 900 → 600), create-pr `core.py` (`timeout=300`),
> finalisation/task-tracker-prep (`600`), CI-analysis (`300`, pure-LLM), and commit-msg
> `LLM_COMMIT_TIMEOUT_SECONDS = 120` in `utils/workflow_utils/commit_operations.py` (pure-LLM).
> Remove the stale CI comment at `constants.py:36`. Do NOT relabel/mutate
> `LLM_IMPLEMENTATION_TIMEOUT_SECONDS` (3600 wall-clock) — delete it if unused or vulture-whitelist
> it, and remove its now-unused imports in `task_processing.py` and `ci_operations.py`. Add no
> wall-clock cap. Update the affected timeout tests first (TDD) and drop stale heartbeat wall-clock
> asserts. pylint/pytest(`-n auto`)/mypy green, one commit.
