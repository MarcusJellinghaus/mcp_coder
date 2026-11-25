# Step 5 — ERROR for open issues with more than one `status-*` label

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_5.md`). Implement step 5 only,
> test-first: in `src/mcp_coder/cli/commands/coordinator/commands.py`, log one ERROR per open issue
> carrying more than one `status-*` label, from the `else` branch of `_collect_work`'s fetch `try`,
> before `check_pr_health`. Dispatch eligibility stays unchanged. Run all checks from the summary;
> produce exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/commands.py`
- `tests/cli/commands/coordinator/test_commands_pr_health.py` (extend)
- other coordinator test fixtures only if they now produce unexpected ERROR records

## WHAT

```python
def _log_multiple_status_labels(repo_name: str, issues: list[IssueData]) -> None:
    """Log one ERROR per open issue that carries more than one status-* label."""
```

## ALGORITHM

```
for issue in issues:
    if issue["state"] != "open": continue          # cached list still holds closed issues
    status_labels = [l for l in issue["labels"] if l.startswith("status-")]
    if len(status_labels) > 1:
        logger.error("%s #%d has multiple status labels: %s", repo_name, issue["number"], ", ".join(status_labels))
```

Call site in `_collect_work`, `else` branch:
```
else:
    _log_multiple_status_labels(repo_name, all_issues)   # before PR-health: a rate limit can't swallow it
    check_pr_health(repo_name, validated_config, all_issues)
```
Logged through the `commands` module logger. Repeats every run until fixed (accepted).

## DATA

None returned.

## HOW — tests first

Add to `test_commands_pr_health.py` (use `caplog`, filter records by logger name
`mcp_coder.cli.commands.coordinator.commands` and `logging.ERROR`):
- one ERROR per open issue with two `status-*` labels; message names repo, `#number` and both labels;
- no ERROR for a closed issue with two `status-*` labels;
- no ERROR for an issue with one `status-*` label plus non-status labels;
- no ERROR for a repo whose executor job is busy, nor for a repo whose cache failed (fallback);
- the ERROR is still logged when `check_pr_health` raises `GitHubRateLimitError` (exit 0);
- an open issue with `status-08:ready-pr` + `status-10:pr-created`: the multi-label ERROR is logged
  for it and `dispatch_workflow` is still called for it (exactly one bot_pickup label → eligible).

Then run the whole coordinator test directory: fixtures must carry at most one `status-*` label
(e.g. `test_commands_capacity_gate.py::_error_messages` counts ERROR records of the `commands` logger).
Fix any fixture that now has two.

## Verify

- `run_pytest_check` with `["-n", "auto", "tests/cli/commands/coordinator"]` passes, then the full fast suite.
