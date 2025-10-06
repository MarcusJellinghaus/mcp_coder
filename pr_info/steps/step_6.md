# Step 6: Update CLI Commands (Minimal Changes)

## Context
Read `pr_info/steps/summary.md` for full context. CLI commands remain mostly unchanged since workflows handle env preparation internally.

## WHERE

**Modified files:**
- `src/mcp_coder/cli/commands/prompt.py`
- `tests/cli/commands/test_prompt.py`

**Note:** `implement.py` and `commit.py` need NO changes - workflows handle env internally.

## WHAT

### Only prompt.py needs updates

The prompt command directly calls LLM functions, so it needs to prepare env vars:

```python
# In execute_prompt() function

# Add import
from ...llm.env import prepare_llm_environment

# Add after timeout/llm_method parsing
try:
    project_dir = Path.cwd()
    env_vars = prepare_llm_environment(project_dir)
except RuntimeError as e:
    # No venv found - continue without env vars for backward compat
    logger.warning(f"Could not prepare environment: {e}")
    env_vars = None

# Pass to ask_llm/prompt_llm/ask_claude_code_api_detailed_sync
response = ask_llm(..., env_vars=env_vars)
```

## HOW

**Integration:**
- Prompt command calls LLM functions directly (not via workflow)
- Try to prepare env_vars, but don't fail if venv missing (graceful degradation)
- Pass env_vars to all LLM function calls

## ALGORITHM

```
1. Import prepare_llm_environment
2. Try prepare_llm_environment(Path.cwd())
3. Catch RuntimeError -> log warning, set env_vars=None
4. Pass env_vars to ask_llm/prompt_llm calls
```

## DATA

**No signature changes to execute_prompt()**

## Test Coverage

**New tests:**
```python
def test_execute_prompt_with_env_vars():
    """Verify env_vars prepared and passed."""

def test_execute_prompt_no_venv_graceful():
    """Verify graceful handling when no venv."""
```

**Extend existing tests:**
- Mock `prepare_llm_environment` 
- Verify it's called and env_vars passed

## LLM Prompt

```
Context: Read pr_info/steps/summary.md and pr_info/steps/step_6.md

Task: Update prompt command to prepare environment variables.

Changes (only in cli/commands/prompt.py):
1. Import prepare_llm_environment
2. In execute_prompt():
   - Try prepare_llm_environment(Path.cwd())
   - Catch RuntimeError -> log warning, use env_vars=None
   - Pass env_vars to ask_llm(), prompt_llm(), ask_claude_code_api_detailed_sync()

Tests in tests/cli/commands/test_prompt.py:
1. Test env_vars prepared and passed
2. Test graceful handling when no venv
3. Run tests

Note: implement.py and commit.py need NO changes - workflows handle env internally.

Follow TDD: Write tests first, then implementation.
```
