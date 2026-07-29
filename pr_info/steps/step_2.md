# Step 2 — CLI: `--fail-on-reviews` flag + pure exit-code contract

Depends on Step 1 (shim). One commit.

## WHERE

- `src/mcp_coder/cli/parsers.py` — add the flag (branch-status subparser).
- `src/mcp_coder/cli/commands/check_branch_status.py` — new `_exit_code` helper;
  drop `replace()` enrichment; pass `fail_on_reviews` to the formatters; use the
  helper for the final exit code.
- `tests/cli/commands/` — exit-contract table + parser test (extend an existing
  `test_check_branch_status*.py` or add a focused module).

## WHAT

New parser argument (in `add_check_parsers`, next to `--wait-for-pr` ~line 433):

```python
branch_status_parser.add_argument(
    "--fail-on-reviews",
    action="store_true",
    help="Exit non-zero unless PR reviews are proven clean; also renders the "
         "Review Gate header (default: off = informational)",
)
```

New pure helper in `check_branch_status.py`:

```python
def _exit_code(report: BranchStatusReport, fail_on_reviews: bool) -> int:
    """Map a report to a process exit code. Evaluated 2 -> 1 -> 0."""
```

## HOW (integration points)

In `execute_check_branch_status`:
- **Drop** the `from dataclasses import replace` import and the
  `if pr_found is not None: report = replace(report, pr_number=…, pr_url=…,
  pr_found=…)` block — upstream `collect_branch_status` fills the PR fields.
- Keep the `--wait-for-pr` polling loop as a **pure gate**: keep a single local
  `pr_found` bool only to `return 1` on timeout; delete the `pr_number`/`pr_url`
  locals (no longer threaded into the report).
- Formatter call becomes (pass the flag unconditionally):
  ```python
  output = (
      report.format_for_llm(fail_on_reviews=args.fail_on_reviews)
      if args.llm_truncate
      else report.format_for_human(fail_on_reviews=args.fail_on_reviews)
  )
  ```
- Replace the scattered exit logic. Keep the pre-`--fix` short-circuit for
  undeterminable CI (so no pointless fix attempt), routing it through the helper;
  keep the `--fix` success path returning 0/1; end with `return _exit_code(...)`:
  ```python
  if report.ci_status in (CIStatus.UNAVAILABLE, CIStatus.UNKNOWN):
      return _exit_code(report, args.fail_on_reviews)   # 2, and skip --fix
  if args.fix > 0:
      ... existing fix path (returns 0 or 1) ...
  return _exit_code(report, args.fail_on_reviews)
  ```

## ALGORITHM (`_exit_code`)

```
if report.ci_status in (UNAVAILABLE, UNKNOWN):              return 2
if fail_on_reviews and report.pr_feedback_undeterminable:   return 2
if report.ci_status == FAILED:                              return 1
if fail_on_reviews and report.pr_feedback_blocks_merge:     return 1
return 0
```

## DATA

- Reads `report.ci_status` (`CIStatus`), `report.pr_feedback_undeterminable`
  (bool), `report.pr_feedback_blocks_merge` (bool).
- Returns `int` exit code (0 / 1 / 2).
- `args.fail_on_reviews` is a `bool` (argparse `store_true`, default `False`).

## TESTS (TDD — write first)

`_exit_code` table (pure, no mocking — build small `BranchStatusReport`s):
- UNAVAILABLE → 2; UNKNOWN → 2 (regardless of flag).
- FAILED, flag off → 1; FAILED, flag on → 1.
- `pr_feedback_undeterminable=True`: flag off → 0, flag on → 2.
- `pr_feedback_blocks_merge=True`: flag off → 0, flag on → 1.
- **Precedence:** FAILED + `pr_feedback_undeterminable` + flag on → 2 (undeterminable
  wins over blocking).
- PASSED / NOT_CONFIGURED / PENDING, clean → 0.

Parser test:
- Parsing `check branch-status --fail-on-reviews` sets `args.fail_on_reviews is True`;
  default is `False`.

Command wiring (extend existing tests, mock `collect_branch_status`):
- assert the formatter is called with `fail_on_reviews=...`;
- assert the dropped `replace()` enrichment is gone (report PR fields come
  straight from the mocked `collect_branch_status`).

## CHECKS

pylint / pytest (parallel, unit-only exclusions) / mypy — all pass.

## LLM PROMPT

> Implement **Step 2** of `pr_info/steps/summary.md` (issue #1068): add the
> `--fail-on-reviews` CLI flag and the pure exit-code contract, per
> `pr_info/steps/step_2.md`.
>
> 1. Add `--fail-on-reviews` (`store_true`, default off) to the branch-status
>    subparser in `cli/parsers.py`.
> 2. In `cli/commands/check_branch_status.py`: add the pure helper
>    `_exit_code(report, fail_on_reviews) -> int` implementing the 2→1→0
>    precedence exactly as in the step's ALGORITHM. Drop the `dataclasses.replace`
>    import and the `replace(report, pr_number=…)` enrichment block. Keep
>    `--wait-for-pr` as a pure gate (one local `pr_found` bool, `return 1` on
>    timeout). Pass `fail_on_reviews=args.fail_on_reviews` to
>    `format_for_human`/`format_for_llm` unconditionally. Route the pre-`--fix`
>    undeterminable-CI short-circuit and the final return through `_exit_code`.
> 3. Write the `_exit_code` contract-table tests (including the FAILED +
>    undeterminable precedence case), the parser test, and the wiring assertions
>    in the step. TDD: tests first.
>
> Use MCP tools only. Run pylint, pytest (parallel, unit-only exclusions), mypy;
> all must pass. Produce exactly one commit.
