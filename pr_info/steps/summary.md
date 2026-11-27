# Summary — #1487: readable round log, no silently dropped triage tasks

## Goal

1. The round log's **Findings** holds the reviewer's *final* message, not narration glued
   onto it; **Decisions** is readable markdown, not a `Verdict(...)` repr.
2. The supervisor knows what the reviewer can and cannot do (file changes only; whether a
   PR exists), every task application reports an outcome per task, and a `tasks` round that
   changed nothing is reported back to the supervisor in the next round instead of vanishing.

## Architectural / design changes

All changes stay inside the review engine (`src/mcp_coder/workflows/review/`) and its
prompts. No provider code changes: `ResponseAssembler.result` and every other
`prompt_llm` caller keep the joined text.

| Concern | Before | After |
|---|---|---|
| Report text | `report_response["text"]` (all assistant blocks joined with `""`) | `reviewer.report_text(response)`: last `done` event's non-empty `result` from `raw_response["events"]`, else the joined text |
| Decisions field | `str(verdict)` (dataclass repr) | `verdict.format_verdict(verdict)`: decision line + tight `-` list of tasks; no escalate reason |
| Supervisor input | report + optional `## PR review feedback` built inline in `core.py` | `reviewer.supervisor_input(report, status, noop_note)` builds report + `## PR review feedback` + `## Review state` (PR-state line, no-op note) |
| Supervisor rules | no statement about what a task may be | rule: a task must be a change to files on the branch; otherwise escalate or don't issue it |
| Task prompt | "edit with the `mcp-workspace` edit tools"; reply discarded | names `edit_file` / `save_file` / `delete_this_file`; asks for leading `applied` / `not applied: <reason>` lines; reply parsed by `reviewer.parse_task_outcomes` |
| **Changes** field (normal path) | `applied` / `no-op` | token, then the outcome lines as plain lines |
| No-op round | logged only | `pending_noop_note` (built by `reviewer.noop_note`) goes into the next supervisor input and exempts that round from the severity floor (passed through the existing `pending_ci_note` argument as `pending_ci_note or pending_noop_note`) |

Design rules kept:

- `core.py` (690/750 lines) only changes call sites; helpers live in `reviewer.py` and
  `verdict.py`. `core.py` must stay under 750 lines.
- The round log stays formatter-stable (no headings, no raw report text in Decisions /
  Changes).
- "Changed nothing" is `round_applied(...) is False` (`steps.py`, unchanged).
- The PR-state line uses only `pr_found`, `pr_number`, `pr_feedback_undeterminable`,
  `ci_status` of `BranchStatusReport`.
- An empty final `result` falls back to the joined text, so the empty-report retry only
  fires when both are empty.

## Files

Modified:

- `src/mcp_coder/workflows/review/reviewer.py` — `report_text`, `_pr_state_line`,
  `supervisor_input`, `parse_task_outcomes`, `noop_note`, task-prompt text
- `src/mcp_coder/workflows/review/verdict.py` — `format_verdict`
- `src/mcp_coder/workflows/review/core.py` — call sites only
- `src/mcp_coder/workflows/review/severity.py` — docstring of `pending_ci_note` only
- `src/mcp_coder/prompts/prompts.md` — `Review Supervisor` rule; `delete_this_file` in both
  reviewer headers
- `tests/workflows/review/conftest.py` — `_status` gains `pr_found`, `pr_number`
- `tests/workflows/review/test_reviewer.py` — unit tests for the new reviewer helpers
- `tests/workflows/review/test_verdict.py` — `format_verdict` tests
- `tests/workflows/review/test_review_log.py` — `write_round_log` + `format_verdict` tests
- `tests/prompts/test_prompt_loader.py` — prompt-content tests

Created:

- `tests/workflows/review/test_core_round_outcomes.py` — new loop tests (report text,
  outcomes in **Changes**, no-op note, floor exemption). `test_core.py` is near the
  750-line limit, so loop tests go here.

## Steps

1. `report_text` — the review uses the final message.
2. `format_verdict` — readable **Decisions**.
3. Supervisor file-change rule + PR-state line via `supervisor_input`.
4. Task outcomes: task prompt, `delete_this_file`, outcome lines in **Changes**.
5. No-op note to the supervisor + severity-floor exemption.

## Out of scope

- A no-op in the last allowed round (no repeat in the rounds-cap handoff).
- #1155's report shape check and its other sections.
