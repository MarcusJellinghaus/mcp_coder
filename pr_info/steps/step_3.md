# Step 3 — Refactor `update_workflow_label` to delegate to `transition_issue_label`

## LLM prompt

> Read `pr_info/steps/summary.md` for context, then implement **this step only** (`pr_info/steps/step_3.md`) in a single commit. Step 2's primitive must already exist. Use the existing `test_issue_manager_label_update.py` tests as regression coverage — they should continue to pass without modification (one test reflecting the intentional idempotency improvement is already consistent with the new behavior). Run all quality checks after.

## WHERE

- `src/mcp_coder/utils/github_operations/issues/manager.py` — refactor body of `IssueManager.update_workflow_label`.

## WHAT — function signature (UNCHANGED)

```python
def update_workflow_label(
    self,
    from_label_id: str,
    to_label_id: str,
    branch_name: Optional[str] = None,
    validated_issue_number: Optional[int] = None,
) -> bool: ...
```

## HOW — integration

- Keep the outer `try/except Exception` (broad-catch pattern matches existing code).
- Keep `@log_function_call` decorator.
- Keep all branch/issue resolution (steps 1–3) and label-config lookup (steps 4–5) exactly as-is.
- Delegate label mutation + idempotency + current-labels fetch to `self.transition_issue_label(...)`.
- Caller-side `labels_to_clear` computation: `label_lookups["all_names"] - {to_label_name}` (decision #6 — subtract `to_label_name` so the primitive's idempotency check can fire).

## ALGORITHM — replacement for old steps 6–9

After the existing step-5 `from_label_name` / `to_label_name` lookups and validations, replace steps 6 through 9 with:

```
labels_to_clear = label_lookups["all_names"] - {to_label_name}
success = self.transition_issue_label(issue_number, to_label_name, labels_to_clear)
if success:
    logger.info(
        f"Successfully updated issue #{issue_number} label: "
        f"{from_label_name} → {to_label_name}"
    )
return success
```

Delete from the old body:

- The step-6 `get_issue` call and the `issue_data["number"] == 0` check → primitive owns the fetch and the empty-`IssueData` guard.
- The step-7 idempotency block (`if to_label_name in current_labels: ...`) → primitive's stricter idempotency check replaces it.
- The step-7 INFO log `'Source label <from_label_id> not present in issue labels'` is removed as a side-effect of delegating to the config-free primitive (which has no concept of `from_label` vs `to_label`). One test asserts this log — see the regression instruction below. Accepted per review Round 1 decision.
- The step-8 `new_labels = (current_labels - label_lookups["all_names"]) | {to_label_name}` computation → moved into primitive via the `labels_to_clear` argument.
- The step-9 `result = self.set_labels(...)` call and `result["number"] == 0` check → primitive returns a `bool` directly.

Keep the final outer `except Exception:` block logging and returning `False`.

## DATA

- No signature change, no return-type change.
- Behavior change (intentional, narrow): stray workflow labels not equal to `to_label_name` are now stripped even when target label is already present; this matches `test_update_workflow_label_removes_different_workflow_label`.

## Tests — regression only

No new tests in this step. The existing suite in `tests/utils/github_operations/test_issue_manager_label_update.py` acts as full regression coverage.

**Required test-assertion update**: `tests/utils/github_operations/test_issue_manager_label_update.py::test_update_workflow_label_removes_different_workflow_label` asserts the removed log string on line 635 (`assert "Source label 'status-06:implementing' not present" in caplog.text`). Drop this assertion. The behavioural assertions on the same test (lines 625, 629, 632 — `set_labels` call-args) already cover the contract. No other test uses this log string; the `'already has ... without ...'` phrase mentioned in Round 1 does not appear in the test suite (confirmed).

Tests expected to pass unchanged:

- `test_update_workflow_label_success_happy_path` → still passes (new path → `transition_issue_label` → `set_labels`).
- `test_update_workflow_label_already_correct_state` → still passes (current has `code_review`, `implementing` absent from both current and `labels_to_clear` stripped set → idempotent short-circuit fires).
- `test_update_workflow_label_missing_source_label` → still passes (primitive just adds the target).
- `test_update_workflow_label_invalid_branch_name` / `_branch_not_linked` / `_label_not_in_config` → unchanged paths; still return `False`.
- `test_update_workflow_label_github_api_error` → primitive swallows non-auth errors and returns `False`; outer `except` still catches anything else.
- `test_update_workflow_label_removes_different_workflow_label` → the intentional improvement; should pass naturally now.

If any of those tests break, the refactor is wrong — fix the refactor, not the tests.

## Acceptance (local checks)

- All tests in `test_issue_manager_label_update.py` pass unchanged.
- All tests in `test_issue_manager_labels.py` (including `TestTransitionIssueLabel` from Step 2) pass unchanged.
- Full suite: `pytest -n auto -m "not <integration markers>"` green.
- pylint / mypy / ruff / lint-imports clean.

## Scope guard

- Do NOT change the public signature of `update_workflow_label`.
- Do NOT change `labels.json` / `label_config.py` / branch resolution helpers.
- Do NOT modify the primitive added in Step 2.
- Do NOT remove the `user_config` fallback from `BaseGitHubManager` (that's issue ⑤).
