# Step 3 — Migrate `create-plan` + add `planning_mcp` label

**Reference:** `pr_info/steps/summary.md` §create-plan. Depends on Step 1 (independent of
Steps 2/4/5). Adds SIGTERM / `sys.exit(1)` / unexpected-exit labeling via the guard and routes
MCP-unavailable to the new `planning_mcp` label. One commit.

## WHERE

- Modify `src/mcp_coder/config/labels.json` (add `planning_mcp`)
- Modify `src/mcp_coder/workflows/create_plan/core.py`
- Delete `src/mcp_coder/workflows/create_plan/constants.py` (only held the enum + dataclass)
- Modify `tests/workflows/create_plan/test_main.py`, `.../test_prompt_execution.py`

## WHAT

`labels.json` — new entry (place beside `planning_llm_timeout`, mirror `plan_review_mcp`):

```json
{
  "internal_id": "planning_mcp",
  "name": "status-03f-mcp:planning-mcp-unavailable",
  "color": "e99695",
  "description": "MCP server(s) failed to connect during planning",
  "category": "human_action",
  "failure": true,
  "vscodeclaude": {
    "emoji": "🔌", "display_name": "PLANNING MCP UNAVAILABLE",
    "stage_short": "plan-mcp-fail", "commands": ["/check_branch_status"], "color": "red"
  }
}
```

`core.py`:

```python
FAILURE_LABELS: dict[str, str] = {
    "general": "planning_failed",
    "timeout": "planning_llm_timeout",
    "mcp_unavailable": "planning_mcp",
    "prereq": "planning_prereq_failed",
}
```

## HOW

- Replace `from .constants import FailureCategory, WorkflowFailure` with the shared
  `WorkflowFailure` (already imported as `SharedWorkflowFailure`) — drop the `SharedWorkflowFailure`
  alias and use `WorkflowFailure` directly.
- `run_planning_prompts`: collapse each prompt's **two** catches (`except LLMTimeoutError` +
  `except Exception` with inline `isinstance` MCP selection) into **one**
  `except Exception as e:` — `reason = llm_failure_reason(e) or "general"`;
  `message = format_mcp_unavailable_message(e) if isinstance(e, McpServersUnavailableError) else
  str(e)`; return `WorkflowFailure(category=FAILURE_LABELS[reason], stage="Prompt N (…)",
  message=message)`. Empty-response / no-session guards → `WorkflowFailure(category="planning_failed",
  stage="Prompt N (…)", …)`. Drop the `prompt_stage` field (the stage text already names the prompt).
- `_format_failure_comment(failure, diff_stat)` now takes the shared `WorkflowFailure`: header
  `## Planning Failed`, `**Stage:** {failure.stage}`, `**Error:** {failure.message}`, optional
  `**Elapsed:**` + `### Uncommitted Changes`. (No enum `.name`; no `prompt_stage` line.)
- `_handle_workflow_failure(failure, project_dir, …, issue_number)` keeps its signature but the
  `failure` is now the shared type (no conversion). Prereq/commit/push deliberate sites build
  `WorkflowFailure(category="planning_prereq_failed" | "planning_failed", …)`.
- Wrap the orchestrator body (prereqs → prompts → validate → commit/push → success label) in
  `run_guarded(body, project_dir=…, from_label_id="planning", general_category="planning_failed",
  comment_header="## Planning Failed", update_issue_labels=…, post_issue_comments=…,
  issue_number=issue_number)`. Each deliberate site keeps its `_handle_workflow_failure(...);
  return 1`. This nets `_load_prompt_or_exit → sys.exit(1)` and SIGTERM (new, intended).
- Delete `create_plan/constants.py`.

## ALGORITHM — prompt catch (×3, identical shape)

```
except Exception as e:
    reason = llm_failure_reason(e) or "general"
    msg = format_mcp_unavailable_message(e) if isinstance(e, McpServersUnavailableError) else str(e)
    return False, WorkflowFailure(FAILURE_LABELS[reason], f"Prompt {n} ({reason})", msg)
```

## DATA

- `FAILURE_LABELS: dict[str, str]` — create-plan taxonomy incl. non-LLM `prereq`.
- `run_planning_prompts` → `tuple[bool, WorkflowFailure | None]` (shared dataclass; category is
  the resolved label id).
- `run_create_plan_workflow` / `run_guarded` → `int`.

## TESTS (write/adjust first)

- `test_prompt_execution.py`: replace `FailureCategory.*` assertions with
  `failure.category == "planning_llm_timeout" | "planning_mcp" | "planning_failed"`. Add: inject
  `McpServersUnavailableError` at a prompt → category `planning_mcp` + message names servers;
  inject `LLMTimeoutError` → `planning_llm_timeout`; inject generic `RuntimeError` →
  `planning_failed`.
- `test_main.py`: migrate off local `WorkflowFailure`/`FailureCategory` imports; assert prereq →
  `planning_prereq_failed`. Add a guard test: a body escape / `sys.exit(1)` (patch a prompt to
  raise `SystemExit`) → `planning_failed` label + comment via the net.

## Verify

`run_pylint_check`, `run_pytest_check` (`-n auto` + unit-exclusion markers), `run_mypy_check`,
`run_lint_imports_check`. Optionally validate `labels.json` parses (run the label tests).

## LLM Prompt

> Implement Step 3 of `pr_info/steps/summary.md` per `pr_info/steps/step_3.md`. Add the
> `planning_mcp` label to `config/labels.json` (mirror `plan_review_mcp`, `status-03f-mcp`).
> Migrate `create_plan/core.py`: add the `FAILURE_LABELS` dict; collapse each of the three prompt
> catch blocks into one broadened `except Exception` that classifies via `llm_failure_reason` and
> routes MCP → `planning_mcp`; switch to the shared `WorkflowFailure`; wrap the orchestrator body
> in `run_guarded` (general `planning_failed`, from `planning`) so SIGTERM / `sys.exit(1)` /
> unexpected-exit are labeled; delete `create_plan/constants.py`. Follow TDD — update
> `test_prompt_execution.py` / `test_main.py` off `FailureCategory` to label-string assertions and
> add the MCP/timeout/generic + guard cases first, then implement. Run pylint, pytest (`-n auto`
> with unit-exclusion markers), mypy, and lint-imports. Produce exactly one commit.
