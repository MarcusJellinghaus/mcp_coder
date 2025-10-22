# Step 7: Add Error Handling for PR Summary Generation

## Context
See `pr_info/steps/summary.md` for full architectural context.

This step adds specific exception handling around the `generate_pr_summary()` call to properly handle LLM failures.

## Objective
Wrap `generate_pr_summary()` call with try-except to catch specific exceptions and return exit code 1.

---

## WHERE
**File to modify:** `src/mcp_coder/workflows/create_pr/core.py`

**Location:** Line ~287 in `run_create_pr_workflow()` function

---

## WHAT - Changes Required

### Current Code
```python
# Step 2: Generate PR summary
log_step("Step 2/5: Generating PR summary...")
title, body = generate_pr_summary(project_dir, provider, method)
```

### Updated Code
```python
# Step 2: Generate PR summary
log_step("Step 2/5: Generating PR summary...")
try:
    title, body = generate_pr_summary(project_dir, provider, method)
except (ValueError, FileNotFoundError) as e:
    logger.error(f"Failed to generate PR summary: {e}")
    return 1
```

---

## HOW - Implementation Details

### Exception Types to Catch

**ValueError:** Raised when LLM returns empty response
- Source: `generate_pr_summary()` line ~169
- Condition: `if not llm_response or not llm_response.strip()`

**FileNotFoundError:** Raised when prompt file not found
- Source: `get_prompt()` call in `generate_pr_summary()` line ~157
- Condition: Prompt file missing at `PROMPTS_FILE_PATH`

### Why These Specific Exceptions?

Looking at `generate_pr_summary()` implementation:
```python
# Can raise FileNotFoundError
prompt_template = get_prompt(str(PROMPTS_FILE_PATH), "PR Summary Generation")

# Can raise ValueError
if not llm_response or not llm_response.strip():
    raise ValueError("LLM returned empty response")
```

Other exceptions (like generic `Exception` from LLM API) will propagate up to CLI layer.

---

## ALGORITHM - Error Handling Flow

```
1. Log start of PR summary generation step
2. TRY:
   - Call generate_pr_summary(project_dir, provider, method)
   - Continue with returned title and body
3. CATCH ValueError (empty LLM response):
   - Log error with details
   - Return exit code 1 (failure)
4. CATCH FileNotFoundError (missing prompt):
   - Log error with details
   - Return exit code 1 (failure)
5. Other exceptions propagate to CLI layer
```

---

## VALIDATION

### Manual Testing
```python
# Test with mocked ValueError
# In test: mock_generate.side_effect = ValueError("Empty response")
# Expected: workflow returns 1, logs error
```

### Automated Testing
```bash
# Run workflow tests (includes exception test)
pytest tests/workflows/create_pr/test_workflow.py::TestRunCreatePrWorkflow::test_workflow_generate_summary_exception -v

# Expected: Test PASS
```

### Code Quality
```bash
# Pylint check
pylint src/mcp_coder/workflows/create_pr/core.py

# Mypy check
mypy src/mcp_coder/workflows/create_pr/core.py
```

---

## LLM Prompt for This Step

```
I'm implementing Step 7 of the create_PR to CLI command conversion.

Context: See pr_info/steps/summary.md for architecture.

Task: Add error handling for PR summary generation.

Step 7 Details: Read pr_info/steps/step_7.md

Instructions:
1. Open src/mcp_coder/workflows/create_pr/core.py
2. Find the generate_pr_summary() call in run_create_pr_workflow()
3. Wrap it with try-except catching (ValueError, FileNotFoundError)
4. Log error and return 1 on exception
5. Run tests to verify
6. Commit with message: "Add error handling for PR summary generation"

Simple change - just add 4 lines of error handling code.
```

---

## Verification Checklist

- [ ] Try-except added around `generate_pr_summary()` call
- [ ] Catches `ValueError` and `FileNotFoundError`
- [ ] Logs error message with details
- [ ] Returns exit code 1 on exception
- [ ] Test passes: `pytest tests/workflows/create_pr/test_workflow.py -v`
- [ ] Pylint passes
- [ ] Mypy passes
- [ ] Commit created

---

## Dependencies

### Required Before This Step
- ✅ Step 2 completed (workflow core exists)
- ✅ Step 6 completed (tests exist to verify behavior)

### Blocks
- Step 10 (final validation)

---

## Notes

- **Specific exceptions only:** Only catch ValueError and FileNotFoundError
- **Other exceptions propagate:** Let CLI layer handle unexpected errors
- **Consistent with workflow pattern:** Other error handling returns 1
- **Quick change:** Should take ~10 minutes
