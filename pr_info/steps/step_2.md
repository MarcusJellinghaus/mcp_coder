# Step 2 — Introduce `transition_issue_label` primitive on `LabelsMixin`

## LLM prompt

> Read `pr_info/steps/summary.md` for context, then implement **this step only** (`pr_info/steps/step_2.md`) in a single commit. Use TDD: write `TestTransitionIssueLabel` first, then the primitive, then run all quality checks. Do not refactor `update_workflow_label` in this step — that is Step 3. Do not modify Step 1 code.

## WHERE

- `src/mcp_coder/utils/github_operations/issues/labels_mixin.py` — add new public method `transition_issue_label` alongside `add_labels` / `remove_labels` / `set_labels`.
- `tests/utils/github_operations/test_issue_manager_labels.py` — add new `TestTransitionIssueLabel` class.

## WHAT — function signature

```python
@log_function_call
@_handle_github_errors(default_return=False)
def transition_issue_label(
    self: "BaseGitHubManager",
    issue_number: int,
    new_label: str,
    labels_to_clear: Iterable[str] = (),
) -> bool:
    """Atomic label transition primitive — no workflow semantics.

    Computes (current - labels_to_clear) | {new_label} and applies via set_labels.
    Idempotent: if new_label already present AND no overlap with labels_to_clear,
    returns True without calling set_labels.
    """
```

## HOW — integration

- Add `from typing import Iterable, List` (or extend existing typing import).
- Primitive is a mixin method — accessed via `IssueManager.transition_issue_label(...)`.
- Decorators in this order: `@log_function_call` then `@_handle_github_errors(default_return=False)` (matches `add_labels` / `remove_labels` / `set_labels`).
- Uses `validate_issue_number` already imported from `.base`.
- Calls `self.get_issue(issue_number)` (provided by `IssueManager`, which also inherits from `BaseGitHubManager`).
- Calls `self.set_labels(issue_number, *new_labels)` (sibling mixin method).
- `ValueError` from `validate_issue_number` propagates (decorator re-raises).
- 401/403 `GithubException` propagates (decorator re-raises).
- Other errors → logged, return `False`.

## ALGORITHM — primitive body

```
validate_issue_number(issue_number)
issue = self.get_issue(issue_number)
current = set(issue["labels"])
to_clear = set(labels_to_clear)
if new_label in current and not (to_clear & current):
    return True  # idempotent short-circuit
new_labels = (current - to_clear) | {new_label}
result = self.set_labels(issue_number, *new_labels)
return result["number"] != 0
```

## DATA

- Input: `issue_number: int`, `new_label: str`, `labels_to_clear: Iterable[str] = ()`.
- Output: `bool` — `True` on success (including idempotent no-op), `False` on swallowed error or failed `set_labels`.
- No new TypedDicts, no new fixtures.

## Tests (write first) — new `TestTransitionIssueLabel` class

Use the existing `mock_issue_manager` fixture (from `tests/utils/github_operations/conftest.py`). Patch `get_issue` and `set_labels` on `IssueManager` via `patch.object` per test. Mock-based, no integration marker.

Cases (each a single test method):

1. `test_transition_basic_adds_and_clears` — current=`{implementing, bug}`, new=`code_review`, clear=`{implementing, planning}` → `set_labels` called with `{code_review, bug}`; returns `True`.
2. `test_transition_idempotent_noop_when_target_present_and_no_overlap` — current=`{code_review, bug}`, new=`code_review`, clear=`{implementing}` → `set_labels` NOT called; returns `True`.
3. `test_transition_clears_stray_labels` — current=`{code_review, planning}`, new=`code_review`, clear=`{implementing, planning}` → `set_labels` called with `{code_review}` (planning stripped, intentional behavior improvement); returns `True`.
4. `test_transition_empty_labels_to_clear_just_adds_new` — current=`{bug}`, new=`code_review`, clear=`()` → `set_labels` called with `{bug, code_review}`; returns `True`.
5. `test_transition_invalid_issue_number_raises` — `issue_number=0` → `ValueError` propagates (not caught by decorator).
6. `test_transition_auth_error_reraises` — `get_issue` / `set_labels` raises `GithubException(401)` → re-raised by decorator.
7. `test_transition_set_labels_failure_returns_false` — `set_labels` returns empty `IssueData` (`number=0`) → primitive returns `False`.

## Acceptance (local checks)

- `TestTransitionIssueLabel` tests all green.
- pylint / pytest / mypy / ruff / lint-imports clean.
- `test_issue_manager_label_update.py` tests still pass (no changes yet expected — `update_workflow_label` unchanged in this step).

## Scope guard

- Do NOT touch `update_workflow_label` yet (Step 3).
- Do NOT touch `labels.json`, `label_config.py`, or any caller.
- Primitive takes NO `current_labels` param, NO `labels_config`, NO `internal_id` — pure label math.
