# Plan Update Decisions

Decisions made during plan refinement after initial draft.

## Step structure: 5 → 3

- **Merge old step 3 + 4 + 5 into a single new step 3.**
  - Old step 3 (helpers only) leaves `_handle_workflow_failure` and `_format_failure_comment` as dead code with no callers — vulture would flag them. They must land with the orchestration that uses them.
  - Old step 5 was a one-line CLI help text change — too small for a standalone commit.
  - Result: 3 steps total (LLM timeout fix; package refactor + labels; failure handling + wiring + CLI help).

## Helper signatures: match implement's pattern exactly

- **`_handle_workflow_failure` drops the `issue_number` parameter.** The shared `handle_workflow_failure()` auto-resolves issue_number from the current branch — passing it explicitly diverges from implement.
- **`_format_failure_comment(failure, diff_stat: str)`.** Caller computes `diff_stat` and passes it in; this matches implement and simplifies tests (no need to mock `get_diff_stat` per test).

## Frozen dataclass: use `dataclasses.replace`

- `WorkflowFailure` is `@dataclass(frozen=True)`. When the orchestrator overrides `elapsed_time` on a failure returned from `run_planning_prompts()`, it must use `dataclasses.replace(failure, elapsed_time=elapsed)` — direct mutation will raise `FrozenInstanceError`.

## Stage label strings: exact match to issue #336 §4

- Use the full strings from the issue, not shortened forms:
  - `"Prerequisites (git working directory not clean)"`
  - `"Prerequisites (issue not found)"`
  - `"Workspace setup (pr_info/ already exists)"`
  - `"Workspace setup (directory creation failed)"`
  - `"Branch management (branch creation failed)"`

## Step 1: enumerate updated tests

- Step 1's "2 new tests" was misleading because 2 existing tests also need updating. Updated to "2 new + 2 updated" with the test names enumerated (`test_prompt_llm_timeout_expired_reraised`, `test_prompt_llm_asyncio_timeout_reraised_for_langchain`).

## Step 2: post-refactor grep + label test assertion

- Add an explicit sub-task to grep `tests/workflows/create_plan/` for any leftover `mcp_coder.workflows.create_plan.<name>` references after the refactor, to catch missed patch paths.
- Verify the existing label-config test covers the 2 new label internal IDs (`planning_llm_timeout`, `planning_prereq_failed`); add a minimal assertion if missing.

## `import time` placement

- `import time` is module-level in `core.py`; `start_time = time.time()` is function-local inside `run_create_plan_workflow()`. Called out explicitly to avoid confusion.

## `check_prerequisites` failure bifurcation

- `check_prerequisites` failure bifurcation: orchestrator pre-checks `is_working_directory_clean` before calling `check_prerequisites`, so each call site maps 1:1 to a specific stage label. Avoids changing the helper's return type.
