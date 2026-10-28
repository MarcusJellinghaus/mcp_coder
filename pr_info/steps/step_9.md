# Step 9 — vscodeclaude inner `except` blocks re-raise rate limits

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_9.md`).
> Implement only Step 9. Tests first, then code.
> Run pylint, pytest (fast unit marker set, `-n auto`) and mypy; all must pass.
> Produce exactly one commit.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/checks.py`
- `src/mcp_coder/workflows/vscodeclaude/issues.py`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py`
- `src/mcp_coder/workflows/vscodeclaude/session_restart.py`
- `src/mcp_coder/workflows/vscodeclaude/assessment.py`
- tests: `tests/workflows/vscodeclaude/test_checks*.py`, `test_issues_branch_check.py`,
  `test_session_launch_process_issues.py`, `test_session_restart_*.py`,
  `test_assessment_issue_facts.py`, `test_status_note.py`

## WHAT
Add `raise_if_rate_limited(<exc>)` as the **first line** of each of these
`except` blocks (nothing else in the block changes):

| File | Block |
|---|---|
| `checks.py` | both excepts in `_resolve_pr_target`; `_check_merge_conflict`; `_check_ci`; `_check_review_comments`; the setup except in `check_pr_health` (~330) |
| `issues.py` | `except ValueError` around `get_github_username()` (~363); repo-level `except Exception` (~404) |
| `session_launch.py` | per-issue `except Exception` in `process_eligible_issues` (~465) |
| `session_restart.py` | per-session `except Exception` (~408) |
| `assessment.py` | `except ValueError` around `get_github_username()` (~277); `_fetch_issue_individually` (~490) |

`except` blocks that need binding a name (`except Exception:` without `as`)
get `as exc`.

Unchanged on purpose:
- `workspace.py` `_fetch_marked_comment` (~665) keeps swallowing (WARNING).
- `_escalate`: a rate limit from `update_workflow_label` (Step 6) now reaches
  the `_check_*` excepts and is re-raised there; other errors stay non-fatal.

## HOW
- Import `raise_if_rate_limited` from `...workflow_utils.rate_limit`.
- Update the "Never raises" docstrings in `checks.py` to
  "Never raises, except `GitHubRateLimitError`".
- Tests (TDD), each with a rate-limit `GithubException` (or `GitHubRateLimitError`) side effect:
  - `check_pr_health`: limit in the first issue's PR lookup / merge check / CI /
    review check → `GitHubRateLimitError` propagates, second issue not checked.
  - `check_pr_health`: `get_github_username` raises `ValueError` from a rate limit → propagates.
  - `_escalate` → `update_workflow_label` raises `GitHubRateLimitError` → propagates.
  - `build_eligible_issues_with_branch_check`: limit in the branch lookup of
    repo 1 → propagates, repo 2 not processed; `GET /user` limit → propagates.
  - `process_eligible_issues`: limit in the branch lookup of issue 1 → propagates,
    issue 2 not started.
  - `restart_closed_sessions`: limit in `_prepare_restart_branch` → propagates,
    `launch_vscode` not called.
  - `_fetch_issue_individually`: limit → propagates; other errors → `None` (unchanged).
  - `build_assessments` with cache and `GET /user` limit → propagates.
  - `_fetch_marked_comment`: rate-limit `GithubException` → returns `None`, WARNING logged
    (acceptance; behaviour already exists, test pins it).
  - Non-rate-limit errors keep today's behaviour in every block (existing tests).

## DATA
No signature changes.
