# Step 6 — `ReviewConfig` + failure-label map + review-log writer

> References `pr_info/steps/summary.md` §2, §3, §6. Data + one small IO helper. No LLM.

## WHERE
- `src/mcp_coder/workflows/review/config.py` (new)
- `src/mcp_coder/workflows/review/review_log.py` (new)
- `tests/workflows/review/test_config.py` (new)
- `tests/workflows/review/test_review_log.py` (new)

## WHAT — `config.py`
```python
@dataclass(frozen=True)
class ReviewConfig:
    name: str                       # "review-implementation" | "review-plan"
    log_stem: str                   # "implementation" | "plan"  -> pr_info/{stem}_review_log_{n}.md
    session_dir_name: str           # "review_implementation_sessions" | "review_plan_sessions"
    reviewer_prompt_header: str     # "Review Implementation Reviewer" | "Review Plan Reviewer"
    supervisor_prompt_header: str   # "Review Supervisor" (shared)
    busy_label_id: str              # "code_reviewing" | "plan_reviewing"
    success_label_id: str           # "ready_pr" | "plan_ready"
    escalate_label_id: str          # "code_review" | "plan_review"
    inject_base_branch: bool        # True (impl) | False (plan)
    run_after_steps: bool           # True (impl: rebase+CI) | False (plan)
    failure_labels: dict[str, str]  # reason -> label internal_id

REVIEW_IMPLEMENTATION: ReviewConfig  # failure_labels keys: general/rounds/timeout/mcp/ci -> 17f*
REVIEW_PLAN: ReviewConfig            # failure_labels keys: general/rounds/timeout/mcp    -> 14f*
```

## WHAT — `review_log.py`
```python
def next_run_number(project_dir: Path, config: ReviewConfig) -> int
def write_round_log(project_dir: Path, config: ReviewConfig, run_number: int,
                    round_number: int, findings: str, decisions: str, changes: str,
                    escalate_reason: str | None = None) -> Path
```

## HOW
- `failure_labels` values are the `internal_id`s added in Step 2; `busy/success/escalate`
  ids are existing/new label ids resolved by `update_workflow_label` /
  `handle_workflow_failure`.
- Log path: `pr_info/{config.log_stem}_review_log_{n}.md`. `next_run_number` scans existing
  matching files (+1). `write_round_log` **appends** a round block (create with header on
  round 1) carrying findings / decisions / changes / `escalate_reason`.

## ALGORITHM (`write_round_log`)
```
path = project_dir / "pr_info" / f"{config.log_stem}_review_log_{run_number}.md"
if round_number == 1 and not path.exists(): write "# {name} review log {n}\n"
append "## Round {r} — {date}\n**Findings**:...\n**Decisions**:...\n**Changes**:...\n"
if escalate_reason: append "**Escalate reason**: {escalate_reason}\n"
return path
```

## DATA
- `ReviewConfig` frozen instances; `write_round_log` returns the `Path` written.

## TDD / checks
- `test_config.py`: assert both instances' ids match the Step 2 label ids; `REVIEW_PLAN`
  has `run_after_steps=False`/`inject_base_branch=False` and **no** `ci` failure key;
  `REVIEW_IMPLEMENTATION` has a `ci` key mapping to `code_review_ci`.
- `test_review_log.py` (tmp_path): `next_run_number` starts at 1 then increments with existing
  files; `write_round_log` creates the file with a header on round 1 and appends round blocks;
  `escalate_reason` is rendered when given.
- Run: `run_pytest_check(extra_args=["-n","auto","-k","review and (config or log)"])`, pylint, mypy.

## LLM prompt for this step
> Implement Step 6 of `pr_info/steps/summary.md`. Create
> `src/mcp_coder/workflows/review/config.py` with a frozen `ReviewConfig` dataclass and two
> instances `REVIEW_IMPLEMENTATION` / `REVIEW_PLAN` (fields and values per the Step 6 table;
> `failure_labels` maps reason→Step 2 label ids, plan has no `ci` reason). Create
> `review_log.py` with `next_run_number()` and `write_round_log()` writing
> `pr_info/{log_stem}_review_log_{n}.md` (header on round 1, append round blocks with
> findings/decisions/changes and optional escalate reason). Write `test_config.py` and
> `test_review_log.py` (tmp_path) first per the Step 6 TDD notes. Run the tests, pylint, mypy.
