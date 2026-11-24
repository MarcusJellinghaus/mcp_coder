# Step 4 — Global reverse-pipeline order (collect, then sort)

## LLM prompt

> Read `pr_info/steps/summary.md` (sections "Coordinator run flow" and "Priority order") and this
> file, then implement Step 4 only. No capacity gate and no delay yet (Step 6). Write the tests
> first, then the implementation. Run pylint, mypy and the fast unit tests (see
> `.claude/CLAUDE.md`), run the formatter, and make exactly one commit:
> `feat(coordinator): dispatch eligible issues of all repos in reverse pipeline order`.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/command_templates.py` — `PRIORITY_ORDER` + comment.
- `src/mcp_coder/cli/commands/coordinator/core.py` — new `stage_index`; remove the sorts (and
  their inner `get_priority` helpers) from `_filter_eligible_issues` and `get_eligible_issues`;
  update docstrings of both and of `get_cached_eligible_issues` ("sorted by priority" → input
  order; the coordinator sorts globally).
- `src/mcp_coder/cli/commands/coordinator/commands.py` — restructure `execute_coordinator_run`.
- Tests: `tests/cli/commands/coordinator/test_core_eligibility.py`,
  `tests/cli/commands/coordinator/test_commands_dispatch_order.py` (**new**).

## WHAT

```python
# command_templates.py
# Dispatch order (highest first): reverse pipeline order, closest to done first.
# Each review step sits just below the stage it unblocks.
PRIORITY_ORDER: list[str] = [
    "status-81:failing-ci",  # fix-ci
    "status-71:merge-conflict",  # fix-conflict
    "status-08:ready-pr",  # create-pr
    "status-17:code-review-bot",  # review-implementation
    "status-05:plan-ready",  # implement
    "status-14:plan-review-bot",  # review-plan
    "status-02:awaiting-planning",  # create-plan (furthest from done)
]

# core.py
def stage_index(issue: IssueData) -> int:
    """Position of the issue's stage in PRIORITY_ORDER; lower is dispatched first.

    Returns:
        Index of the first label found in PRIORITY_ORDER, len(PRIORITY_ORDER) if none.
    """

# commands.py
class _Repo(NamedTuple):
    """Per-repository values the dispatch loop needs."""

    index: int  # position in config order, the sort tie-break
    name: str
    full_name: str
    config: dict[str, str]  # the existing validated_config
    issue_manager: IssueManager
    branch_manager: IssueBranchManager


def _dispatch_sort_key(item: tuple[IssueData, _Repo]) -> tuple[int, int]:
    """Stage first, then config repo order; extend the tuple for further criteria."""
    return (stage_index(item[0]), item[1].index)
```

## HOW

- `execute_coordinator_run` keeps steps 1–3 (config creation, repo list, Jenkins client) and the
  outer `except` blocks unchanged. Step 4 is split into a collection loop and a dispatch loop.
- Collection loop: the existing per-repo code (load/validate config, header log, managers,
  `repo_full_name`, cached fetch with direct-fetch fallback, "Found N eligible issues",
  "No eligible issues for X") moves unchanged; instead of dispatching it appends
  `(issue, repo)` for each eligible issue to `work`.
- Dispatch loop: the existing per-issue body unchanged (workflow label check → trust gate →
  dispatch → cache update → per-issue `except` with fail-fast), using `repo.*` instead of the
  per-repo locals.
- Untrusted summary: `skipped: dict[str, list[tuple[int, BodyTrustResult]]]` keyed by repo
  name (insertion order = first skip). One `try/finally` around the dispatch loop logs the
  existing line `"Skipped %d issue(s) in %s with untrusted body: %s"` once per repo.
- Drop `"Finished processing eligible issues in {repo_name}"` (no longer per-repo); log
  `"Finished dispatching eligible issues"` once after the loop.
- Move helpers out of `execute_coordinator_run` only if pylint reports too-many-branches /
  too-many-statements (e.g. `_collect_repo(index, repo_name, force_refresh) -> tuple[_Repo, list[IssueData]]`).

## ALGORITHM

```
work = []
for index, repo_name in enumerate(repo_names):
    repo, issues = <existing per-repo config + fetch>   # repo = _Repo(index, ...)
    work.extend((issue, repo) for issue in issues)
work.sort(key=_dispatch_sort_key)                        # stable: keeps fetch order on ties
try: for issue, repo in work: <existing per-issue body>
finally: log one untrusted summary per repo in skipped
```

## DATA

- `work: list[tuple[IssueData, _Repo]]`, sorted.
- `skipped: dict[str, list[tuple[int, BodyTrustResult]]]`.

## Tests (write first)

`test_core_eligibility.py`:
- `test_get_eligible_issues_filters_by_bot_pickup_labels`: the result keeps input order
  (`[1, 4]`), not priority order.
- Same for `_filter_eligible_issues` / `get_cached_eligible_issues` if a test asserts sorting.
- `stage_index`: each of the 7 labels maps to its position in the order 81, 71, 08, 17, 05, 14, 02;
  an issue without such a label → `len(PRIORITY_ORDER)`.

`test_commands_dispatch_order.py` (new; a `mocks` fixture like `test_commands_trust_gate.py`,
two repos via patched `load_config` and `load_repo_config.side_effect` keyed by repo name,
`get_cached_eligible_issues.side_effect` per repo, `dispatch_workflow` returning
`DispatchResult.STARTED`):
1. Global order across repos: repo_a has `[02 #1, 08 #2]`, repo_b has `[81 #3, 05 #4]` →
   dispatched `[3, 2, 4, 1]`.
2. Tie-break by config repo order: both repos have a `05` issue → repo_a's first.
3. Stable within a stage and repo: repo_a `[05 #7, 05 #5]` → `[7, 5]`.
4. All issues of all repos are fetched before the first dispatch (record call order with a
   shared `MagicMock` parent or a list appended by side effects).
5. Untrusted summary per repo, logged after all dispatches: repo_a and repo_b each with one
   untrusted issue → two summary lines, each after the last "dispatch" call.
6. Fail-fast still ends the run at the first dispatch error (exit 1), and the summary of an
   earlier-skipped issue is still logged.
