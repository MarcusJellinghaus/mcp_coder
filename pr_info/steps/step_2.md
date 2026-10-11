# Step 2: Always resolve the issue number and inject the closing reference

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`. Step 1 (`ensure_closing_reference`) is already in place. Update the tests first, then `core.py`. Run pylint, mypy and the fast pytest suite (`-n auto`, integration markers excluded) and make sure all pass. Then run the formatter and produce one commit.

## WHERE

- `src/mcp_coder/workflows/create_pr/core.py`: `run_create_pr_workflow`
- `tests/workflows/create_pr/conftest.py`: **new**
- `tests/workflows/create_pr/test_workflow.py`
- `tests/workflows/test_create_pr_integration.py`

## WHAT / HOW

### `core.py`: `run_create_pr_workflow`

1. Replace the gated block:
   ```python
   cached_issue_number: Optional[int] = validate_branch_issue_linkage(project_dir)
   if cached_issue_number:
       logger.log(OUTPUT, "Branch linked to issue #%s", cached_issue_number)
   else:
       logger.warning("Branch not linked to any issue")
   ```
   Keep the existing comment explaining why this must run before PR creation. Update its wording: the cached value now serves both label updates and the closing reference.
2. In step 5, immediately before `create_pull_request(project_dir, title, body)`:
   ```python
   if cached_issue_number:
       body = ensure_closing_reference(body, cached_issue_number)
   ```
3. Nothing else changes. The post-creation `get_closing_issue_numbers` fallback and the label-update logic stay as they are.

### `tests/workflows/create_pr/conftest.py` (new)

```python
@pytest.fixture(autouse=True)
def _no_branch_issue_link() -> Iterator[MagicMock]:
    """Default: branch not linked. Tests override with their own @patch."""
    with patch(
        "mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage",
        return_value=None,
    ) as mock:
        yield mock
```

Tests that use `@patch(...validate_branch_issue_linkage)` apply their patch inside the fixture's patch, so they still win. `test_workflow_helpers.py` imports the real function object directly, so it is unaffected.

### `tests/workflows/test_create_pr_integration.py`

In `TestWorkflowMainFunction`, add `@patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage", return_value=None)` to `test_main_workflow_prerequisite_failure` and `test_main_workflow_pr_creation_failure`. Add the matching mock argument to each.

## Tests (write first) in `test_workflow.py`

Reuse the mock setup of `test_workflow_session_params_passed_to_generate_summary`: patch prerequisites, generate, push, create_pull_request, cleanup, is_working_directory_clean, get_current_branch_name, detect_base_branch and `_add_pr_assignee_best_effort`. `mock_generate` returns `("Title", "Body")`.

1. `test_workflow_appends_closing_reference_without_label_updates`
   - `@patch(...validate_branch_issue_linkage, return_value=123)`, called with `update_issue_labels=False` (the default).
   - Assert `result == 0` and `mock_validate.assert_called_once_with(Path("/test"))`.
   - Assert `mock_create_pr.assert_called_once_with(Path("/test"), "Title", "Body\n\nCloses #123")`.
2. `test_workflow_leaves_body_unchanged_when_not_linked`
   - Relies on the conftest default (`None`).
   - Assert `mock_create_pr.assert_called_once_with(Path("/test"), "Title", "Body")`.

## DATA

There are no new return values. `run_create_pr_workflow` still returns `0` or `1`.
