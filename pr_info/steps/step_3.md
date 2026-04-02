# Step 3: create-pr Workflow — Remove log_step(), Add PR Summary Fields

## LLM Prompt
> Read `pr_info/steps/summary.md` for full context. Implement Step 3: Remove log_step() from create_pr/core.py, replace all call sites with logger.log(OUTPUT, ...), add PR summary fields after creation. Update any tests that reference log_step. Run all three code quality checks after changes.

## WHERE
- `src/mcp_coder/workflows/create_pr/core.py` — main changes
- `tests/workflows/create_pr/test_workflow.py` — update if tests reference `log_step`

## WHAT

### 3a. Remove `log_step()` function

Delete the function entirely:
```python
# DELETE THIS:
def log_step(message: str) -> None:
    """Log step with structured logging instead of print."""
    logger.info(message)
```

### 3b. Import OUTPUT constant

Add to imports at top of file:
```python
from mcp_coder.utils.log_utils import OUTPUT
```

### 3c. Replace all `log_step()` call sites

Mechanical replacement pattern:
```python
# BEFORE
log_step("Step 1/5: Checking prerequisites...")
log_step(f"Using project directory: {project_dir}")
log_step("Commits pushed successfully")

# AFTER
logger.log(OUTPUT, "Step 1/5: Checking prerequisites...")
logger.log(OUTPUT, "Using project directory: %s", project_dir)
logger.log(OUTPUT, "Commits pushed successfully")
```

**Important:** Use `%s` formatting (lazy logging) instead of f-strings for `logger.log()` calls. This is a pylint requirement.

All `log_step()` calls in `run_create_pr_workflow()` should be converted. There are approximately 20 call sites. Keep "Step N/5:" prefix as-is.

### 3d. Add PR summary fields after creation

After the PR is successfully created (after `create_pull_request()` returns), replace the single combined log line with individual fields:

```python
# BEFORE
log_step(f"Pull request created: #{pr_number} ({pr_url})")

# AFTER
pr_title = title  # Already available in scope
current_branch = get_current_branch_name(project_dir)
base_branch = detect_base_branch(project_dir, current_branch=current_branch)
logger.log(OUTPUT, "PR Number: #%s", pr_number)
logger.log(OUTPUT, "PR URL: %s", pr_url)
logger.log(OUTPUT, "PR Title: %s", pr_title)
logger.log(OUTPUT, "Base Branch: %s", base_branch)
logger.log(OUTPUT, "Head Branch: %s", current_branch)
```

Note: `current_branch` and `base_branch` are already computed earlier in the workflow and may need to be captured in local variables, OR re-fetched here. Check the existing code — `create_pull_request()` already computes these internally. The simplest approach is to use `title` (already in scope) and extract from `pr_result` dict or re-derive.

### 3e. Keep detail messages at INFO

Messages inside helper functions (`generate_pr_summary`, `cleanup_repository`, `create_pull_request`, etc.) already use `logger.info()` and `logger.error()`. These stay as-is — they're invisible at OUTPUT threshold and visible at INFO/DEBUG.

## DATA
- `pr_result` dict contains: `{"number": int, "url": str, ...}`
- `title` and `body` are local variables from `generate_pr_summary()`
- `current_branch` from `get_current_branch_name()`

## HOW — Integration Points
- `OUTPUT` imported from `mcp_coder.utils.log_utils`
- `logger.log(OUTPUT, ...)` produces records at level 25
- At OUTPUT threshold: visible via CleanFormatter (bare message)
- At INFO threshold: visible via ExtraFieldsFormatter (timestamped)

## ALGORITHM (PR summary output)
```
1. Create PR via create_pull_request()
2. If successful, log each field on its own line:
   PR Number, PR URL, PR Title, Base Branch, Head Branch
3. Continue with cleanup steps
```

## Commit Message
```
refactor(create-pr): remove log_step, use OUTPUT level logging

- Remove log_step() wrapper function
- Replace ~20 call sites with logger.log(OUTPUT, ...)
- Add per-field PR summary output at OUTPUT level
- Detail messages stay at INFO (hidden at OUTPUT threshold)
```
