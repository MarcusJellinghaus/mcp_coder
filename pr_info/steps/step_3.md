# Step 3: Update Existing `WorkflowFailure(...)` Constructions with `build_url` and `elapsed_time`

## Context

See [summary.md](summary.md) for full context. This step is a mechanical change: capture `start_time` and `build_url` at the top of `run_implement_workflow()`, and pass them to every existing `WorkflowFailure(...)` construction.

## WHERE

- **Source**: `src/mcp_coder/workflows/implement/core.py` — `run_implement_workflow()` function
- **Tests**: `tests/workflows/implement/test_core.py`

## WHAT

### At top of `run_implement_workflow()`:

```python
import os
import time

def run_implement_workflow(project_dir, provider, mcp_config=None, execution_dir=None) -> int:
    start_time = time.time()
    build_url = os.environ.get("BUILD_URL")
    # ... rest of existing code ...
```

### Update every existing `WorkflowFailure(...)`:

Every existing `WorkflowFailure(...)` construction in `run_implement_workflow()` gains two keyword arguments:

```python
# Before:
WorkflowFailure(
    category=FailureCategory.GENERAL,
    stage="Task tracker preparation",
    message="...",
)

# After:
WorkflowFailure(
    category=FailureCategory.GENERAL,
    stage="Task tracker preparation",
    message="...",
    build_url=build_url,
    elapsed_time=time.time() - start_time,
)
```

## HOW

- Add `import os` if not present
- Add `start_time = time.time()` and `build_url = os.environ.get("BUILD_URL")` at top of function
- Find every `WorkflowFailure(...)` in the function and add `build_url=build_url, elapsed_time=time.time() - start_time`
- Purely mechanical — no logic changes

## TESTS

Add to `tests/workflows/implement/test_core.py`:

```python
class TestExistingFailuresIncludeNewFields:
    def test_existing_failures_include_build_url_and_elapsed(self):
        """Existing handled failures include build_url and elapsed_time."""
        with patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True), \
             patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push"), \
             patch("mcp_coder.workflows.implement.core.prepare_task_tracker", return_value=False), \
             patch("mcp_coder.workflows.implement.core._handle_workflow_failure") as mock_handle, \
             patch.dict(os.environ, {"BUILD_URL": "https://jenkins.example.com/job/2/console"}):

            run_implement_workflow(Path("/fake"), "claude")

            failure = mock_handle.call_args[0][0]
            assert failure.build_url == "https://jenkins.example.com/job/2/console"
            assert failure.elapsed_time is not None
            assert failure.elapsed_time >= 0

    def test_build_url_none_when_env_not_set(self):
        """build_url is None when BUILD_URL env var is not set."""
        with patch("mcp_coder.workflows.implement.core.check_git_clean", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_main_branch", return_value=True), \
             patch("mcp_coder.workflows.implement.core.check_prerequisites", return_value=True), \
             patch("mcp_coder.workflows.implement.core._attempt_rebase_and_push"), \
             patch("mcp_coder.workflows.implement.core.prepare_task_tracker", return_value=False), \
             patch("mcp_coder.workflows.implement.core._handle_workflow_failure") as mock_handle, \
             patch.dict(os.environ, {}, clear=True):

            run_implement_workflow(Path("/fake"), "claude")

            failure = mock_handle.call_args[0][0]
            assert failure.build_url is None
```

## COMMIT

`feat(core): add build_url and elapsed_time to existing WorkflowFailure constructions (#598)`

## LLM PROMPT

```
Implement Step 3 from pr_info/steps/step_3.md.
Context: pr_info/steps/summary.md

Mechanical change in `src/mcp_coder/workflows/implement/core.py`:

1. Add `import os` if not already present.
2. At top of `run_implement_workflow()`, add:
   - `start_time = time.time()`
   - `build_url = os.environ.get("BUILD_URL")`
3. Update every existing `WorkflowFailure(...)` construction in the function to include:
   - `build_url=build_url`
   - `elapsed_time=time.time() - start_time`
4. Add tests in `tests/workflows/implement/test_core.py` verifying that handled failures include build_url and elapsed_time.

No logic changes — purely adding the two new fields to existing constructions.
Run all code quality checks.
Commit: "feat(core): add build_url and elapsed_time to existing WorkflowFailure constructions (#598)"
```
