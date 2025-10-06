# Step 5: Update Workflows with Environment Preparation

## Context
Read `pr_info/steps/summary.md` for full context. Workflows prepare env vars internally.

## WHERE

**Modified files:**
- `src/mcp_coder/workflows/implement/core.py`
- `src/mcp_coder/utils/commit_operations.py`
- `tests/workflows/implement/test_core.py`
- `tests/utils/test_commit_operations.py`

## WHAT

### Changes to run_implement_workflow()

```python
# In src/mcp_coder/workflows/implement/core.py

# Add import at top
from ...llm.env import prepare_llm_environment

# In prepare_task_tracker() function
def prepare_task_tracker(project_dir: Path, provider: str, method: str) -> bool:
    # Add after logger.info about generating tasks
    env_vars = prepare_llm_environment(project_dir)  # NEW
    
    response = ask_llm(
        prompt_template, provider=provider, method=method, timeout=300,
        env_vars=env_vars  # NEW
    )
```

### Changes to generate_commit_message_with_llm()

```python
# In src/mcp_coder/utils/commit_operations.py

# Add import at top
from ..llm.env import prepare_llm_environment

# In generate_commit_message_with_llm() function
def generate_commit_message_with_llm(
    project_dir: Path, provider: str = "claude", method: str = "api"
) -> Tuple[bool, str, Optional[str]]:
    # Add early in function
    env_vars = prepare_llm_environment(project_dir)  # NEW
    
    # Later when calling ask_llm
    response = ask_llm(
        full_prompt,
        provider=provider,
        method=method,
        timeout=LLM_COMMIT_TIMEOUT_SECONDS,
        env_vars=env_vars  # NEW
    )
```

## HOW

**Integration:**
- Import `prepare_llm_environment` from `llm.env`
- Call it to get env_vars dict
- Pass env_vars to `ask_llm()`
- Handle RuntimeError if venv not found

## ALGORITHM

```
1. Import prepare_llm_environment
2. Call prepare_llm_environment(project_dir) to get env_vars
3. Pass env_vars to ask_llm() call
4. Let RuntimeError propagate if no venv found
```

## DATA

**No signature changes** - workflows handle env internally

## Test Coverage

**Mock prepare_llm_environment in tests:**
```python
@patch('mcp_coder.llm.env.prepare_llm_environment')
def test_prepare_task_tracker_sets_env_vars(mock_env, ...):
    mock_env.return_value = {'MCP_CODER_PROJECT_DIR': '/test'}
    # Verify ask_llm called with env_vars
```

**Test error handling:**
```python
def test_prepare_task_tracker_no_venv_error():
    """Verify RuntimeError propagates when no venv."""
```

## LLM Prompt

```
Context: Read pr_info/steps/summary.md and pr_info/steps/step_5.md

Task: Add environment preparation to workflows.

Changes:
1. In workflows/implement/core.py:
   - Import prepare_llm_environment
   - Add env_vars = prepare_llm_environment(project_dir) in prepare_task_tracker()
   - Pass env_vars to ask_llm()

2. In utils/commit_operations.py:
   - Import prepare_llm_environment
   - Add env_vars = prepare_llm_environment(project_dir) in generate_commit_message_with_llm()
   - Pass env_vars to ask_llm()

Tests:
1. Mock prepare_llm_environment in workflow tests
2. Verify env_vars passed to ask_llm
3. Test error handling for RuntimeError
4. Run tests

Follow TDD: Write tests first, then implementation.
```
