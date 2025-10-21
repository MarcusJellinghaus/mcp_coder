# Step 2: Create Workflow Package and Core Logic

## Context
Read `pr_info/steps/summary.md` for full architectural context.

This step creates the workflow package structure and moves the core workflow logic from the standalone script into the new package, following the pattern from the `implement` workflow.

## Objective
Move `workflows/create_PR.py` to `src/mcp_coder/workflows/create_pr/core.py` with minimal changes to maintain existing functionality while integrating with the new CLI interface.

---

## Part A: Create Workflow Package Structure

### WHERE - Files to Create

1. **`src/mcp_coder/workflows/create_pr/__init__.py`**
2. **`src/mcp_coder/workflows/create_pr/core.py`**

---

### File 1: Package Initialization

**File:** `src/mcp_coder/workflows/create_pr/__init__.py`

**Content:**
```python
"""Create PR workflow package.

This package provides functionality for creating pull requests with
AI-generated summaries and automated repository cleanup.
"""

from .core import run_create_pr_workflow

__all__ = [
    "run_create_pr_workflow",
]
```

---

### File 2: Core Workflow Logic

**File:** `src/mcp_coder/workflows/create_pr/core.py`

**Source:** Copy from `workflows/create_PR.py`

**Required Changes:**

#### 1. Remove Duplicate Functions
Delete these functions (use shared utilities instead):
- `parse_arguments()` - CLI handles argument parsing
- `resolve_project_dir()` - Use from `workflows.utils`
- `main()` - Replace with `run_create_pr_workflow()`

#### 2. Update `generate_pr_summary()` Signature

**OLD:**
```python
def generate_pr_summary(project_dir: Path, llm_method: str = "claude_code_api") -> Tuple[str, str]:
```

**NEW:**
```python
def generate_pr_summary(project_dir: Path, provider: str, method: str) -> Tuple[str, str]:
    """Generate PR title and body using LLM and git diff.
    
    Args:
        project_dir: Path to project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
        
    Returns:
        Tuple of (title, body) strings
    """
```

**Update internal call:**
```python
# OLD:
provider, method = parse_llm_method(llm_method)
llm_response = ask_llm(full_prompt, provider=provider, method=method, timeout=300)

# NEW (already has provider, method):
llm_response = ask_llm(full_prompt, provider=provider, method=method, timeout=300)
```

#### 3. Create New Main Function

**Replace `main()` with:**

```python
def run_create_pr_workflow(project_dir: Path, provider: str, method: str) -> int:
    """Main workflow orchestration function - creates PR and cleans up repository.
    
    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
    
    Returns:
        int: Exit code
            0 - Complete success (PR created and cleanup completed)
            1 - Error (prerequisites failed or PR creation failed)
            2 - Partial success (PR created but cleanup failed)
    """
    log_step("Starting create PR workflow...")
    log_step(f"Using project directory: {project_dir}")
    
    # Step 1: Check prerequisites
    log_step("Step 1/4: Checking prerequisites...")
    if not check_prerequisites(project_dir):
        logger.error("Prerequisites check failed")
        return 1
    
    # Step 2: Generate PR summary
    log_step("Step 2/5: Generating PR summary...")
    title, body = generate_pr_summary(project_dir, provider, method)
    
    # Step 3: Push any existing commits
    log_step("Step 3/5: Pushing commits...")
    push_result = git_push(project_dir)
    if not push_result["success"]:
        logger.warning(f"Failed to push commits: {push_result['error']}")
    else:
        log_step("Commits pushed successfully")
    
    # Step 4: Create pull request
    log_step("Step 4/5: Creating pull request...")
    if not create_pull_request(project_dir, title, body):
        logger.error("Failed to create pull request")
        return 1
    
    # Step 5: Clean up repository
    log_step("Step 5/5: Cleaning up repository...")
    cleanup_success = cleanup_repository(project_dir)
    
    if cleanup_success:
        # Check if there are changes to commit
        if not is_working_directory_clean(project_dir):
            # Commit cleanup changes
            log_step("Committing cleanup changes...")
            commit_result = commit_all_changes(
                "Clean up pr_info/steps planning files", 
                project_dir
            )
            
            if commit_result["success"]:
                log_step(f"Cleanup committed: {commit_result['commit_hash']}")
                
                # Push cleanup commit
                log_step("Pushing cleanup changes...")
                push_result = git_push(project_dir)
                
                if push_result["success"]:
                    log_step("Cleanup changes pushed successfully")
                else:
                    logger.warning(f"Failed to push cleanup changes: {push_result['error']}")
                    log_step("PR created successfully, but cleanup push failed")
                    return 2  # Partial success
            else:
                # Don't warn about "No staged files" - this is expected when cleanup had no effect
                error_msg = commit_result.get("error", "")
                if error_msg and "No staged files" in error_msg:
                    log_step("No cleanup changes to commit (files were already clean)")
                else:
                    logger.warning(f"Failed to commit cleanup changes: {commit_result['error']}")
                    log_step("PR created successfully, but cleanup commit failed")
                    return 2  # Partial success
        else:
            log_step("No cleanup changes to commit")
    else:
        logger.warning("Repository cleanup completed with errors, but PR was created successfully")
        return 2  # Partial success
    
    log_step("Create PR workflow completed successfully!")
    return 0
```

#### 4. Remove Unused Imports

