# Step 4: Implement Main Workflow Script with Tests

## WHERE
- **Test File**: `tests/test_create_pr.py` (extend existing)
- **Implementation**: `workflows/create_PR.py` (complete main function)

## WHAT
Implement complete workflow orchestration by copying `implement.py` structure and replacing workflow logic.

### Main Function Signature
```python
def main() -> None
```

### Helper Functions
```python
def parse_pr_summary(llm_response: str) -> tuple[str, str]  # title, body
def check_prerequisites(project_dir: Path) -> bool
def generate_pr_summary(project_dir: Path) -> tuple[str, str]
def cleanup_repository(project_dir: Path) -> bool
def create_pull_request(project_dir: Path, title: str, body: str) -> bool
```

## HOW

### Integration Points
- **Copy Structure**: Use `implement.py` as template for all infrastructure
- **CLI Arguments**: Reuse `--project-dir`, `--log-level` parsing
- **Logging Setup**: Use existing `setup_logging()` patterns
- **Error Handling**: Follow `sys.exit(1)` patterns from implement.py
- **Dependencies**: Import all required modules from existing codebase

### Workflow Steps
1. Parse arguments and setup logging (reuse implement.py)
2. Validate prerequisites (git clean + no incomplete tasks)
3. Generate PR summary using LLM + git diff
4. Clean up repository state
5. Create GitHub pull request
6. Log success and exit

## ALGORITHM (Pseudocode)
```
1. Setup CLI, logging, project validation (copy from implement.py)
2. Check git clean AND no incomplete tasks (exit if fail)
3. Get branch diff, load prompt, call LLM for summary
4. Parse LLM response into title and body
5. Delete steps directory, truncate task tracker
6. Commit cleanup changes and push
7. Create PR via PullRequestManager
8. Log success message and exit
```

## LLM Prompt

### Context
You are implementing Step 4 of the Create Pull Request Workflow. Review the summary document in `pr_info/steps/summary.md` for full context. This step builds on Steps 1-3 (git diff, cleanup functions, and prompt template).

### Task
Complete the `workflows/create_PR.py` script by implementing the main workflow orchestration.

### Requirements
1. **Copy Infrastructure**: Use `workflows/implement.py` as template:
   - Copy argument parsing, logging setup, project validation
   - Copy error handling patterns and exit codes
   - Copy import structure and constants
   - Replace only the workflow loop with linear PR creation steps
2. **Integration**: Use functions from previous steps:
   - `get_branch_diff()` from git_operations
   - `delete_steps_directory()` and `truncate_task_tracker()` 
   - `get_incomplete_tasks()` for prerequisite check
   - `PullRequestManager` for PR creation
3. **Test Coverage**: Extend tests in `tests/test_create_pr.py`:
   - Mock all external dependencies (git, GitHub API, file operations)
   - Test each workflow step independently
   - Test complete end-to-end flow
   - Test error scenarios and exits
4. **KISS Principle**: Keep workflow simple and linear:
   - No loops or complex state management
   - Clear step-by-step progression
   - Fail fast on any error

### Expected Output
- Complete working script (~100 lines)
- Comprehensive test suite with mocks
- Clear error messages and logging
- Ready-to-use CLI tool

### Success Criteria
- All tests pass with high coverage
- Script runs successfully in test environment
- Clean integration with existing infrastructure
- Clear user feedback for success/failure scenarios