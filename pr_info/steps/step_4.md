# Step 4 — Migrate `create-pr` + add `pr_creating_timeout` / `pr_creating_mcp`

**Reference:** `pr_info/steps/summary.md` §create-pr. Depends on Step 1 (independent of
Steps 2/3/5). Replaces the hand-rolled `reached_terminal_state` + `finally` with `run_guarded`
and classifies the summary-generation LLM failure into distinct labels. Preserves the
`core._handle_create_pr_failure` / `core._format_failure_comment` patch seams on the
**deliberate** paths. One commit.

## WHERE

- Modify `src/mcp_coder/config/labels.json` (add `pr_creating_timeout`, `pr_creating_mcp`)
- Modify `src/mcp_coder/workflows/create_pr/helpers.py`
- Modify `src/mcp_coder/workflows/create_pr/core.py`
- Modify `tests/workflows/create_pr/test_failure_handling.py`

## WHAT

`labels.json` — two new entries beside `pr_creating_failed` (mirror the `*_timeout` / `*_mcp`
shape):

```json
{ "internal_id": "pr_creating_timeout", "name": "status-09f-timeout:pr-creating-llm-timeout",
  "color": "e99695", "description": "LLM timed out during PR creation", "category": "human_action",
  "failure": true, "vscodeclaude": { "emoji": "⏱️", "display_name": "PR CREATION LLM TIMEOUT",
  "stage_short": "pr-timeout", "commands": ["/check_branch_status"], "color": "red" } },
{ "internal_id": "pr_creating_mcp", "name": "status-09f-mcp:pr-creating-mcp-unavailable",
  "color": "e99695", "description": "MCP server(s) failed to connect during PR creation",
  "category": "human_action", "failure": true, "vscodeclaude": { "emoji": "🔌",
  "display_name": "PR CREATION MCP UNAVAILABLE", "stage_short": "pr-mcp-fail",
  "commands": ["/check_branch_status"], "color": "red" } }
```

`helpers.py` — thread an optional category (default preserves current behavior):

```python
def handle_create_pr_failure(..., category: str = "pr_creating_failed") -> None: ...
    #   failure = WorkflowFailure(category=category, stage=stage, message=message, elapsed_time=elapsed_time)
```

## HOW

- `helpers.handle_create_pr_failure`: add `category: str = "pr_creating_failed"` (last kwarg) and
  pass it to `WorkflowFailure(category=category, …)`. `format_failure_comment` is unchanged.
- `core.py`: wrap the Step 1–5 body in `def body() -> int:` and call
  `run_guarded(body, project_dir=…, from_label_id="pr_creating", general_category="pr_creating_failed",
  comment_header="## PR Creation Failed", update_issue_labels=…, post_issue_comments=…,
  issue_number=cached_issue_number)`. Resolve `cached_issue_number` (the pre-body linkage lookup)
  **before** calling `run_guarded`. Remove `reached_terminal_state` and the old `finally`.
- Deliberate paths keep calling `_handle_create_pr_failure(...)` (the module-level seam) and then
  `return 1` — the seam is preserved for tests that patch it by name.
- At the `summary_generation` catch, classify:

  ```
  reason = llm_failure_reason(e)
  category = {"timeout": "pr_creating_timeout", "mcp_unavailable": "pr_creating_mcp"}.get(reason, "pr_creating_failed")
  message = format_mcp_unavailable_message(e) if isinstance(e, McpServersUnavailableError) else str(e)
  _handle_create_pr_failure(stage="summary_generation", message=message, category=category, …); return 1
  ```

- The **net** path (unexpected escape / SIGTERM) no longer routes through
  `_handle_create_pr_failure`; `run_guarded` calls `handle_workflow_failure` directly with the
  generic `## PR Creation Failed` comment and the `pr_creating_failed` label.

## ALGORITHM — orchestrator skeleton

```
cached_issue_number = validate_branch_issue_linkage(...) if update_issue_labels else None
def body() -> int:
    ... Step1..Step5 ; each deliberate failure: _handle_create_pr_failure(...); return 1
    return 0
return run_guarded(body, project_dir=..., from_label_id="pr_creating",
                   general_category="pr_creating_failed", comment_header="## PR Creation Failed",
                   update_issue_labels=..., post_issue_comments=..., issue_number=cached_issue_number)
```

## DATA

- `handle_create_pr_failure(..., category="pr_creating_failed")` → `None`.
- `run_create_pr_workflow` / `run_guarded` → `int`.
- Reason→label map at the summary catch: `{"timeout": "pr_creating_timeout",
  "mcp_unavailable": "pr_creating_mcp"}` (default `pr_creating_failed`).

## TESTS (write/adjust first)

- Keep `TestFormatFailureComment` (seam `core._format_failure_comment` unchanged).
- Add: patch `generate_pr_summary` to raise `McpServersUnavailableError` → deliberate path labels
  `pr_creating_mcp` (assert via patched `_handle_create_pr_failure` receiving
  `category="pr_creating_mcp"`); raise `LLMTimeoutError` → `pr_creating_timeout`; raise generic
  `RuntimeError` → `pr_creating_failed`.
- Migrate the old net/`unexpected`-path seam test: a body escape / `SystemExit` is now labeled by
  the **guard** — assert `handle_workflow_failure` (or the resulting label transition +
  `## PR Creation Failed` comment) rather than the `_handle_create_pr_failure` seam.

## Verify

`run_pylint_check`, `run_pytest_check` (`-n auto` + unit-exclusion markers), `run_mypy_check`,
`run_lint_imports_check`.

## LLM Prompt

> Implement Step 4 of `pr_info/steps/summary.md` per `pr_info/steps/step_4.md`. Add
> `pr_creating_timeout` and `pr_creating_mcp` to `config/labels.json` (mirror the existing
> `*_timeout`/`*_mcp` blocks, `status-09f-*`). Give `helpers.handle_create_pr_failure` /
> `WorkflowFailure` an optional `category` (default `pr_creating_failed`). In `core.py` replace the
> hand-rolled `reached_terminal_state` + `finally` with `run_guarded` (general `pr_creating_failed`,
> from `pr_creating`, issue number resolved before the guard); keep the deliberate paths calling
> the `_handle_create_pr_failure` / `_format_failure_comment` seams; and at the
> `summary_generation` catch classify via `llm_failure_reason` into
> `pr_creating_timeout`/`pr_creating_mcp`/`pr_creating_failed`. Follow TDD — add the
> timeout/MCP/generic deliberate-path tests and migrate the old net-path seam test to assert guard
> behavior first, then implement. Run pylint, pytest (`-n auto` with unit-exclusion markers), mypy,
> and lint-imports. Produce exactly one commit.