Delete:
```python
import argparse  # No longer needed
import sys  # No longer needed (returns int instead of sys.exit)
```

#### 5. Keep All Other Functions Unchanged

All these functions remain exactly as-is:
- `delete_steps_directory()`
- `clean_profiler_output()`
- `truncate_task_tracker()`
- `parse_pr_summary()`
- `check_prerequisites()`
- `_load_prompt_or_exit()`
- `cleanup_repository()`
- `create_pull_request()`
- `log_step()`

### ALGORITHM - Migration Steps (Pseudocode)

```
1. Copy workflows/create_PR.py → src/mcp_coder/workflows/create_pr/core.py
2. Remove: parse_arguments(), resolve_project_dir(), main()
3. Update: generate_pr_summary() signature (llm_method → provider, method)
4. Create: run_create_pr_workflow() based on old main()
5. Remove: argparse and sys imports
6. Keep: All other functions unchanged
```

### DATA - Function Signatures Summary

**New/Changed:**
```python
def run_create_pr_workflow(project_dir: Path, provider: str, method: str) -> int

def generate_pr_summary(project_dir: Path, provider: str, method: str) -> Tuple[str, str]
```

**Unchanged (20+ functions):**
```python
def delete_steps_directory(project_dir: Path) -> bool
def clean_profiler_output(project_dir: Path) -> bool
def truncate_task_tracker(project_dir: Path) -> bool
def parse_pr_summary(llm_response: str) -> Tuple[str, str]
def check_prerequisites(project_dir: Path) -> bool
def _load_prompt_or_exit(header: str) -> str
def cleanup_repository(project_dir: Path) -> bool
def create_pull_request(project_dir: Path, title: str, body: str) -> bool
def log_step(message: str) -> None
# ... plus all other helper functions
```

---

## Part B: Update Existing Tests to Use New Module Path

### WHERE
Update import statements in all existing test files:

1. `tests/workflows/create_pr/test_file_operations.py`
2. `tests/workflows/create_pr/test_parsing.py`
3. `tests/workflows/create_pr/test_prerequisites.py`
4. `tests/workflows/create_pr/test_generation.py`
5. `tests/workflows/create_pr/test_repository.py`
6. `tests/workflows/create_pr/test_main.py`

### WHAT - Import Changes

**OLD (current):**
```python
from workflows.create_PR import function_name
```

**NEW (target):**
```python
from mcp_coder.workflows.create_pr.core import function_name
```

### HOW - Find and Replace

For each test file, replace:
- `from workflows.create_PR import` → `from mcp_coder.workflows.create_pr.core import`
- `@patch("workflows.create_PR.` → `@patch("mcp_coder.workflows.create_pr.core.`

---

## Part C: Validate Tests Pass

### TEST EXECUTION
```bash
# Run all create_pr workflow tests
pytest tests/workflows/create_pr/ -v

# All tests should PASS now
```

### CODE QUALITY CHECKS
```bash
# Pylint check on new module
pylint src/mcp_coder/workflows/create_pr/

# Mypy check on new module
mypy src/mcp_coder/workflows/create_pr/

# All checks should PASS
```

---

## LLM Prompt for This Step

```
I'm implementing Step 2 of the create_PR to CLI command conversion (Issue #139).

Context: Read pr_info/steps/summary.md for full architectural overview.

Task: Create workflow package and migrate core logic from standalone script.

Step 2 Details: Read pr_info/steps/step_2.md

Instructions:
1. Create src/mcp_coder/workflows/create_pr/__init__.py (package initialization)
2. Create src/mcp_coder/workflows/create_pr/core.py by:
   - Copying from workflows/create_PR.py
   - Removing: parse_arguments(), resolve_project_dir(), main()
   - Updating: generate_pr_summary() signature
   - Creating: run_create_pr_workflow() function
3. Update all test file imports (tests/workflows/create_pr/*.py) from workflows.create_PR to mcp_coder.workflows.create_pr.core
4. Run tests (they should PASS)
5. Run code quality checks (pylint, mypy)

Reference: src/mcp_coder/workflows/implement/core.py for workflow pattern

Keep all existing helper functions unchanged - minimal changes only!
```

---

## Verification Checklist

- [ ] All test imports updated to new module path
- [ ] Package created: `src/mcp_coder/workflows/create_pr/__init__.py`
- [ ] Core module created: `src/mcp_coder/workflows/create_pr/core.py`
- [ ] Removed: `parse_arguments()`, `resolve_project_dir()`, `main()`
- [ ] Updated: `generate_pr_summary()` signature
- [ ] Created: `run_create_pr_workflow()` function
- [ ] All tests pass: `pytest tests/workflows/create_pr/ -v`
- [ ] Pylint passes: `pylint src/mcp_coder/workflows/create_pr/`
- [ ] Mypy passes: `mypy src/mcp_coder/workflows/create_pr/`

## Dependencies

### Required Before This Step
- ✅ Step 1 completed (CLI command interface exists)
- ✅ All existing tests passing

### Blocks
- Step 3 (CLI main integration needs workflow to exist)

## Notes

- **KISS principle applied:** Keep all functions in one file (core.py)
- No splitting into multiple modules - current size (~500 lines) is manageable
- Minimal changes - only remove duplication and update entry point
- All existing tests continue to work with simple import updates
- Pattern matches `implement` workflow architecture
