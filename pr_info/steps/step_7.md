# Step 7 — Review engine core loop (`core.py`)

> References `pr_info/steps/summary.md` §1, §6. Implements the **shared** loop; this step fully
> realizes **`review-plan`** (`run_after_steps=False`). Step 8 adds the
> `review-implementation` after-steps. Deterministic tests mock the LLM.

## WHERE
- `src/mcp_coder/workflows/review/core.py` (new)
- `tests/workflows/review/test_core.py` (new — mocked LLM)

## WHAT
```python
REVIEW_MAX_ROUNDS = 5
VERDICT_REPAIR_RETRIES = 2

def run_review_workflow(
    config: ReviewConfig,
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    execution_dir: Path | None = None,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
) -> int: ...

# internal helpers
def _resolve_context(config, project_dir) -> tuple[int | None, str | None]   # issue_no, base_branch
def _run_reviewer(config, ..., issue_number, base_branch, session_id, tasks) -> LLMResponseDict
def _get_verdict(config, ..., supervisor_sid) -> tuple[Verdict | None, str | None]
def _after_steps(config, project_dir, provider, ...) -> str | None   # Step 7 stub: returns None
def _fail(config, project_dir, reason, *, update_issue_labels, post_issue_comments) -> int
```

## HOW
- **Sessions:** reviewer always `prompt_llm(session_id=None)` (fresh per round); supervisor id
  captured on round 1 and **re-captured from each response** (discipline proven in Step 1),
  threaded via `session_id=`. `mcp_config` passed to **both** calls.
- **Prompts:** `get_prompt_with_substitutions(PROMPTS_FILE_PATH, config.reviewer_prompt_header,
  {"issue_number":…, "base_branch":…})`; supervisor via `config.supervisor_prompt_header`.
- **After-steps (`tasks` round):** resume reviewer session with the task list → reviewer edits
  via MCP → `run_formatters` + `commit_changes` + `push_changes` (from
  `mcp_coder.workflow_steps.commit`). `_after_steps` is a no-op stub here (Step 8 fills it).
- **Verdict repair:** `_get_verdict` calls the supervisor, `parse_verdict`; on `None`, resume
  the supervisor up to `VERDICT_REPAIR_RETRIES` asking for valid fenced JSON; still `None` →
  reason `"general"`.
- **Backstop (layer C):** capture `sha_before = get_latest_commit_sha()` at round start;
  after a `tasks` round, if sha unchanged **and** working dir clean, log a silent-no-op via
  `write_round_log` (round still counts toward the cap; loop continues — layer A re-surfaces it).
- **Routing / labels:** `dismiss` → `update_workflow_label(from=busy, to=success)` → `0`;
  `escalate` → `write_round_log(escalate_reason=…)` + `update_workflow_label(from=busy,
  to=escalate)` → `0` (not a failure, no comment); `error` → `_fail(...)` → `1`.
- **`_fail`** delegates to shared `handle_workflow_failure(from_label_id=config.busy_label_id,
  category=config.failure_labels[reason], comment_body=…)` (posts a comment on the error path,
  like `implement`).
- **Exceptions:** wrap LLM calls; `LLMTimeoutError` → reason `"timeout"`,
  `McpServersUnavailableError` → `"mcp"` (reuse `llm_failure_reason` if convenient); other →
  `"general"`.

## ALGORITHM (`run_review_workflow`)
```
issue_no, base = _resolve_context(config, project_dir)      # base None when not inject_base_branch
sup_sid = None; tasks = None
for r in 1..REVIEW_MAX_ROUNDS:
    sha0 = get_latest_commit_sha(project_dir)
    report = _run_reviewer(config, ..., issue_no, base, session_id=None, tasks=tasks)  # fresh
    verdict, sup_sid = _get_verdict(config, ..., sup_sid, report)   # None -> return _fail("general")
    if verdict.decision == "dismiss":
        reason = _after_steps(config, ...)          # Step 8: rebase+CI gate; Step 7: None
        if reason: return _fail(config, reason, ...)
        update_workflow_label(from=busy, to=success); return 0
    if verdict.decision == "escalate":
        write_round_log(..., escalate_reason=verdict.escalate_reason)
        update_workflow_label(from=busy, to=escalate); return 0
    # decision == "tasks"
    _run_reviewer(config, ..., session_id=<reviewer_sid>, tasks=verdict.tasks); commit_changes; push_changes
    reason = _after_steps(config, ...)              # Step 8 hook; Step 7 stub None
    if reason: return _fail(config, reason, ...)
    changed = get_latest_commit_sha(project_dir) != sha0 or not is_working_directory_clean(project_dir)
    write_round_log(..., findings=report, decisions=str(verdict), changes="no-op" if not changed else "applied")
    tasks = None
return _fail(config, "rounds", ...)                 # cap exhausted
```

## DATA
- Returns `int` exit code: `0` (success **or** escalate/needs-human), `1` (error).
- `Verdict` from Step 5; `ReviewConfig` from Step 6; `LLMResponseDict` from `prompt_llm`.

## TDD / checks (mock `prompt_llm`; use `REVIEW_PLAN`)
- `dismiss` on round 1 → returns 0, success label set, no failure comment.
- `escalate` → returns 0, escalate label set, log has escalate reason, no comment.
- `tasks` then `dismiss` → 2 rounds, reviewer resumed with tasks, success.
- verdict unparseable after 2 repairs → returns 1, `general` failure label + comment.
- `tasks` every round → rounds cap → returns 1, `rounds` label.
- silent no-op (`tasks` but sha unchanged + clean) → logged, loop continues, still capped.
- `LLMTimeoutError` / `McpServersUnavailableError` raised by the mock → `timeout` / `mcp` labels.
- Run: `run_pytest_check(extra_args=["-n","auto","-k","review and core"])`, pylint, mypy.

## LLM prompt for this step
> Implement Step 7 of `pr_info/steps/summary.md`: create
> `src/mcp_coder/workflows/review/core.py` with `run_review_workflow(config, ...)` and the
> helpers listed, implementing the shared loop exactly as the Step 7 pseudocode (fresh reviewer
> session per round + persistent supervisor with re-captured session id; `mcp_config` to both;
> verdict parse with 2 repair retries; 3-way routing via `update_workflow_label` for
> dismiss/escalate and `handle_workflow_failure` for errors; whole-round commit-sha backstop;
> rounds cap 5; commit/push reviewer edits via `workflow_steps.commit`). `_after_steps` is a
> no-op stub returning `None` in this step. Map `LLMTimeoutError`→`timeout`,
> `McpServersUnavailableError`→`mcp`, else `general`; `rounds` on cap. Write
> `tests/workflows/review/test_core.py` first with a mocked `prompt_llm` covering all cases in
> the Step 7 TDD list, driving `REVIEW_PLAN`. Run the core tests, pylint, mypy.
