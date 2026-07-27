# Summary — Consolidate LLM-failure handling onto one shared harness (#1096)

## Goal

Bring all four autonomous workflows — `implement`, `create-plan`, `create-pr`, and the
shared `review` engine (`review-plan` + `review-implementation`) — onto **one robust,
consolidated LLM-failure contract**. Today `implement` is robust; the others let a
non-timeout/non-MCP exception escape unlabeled to the CLI boundary (the concrete #1042
`review-plan` silent death). After this change **no exception from any LLM call site in any
of the four workflows can reach the CLI uncategorized** — every terminal failure (including
SIGTERM / unexpected exit) sets a workflow label and (when enabled) posts a comment.

## Architectural / design changes

### 1. One shared harness in `workflow_utils/failure_handling.py`

Three primitives, used by all four workflows:

- **`llm_failure_reason(exc) -> "timeout" | "mcp_unavailable" | None`** — the single
  exception→reason classifier (moved here from `implement/llm_failures.py`, which is
  deleted). Canonical reason string is `"mcp_unavailable"`.
- **`WorkflowFailure(category: str, stage, message, elapsed_time)`** — the existing shared
  dataclass becomes the **only** one. Per-workflow context (tasks done/total, prompt stage,
  review round/verdict) is **not** added to it; it is carried in each workflow's comment text
  (built at the deliberate `_fail` call site, where the values are live locals).
