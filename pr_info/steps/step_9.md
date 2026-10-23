# Step 9 — Phase B module: `create_pr/post_creation.py`

Standalone function; wired into the workflow in step 10.

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_9.md` exactly.
> Write `tests/workflows/create_pr/test_post_creation.py` first, then the module.
> Run pylint, pytest (fast unit set, `-n auto`), mypy and lint-imports; all must pass. Format the code and make exactly one commit.

## WHERE
- New `src/mcp_coder/workflows/create_pr/post_creation.py`
- New `tests/workflows/create_pr/test_post_creation.py`

## WHAT
```python
def run_post_creation(project_dir: Path, branch: str) -> str:
    """Check mergeability, then wait for CI. No fixing.

    Returns:
        Label ID for the final transition from pr_creating:
        "pr_merge_conflict", "failing_ci" or "pr_created".
    """
```

## ALGORITHM
```
state = _poll_mergeable_state(project_dir, branch)
if state == "dirty":
    outcome = _attempt_rebase_and_push(project_dir); log outcome.reason
    state = _poll_mergeable_state(project_dir, branch)
    if state == "dirty": log; return "pr_merge_conflict"
try: ci_manager = CIResultsManager(project_dir)
except Exception as e: logger.info("CI_API_ERROR: ... (%s)", e); return "pr_created"
ci_status, ci_ok = _poll_for_ci_completion(ci_manager, branch, expected_sha=get_latest_commit_sha(project_dir))
return "failing_ci" if ci_status is not None and not ci_ok else "pr_created"
```

## HOW
- Imports: `_poll_mergeable_state`, `_attempt_rebase_and_push` from `mcp_coder.workflow_steps.rebase`;
  `_poll_for_ci_completion` from `mcp_coder.workflow_steps.ci`; `CIResultsManager` from `mcp_coder.mcp_workspace_github`;
  `get_latest_commit_sha` from `mcp_coder.mcp_workspace_git`.
- `expected_sha` is read **after** any rebase, so it is the HEAD that was actually pushed.
- `unknown`, `None` and non-dirty states (`behind`, `clean`, `blocked`, `unstable`, ...) all go to the CI wait — no extra branches.
- `get_latest_commit_sha` returning `None` is passed through (accept-any-run behaviour); no special case.
- Module docstring: one paragraph explaining the conflict-before-CI order (same as PR-health) and "wait only, no fixing".

## Tests (write first)
Patch everything at `mcp_coder.workflows.create_pr.post_creation.*`.
| Case | Expected |
|---|---|
| `clean`, CI `(status, True)` | `pr_created`; no rebase |
| `behind`, CI green | `pr_created`; no rebase |
| `unknown` | `pr_created` path via CI |
| `None` | CI wait runs; `pr_created` |
| `clean`, CI `(status, False)` | `failing_ci` |
| `clean`, CI `(None, True)` (timeout / no CI / API error) | `pr_created` |
| `dirty` → rebase → `clean`, CI green | `pr_created`; rebase called once |
| `dirty` → rebase → `dirty` | `pr_merge_conflict`; CI not polled |
| `CIResultsManager` raises | `pr_created` |
| `expected_sha` | equals `get_latest_commit_sha` return value, read after the rebase (assert call order) |

## DATA
`str` label ID.
