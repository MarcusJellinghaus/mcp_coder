# Step 7 — Coordinator: stop on rate limit, partial-dispatch exit code

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_7.md`).
> Implement only Step 7. Tests first, then code.
> Run pylint, pytest (fast unit marker set, `-n auto`) and mypy; all must pass.
> Produce exactly one commit.

## WHERE
- `src/mcp_coder/cli/commands/coordinator/commands.py` (`execute_coordinator_run`, ~lines 255-335)
- `src/mcp_coder/cli/commands/coordinator/core.py` (`dispatch_workflow`, ~lines 363-482)
- tests: `tests/cli/commands/coordinator/test_commands.py`, `test_core_dispatch.py`, `test_core_eligibility.py`

## WHAT
- `dispatch_workflow(...) -> bool`. Returns `True` in every existing path
  (including the existing early `return`s for invalid URL / no branch). Wrap
  only Step 7 (`remove_labels` + `add_labels`):
  ```python
  try:
      issue_manager.remove_labels(issue["number"], current_label)
      issue_manager.add_labels(issue["number"], workflow_config["next_label"])
  except Exception as exc:  # pylint: disable=broad-exception-caught
      if as_rate_limit(exc) is None:
          raise
      logger.error(
          "Issue #%d: Jenkins job started, label not updated "
          "(old label '%s', intended label '%s'): %s",
          issue["number"], current_label, workflow_config["next_label"], exc,
      )
      return False
  ```
  Update docstring (`Returns:` True unless the job started but the label swap hit a rate limit).
- `commands.py`:
  - `except` at ~262 (cache fallback): first line `raise_if_rate_limited(e)`.
  - dispatch: `if not dispatch_workflow(...): return 1` (skip the cache update).
  - `except` at ~313 and ~318: first line `raise_if_rate_limited(...)`.
  - Add before `except ValueError` at the end:
    ```python
    except GitHubRateLimitError as e:
        log_rate_limit_stop(e)
        return 0
    ```
  - The outer `except ValueError` and `except Exception` handlers also detect
    rate limits (same pattern as Step 8's `_rate_limit_or_raise`), so a raw
    rate-limit `GithubException` from code outside the re-raising `except`
    blocks (the `get_eligible_issues` fallback at ~266, repo setup before ~255)
    and a rate limit wrapped in a `ValueError` also exit 0:
    ```python
    except ValueError as e:
        if (rl := as_rate_limit(e)) is not None:
            log_rate_limit_stop(rl)
            return 0
        logger.error("%s", e)
        return 1
    except Exception as e:
        if (rl := as_rate_limit(e)) is not None:
            log_rate_limit_stop(rl)
            return 0
        <unchanged: log + raise>
    ```
- `core.py:347` (`get_cached_eligible_issues`) stays unchanged — it catches
  `(ValueError, KeyError, TypeError)`, which `GitHubRateLimitError` is not.
- Branch lookup in `dispatch_workflow` (~line 416) stays live; a rate limit there
  propagates (before `start_job`) and follows the exit-0 rule.

## HOW
Imports: `as_rate_limit`, `raise_if_rate_limited`, `log_rate_limit_stop` from
`....workflow_utils.rate_limit`; `GitHubRateLimitError` from `....mcp_workspace_github`.

Tests (TDD):
- `get_cached_eligible_issues` with `get_all_cached_issues` raising
  `GitHubRateLimitError` → propagates; `get_eligible_issues` not called (acceptance, `core.py:347`).
- `execute_coordinator_run`: `get_cached_eligible_issues` raises `GitHubRateLimitError`
  → returns 0, `get_eligible_issues` not called, second repo not processed,
  one "reset" log line (acceptance, `commands.py:262`).
- branch lookup raises a rate-limit `GithubException` → `start_job` not called, exit 0.
- partial dispatch: `start_job` succeeds, `add_labels` raises a rate-limit
  `GithubException` → `dispatch_workflow` returns `False`, one ERROR containing the
  issue number, old and intended label; `execute_coordinator_run` returns 1 and
  does not call `update_issue_labels_in_cache`.
- outer handlers, one test each → returns 0, one "reset" log line:
  - `get_cached_eligible_issues` raises a non-rate-limit error and the
    `get_eligible_issues` fallback raises a raw rate-limit `GithubException`;
  - repo setup before the cache call (e.g. `IssueManager` construction) raises a
    raw rate-limit `GithubException`;
  - a `ValueError` raised `from` a rate-limit `GithubException` reaches `except ValueError`.
- non-rate-limit `ValueError` still → 1; non-rate-limit `RuntimeError` still re-raised.
- Existing dispatch tests: assert `True` is returned on success.

## DATA
`dispatch_workflow -> bool`.