- **`run_guarded(body, …) -> int`** — the reusable safety net, extracted from `implement`'s
  SIGTERM handler + terminal-state flag + `finally`, packaged as a **runner callback**:

  ```python
  def run_guarded(
      body: Callable[[], int],
      *,
      project_dir: Path,
      from_label_id: str,          # busy label, e.g. "implementing"
      general_category: str,       # general failure label, e.g. "implementing_failed"
      comment_header: str,         # generic net-comment header
      build_comment: Callable[[GuardOutcome], str] | None = None,
      update_issue_labels: bool = False,
      post_issue_comments: bool = False,
      issue_number: int | None = None,
  ) -> int: ...
  ```

  **Contract:**
  - A **clean return from `body()` — any exit code (`0` or `1`) — is terminal**; the net
    stays silent. Every deliberate `_fail(...); return 1` site is therefore automatically
    terminal. No `mark_terminal()` bookkeeping.
  - The net fires **only on an escape**: an unexpected `Exception`, or `SystemExit`
    (SIGTERM → `sys.exit`). It builds `WorkflowFailure(category=general_category, …)` with a
    generic stage/message (the MCP-unavailable vs SIGTERM vs "unexpected exit" selection lives
    **once**, in the runner), posts the comment, and returns `1`. `SystemExit` is **re-raised**
    after netting (preserves `implement`'s SIGTERM parity; also nets create-plan's
    `_load_prompt_or_exit → sys.exit(1)`).
  - **The net always maps to the *general* label.** Precise `timeout`/`mcp_unavailable` labels
    come only from the deliberate in-body `except → llm_failure_reason → _fail` paths.
  - `run_guarded` owns its own `start_time` (for the net's elapsed) and the SIGTERM
    install/restore.

### 2. KISS decision — no cross-scope "mutable progress handle" except in `implement`

The issue floated a mutable progress handle in three workflows so the **net-path** comment
could show live progress. That is the plan's trickiest mechanism. We **confine it to
`implement` only** (to keep `implement` a literal pure refactor — its SIGTERM/crash comment
keeps its `Progress: X/Y` line via a small mutable `Progress` object read by its
`build_comment` closure). For `review`, `create-plan`, and `create-pr` the net path is **new**
behavior (no prior comment content to preserve), so their net comment is generic
(`comment_header` + stage + message + elapsed). All **deliberate** failure comments — the
common case in every workflow — are built from live locals passed as plain args, so no
cross-scope handle is needed there.

### 3. Collapse the duplicated failure types

- Delete `implement/constants.py` and `create_plan/constants.py` `FailureCategory` enums and
  their private `WorkflowFailure` dataclasses. Delete the four classifier copies
  (`implement/llm_failures.py`, `review/core.py::_reason_for_exception`, and the inline
  `isinstance(e, McpServersUnavailableError)` selection in `create_plan`/`create_pr`).
- Each workflow keeps a plain **`reason → label_id` dict** (labels stay stage-specific data —
  see below). `review` already has this shape (`config.failure_labels`);
  `implement`/`create-plan` get a module-level `FAILURE_LABELS`; `create-pr` maps at its one
  LLM catch site.

### 4. Broadened `except` at every LLM call site

Every narrow `except (LLMTimeoutError, McpServersUnavailableError)` becomes
`except Exception as exc: … llm_failure_reason(exc) or <general>`, so a **generic** exception
is categorized at the call site (general label + comment) instead of escaping. In review's
`_after_steps` the broaden is scoped to the `check_and_fix_ci` call so it does not swallow the
`"rebase"`/`"ci"` control-flow reasons.

### 5. review-specific: empty-report retry + rename + enriched comment

- Bounded **inner retry (N = 3)** on a whitespace-only reviewer report only — re-invokes the
  fresh reviewer, **does not consume a `REVIEW_MAX_ROUNDS` round**; on exhaustion fail with the
  **general** label. Never retries exceptions/timeouts.
- Rename reason key `"mcp"` → `"mcp_unavailable"` in both `ReviewConfig.failure_labels` and in
  `_after_steps`'s return (load-bearing after the broaden).
- Enrich the deliberate `_fail` comment with round number, last verdict, and elapsed time
  (plain args — no mutable handle).

### 6. Label taxonomy gaps (`config/labels.json`)

Add three stage-specific failure labels so every stage has the full general/timeout/mcp set,
each with its `vscodeclaude` TUI block mirroring existing `*_timeout`/`*_mcp` entries:
`planning_mcp` (`status-03f-mcp`), `pr_creating_timeout` (`status-09f-timeout`),
`pr_creating_mcp` (`status-09f-mcp`). **Labels stay stage-specific — code is unified, labels
are not merged.**

### Constraints honored

- Import direction stays downward (`workflows → workflow_utils`; `failure_handling.py` already
  imports the MCP error from `llm`, add the `LLMTimeoutError` import). Re-run import-linter
  layer + `mcp_coder_utils_isolation` contracts after the move.
- `implement` prereq returns stay **unlabeled** (behavior unchanged; deferred).
- MLflow orphan run is pipeline-owned — **out of scope**.
- `create-pr` test seams `core._handle_create_pr_failure` / `core._format_failure_comment` are
  preserved on the **deliberate** paths (tests patch them by name); the net path asserts guard
  behavior instead.
- `check_and_fix_ci` already re-raises the typed LLM errors (verify only); its analysis-phase
  generic-exception swallow (`ci.py:143 → return None`) is unchanged.

## Behavior deltas (intended)

| Workflow | Change |
|----------|--------|
| `implement` | **Pure refactor** — externally observable behavior unchanged. |
| `create-plan` | **Gains** SIGTERM + `sys.exit(1)` (prompt-load) + unexpected-exit labeling via the guard; MCP-unavailable now routes to `planning_mcp` (was generic `planning_failed`). |
| `create-pr` | **Gains** SIGTERM + unexpected-exit labeling via the guard; summary-generation timeout/MCP now route to `pr_creating_timeout`/`pr_creating_mcp` (was collapsed to `pr_creating_failed`). |
| `review` (both) | **Gains** the entire failure net (was the #1042 hole): generic-exception categorization at every LLM site, empty-report retry, and a failure comment with round/verdict/elapsed. |

## Files created / modified

### Shared harness
- **Modify** `src/mcp_coder/workflow_utils/failure_handling.py` — add `LLMTimeoutError` import,
  `llm_failure_reason`, `GuardOutcome`, `run_guarded`.
- **Modify** `tests/workflow_utils/test_failure_handling.py` — add `llm_failure_reason` tests.
- **Create** `tests/workflow_utils/test_run_guarded.py` — `run_guarded` unit tests.

### implement
- **Modify** `src/mcp_coder/workflows/implement/core.py` — `finally`-net → `run_guarded`;
  `body()` closure; local `fail` partial; `Progress` mutable holder for the net comment.
- **Modify** `src/mcp_coder/workflows/implement/constants.py` — delete `FailureCategory` enum +
  private `WorkflowFailure` (keep all other constants).
- **Modify** `src/mcp_coder/workflows/implement/failure_reporting.py` — `FAILURE_LABELS` dict,
  `format_failure_comment(...)` (context as args), `_fail(...) -> int`.
- **Modify** `src/mcp_coder/workflows/implement/task_processing.py` — import
  `llm_failure_reason` from `workflow_utils`.
- **Delete** `src/mcp_coder/workflows/implement/llm_failures.py`.
- **Delete** `tests/workflows/implement/test_llm_failures.py` (coverage moves to
  `test_failure_handling.py`).

### create-plan
- **Modify** `src/mcp_coder/workflows/create_plan/core.py` — `run_guarded`; module
  `FAILURE_LABELS`; 3 prompt catch sites → single broadened `except` using the classifier;
  shared `WorkflowFailure`.
- **Delete** `src/mcp_coder/workflows/create_plan/constants.py` (only held the enum + dataclass).
- **Modify** `tests/workflows/create_plan/test_main.py`, `.../test_prompt_execution.py` —
  migrate off `FailureCategory`/local `WorkflowFailure` to label-string assertions.
- **Modify** `src/mcp_coder/config/labels.json` — add `planning_mcp`.

### create-pr
- **Modify** `src/mcp_coder/workflows/create_pr/core.py` — `run_guarded`; classify at
  `summary_generation`; keep deliberate-path seams.
- **Modify** `src/mcp_coder/workflows/create_pr/helpers.py` — `handle_create_pr_failure` /
  `WorkflowFailure` accept a `category`.
- **Modify** `tests/workflows/create_pr/test_failure_handling.py` — new-label assertions;
  migrate net-path seam test to guard-behavior test.
- **Modify** `src/mcp_coder/config/labels.json` — add `pr_creating_timeout`, `pr_creating_mcp`.

### review
- **Modify** `src/mcp_coder/workflows/review/core.py` — loop wrapped in `run_guarded`;
  broadened `except` sites; `_after_steps` CI-gate broaden; delete `_reason_for_exception`;
  empty-report retry; enriched `_fail`.
- **Modify** `src/mcp_coder/workflows/review/config.py` — rename `"mcp"` → `"mcp_unavailable"`
  in both `failure_labels`.
- **Modify** `tests/workflows/review/test_core.py`, `.../test_core_after_steps.py` — new
  failure-path coverage.

## Suggested sequencing (one commit per step)

1. **Step 1** — Shared primitives (`llm_failure_reason` move + `run_guarded`) + unit tests.
   Additive; no behavior change.
2. **Step 2** — Migrate `implement` onto `run_guarded` + `FAILURE_LABELS`; delete
   `llm_failures.py` + enum/dataclass. Pure refactor.
3. **Step 3** — Migrate `create-plan`; add `planning_mcp`.
4. **Step 4** — Migrate `create-pr`; add `pr_creating_timeout` + `pr_creating_mcp`.
5. **Step 5** — Enhance `review` (guard + broadened excepts + empty-report retry + rename +
   enriched comment).

Steps 3–5 are independent of each other; all depend on Step 1. Each step lands independently
green (pylint + pytest + mypy).
