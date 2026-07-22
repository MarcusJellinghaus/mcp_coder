# Step 9 — CLI verbs (`review-plan` / `review-implementation`)

> References `pr_info/steps/summary.md` (CLI). Thin entry points over `run_review_workflow`;
> mirrors `implement` / `create-plan` arg wiring.

## WHERE
- `src/mcp_coder/cli/commands/review.py` (new)
- `src/mcp_coder/cli/parsers.py` (modify — add two parser functions)
- `src/mcp_coder/cli/main.py` (modify — import + route)
- `src/mcp_coder/cli/command_catalog.py` (modify — `COMMAND_DESCRIPTIONS`)
- `tests/cli/commands/test_review.py` (new)

## WHAT — `review.py`
```python
def execute_review_plan(args: argparse.Namespace) -> int:
    return _execute_review(args, REVIEW_PLAN)

def execute_review_implementation(args: argparse.Namespace) -> int:
    return _execute_review(args, REVIEW_IMPLEMENTATION)

def _execute_review(args, config: ReviewConfig) -> int: ...
```

## WHAT — `parsers.py`
```python
def add_review_plan_parser(subparsers) -> None
def add_review_implementation_parser(subparsers) -> None
```

## HOW
- `_execute_review` mirrors `execute_implement`: `resolve_project_dir`,
  `log_command_startup`, `enable_crash_logging`, `resolve_execution_dir`,
  `resolve_llm_method`+`parse_llm_method_from_args`, `resolve_mcp_config_path`,
  `resolve_claude_settings_path`, `resolve_issue_interaction_flags`, then
  `run_review_workflow(config, project_dir, provider, mcp_config, settings_file,
  execution_dir, update_issue_labels, post_issue_comments)`.
- Both parsers reuse the shared arg helpers (`add_project_dir_arg`, `add_llm_method_arg`,
  `add_mcp_config_arg`, `add_settings_arg`, `add_execution_dir_arg`) plus the
  `--update-issue-labels` / `--post-issue-comments` `BooleanOptionalAction` flags — identical
  to `add_implement_parser`. **No `issue_number` positional** (derived from the branch).
- `main.py`: register both via `create_parser()` and route
  `args.command in {"review-plan","review-implementation"}` to the two `execute_*` functions.
- `command_catalog.py`: add short descriptions for both verbs.

## ALGORITHM
- None (wiring).

## DATA
- Exit code `int` propagated from `run_review_workflow`.

## TDD / checks
- `test_review.py`: patch `run_review_workflow`, call `execute_review_plan` /
  `execute_review_implementation` with a fake `args`, assert it is invoked with the right
  `ReviewConfig` and resolved params and the return code propagates.
- Parser tests (extend `tests/cli/test_parsers.py` or add here): `mcp-coder review-plan` /
  `review-implementation` parse; `--no-update-issue-labels` works; help-anti-drift passes.
- Run: `run_pytest_check(extra_args=["-n","auto","-k","review or parser or help"])`, pylint, mypy.

## LLM prompt for this step
> Implement Step 9 of `pr_info/steps/summary.md`: create
> `src/mcp_coder/cli/commands/review.py` with `execute_review_plan` /
> `execute_review_implementation` delegating to a shared `_execute_review(args, config)` that
> resolves args exactly like `execute_implement` and calls `run_review_workflow` with
> `REVIEW_PLAN` / `REVIEW_IMPLEMENTATION`. Add `add_review_plan_parser` /
> `add_review_implementation_parser` to `parsers.py` (same options as `add_implement_parser`, no
> issue positional), register+route them in `main.py`, and add `COMMAND_DESCRIPTIONS` entries in
> `command_catalog.py`. Write `tests/cli/commands/test_review.py` first (patch
> `run_review_workflow`, assert correct config/params/return), and ensure parser + help-anti-drift
> tests pass. Run the tests, pylint, mypy.
