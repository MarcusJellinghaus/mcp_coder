# Step 5: Finalization and Prompt File Updates

## Objective

Complete the main workflow orchestration, implement commit/push logic, and update prompt documentation files.

## Files to Modify

- `workflows/create_plan.py` - Add `main()` function and workflow orchestration
- `src/mcp_coder/prompts/prompts.md` - Add Plan Generation Workflow section
- `PR_Info/DEVELOPMENT_PROCESS.md` - Replace inline prompts with links

## Implementation Details

### WHERE

**Workflow completion:**
- `workflows/create_plan.py` - Add `main()` function with full workflow orchestration

**Prompt documentation:**
- `src/mcp_coder/prompts/prompts.md` - Add new section
- `PR_Info/DEVELOPMENT_PROCESS.md` - Update existing section

### WHAT

```python
def main() -> None:
    """Main workflow orchestration function - creates implementation plan for issue."""
```

### HOW

**Imports:**
```python
from mcp_coder.utils import commit_all_changes, git_push
```

**main() function:**
- Parse arguments and setup logging
- Call each step function in sequence with detailed logging
- Exit on any failure with sys.exit(1)
- Commit and push on success

**Prompt file updates:**
- Copy three prompts to prompts.md under new section
- Update DEVELOPMENT_PROCESS.md to reference the new section

### ALGORITHM

**main():**
```
1. args = parse_arguments()
2. project_dir = resolve_project_dir(args.project_dir)
3. setup_logging(args.log_level)
4. Log "Starting create plan workflow..."
5. Log "Step 1/7: Validating prerequisites..."
   - success, issue_data = check_prerequisites(project_dir, args.issue_number)
   - If not success: exit(1)
6. Log "Step 2/7: Managing branch..."
   - branch_name = manage_branch(project_dir, args.issue_number, issue_data["title"])
   - If branch_name is None: exit(1)
7. Log "Step 3/7: Verifying pr_info/steps/ is empty..."
   - If not verify_steps_directory(project_dir): exit(1)
8. Log "Step 4/7: Running initial analysis for issue #X 'Title'..."
9. Log "Step 5/7: Running simplification review..."
10. Log "Step 6/7: Generating implementation plan..."
    - If not run_planning_prompts(project_dir, issue_data, args.llm_method): exit(1)
11. Log "Step 7/7: Validating output files..."
    - If not validate_output_files(project_dir): exit(1)
12. commit_message = f"Initial plan generated for issue #{args.issue_number}"
13. commit_result = commit_all_changes(commit_message, project_dir)
14. If not commit_result["success"]: log warning but continue
15. push_result = git_push(project_dir)
16. If not push_result["success"]: log warning
17. Log "Create plan workflow completed successfully!"
18. exit(0)
```

### DATA

**main() returns:**
```python
None  # Exits with sys.exit(0) or sys.exit(1)
```

## Prompt File Updates

### prompts.md - Add Section

Add after existing sections:

```markdown
## Plan Generation Workflow

Three-prompt sequence for generating implementation plans from GitHub issues.

### Initial Analysis Prompt

```
## Discuss implementation steps
Please take a look at the existing solution, its files and its architecture documentation.
Do you understand the task below?
What are the implementation steps?
Do not yet modify any code!
```

### Simplification Review Prompt

```
Let's review the plan with simplicity in mind. Can we achieve the same goals with a simpler approach? Consider KISS principle and maintainability while preserving the issue's core requirements.
```

### Implementation Plan Creation Prompt

```
## Python Project Implementation Plan Request
Create a **summary** (`pr_info/steps/summary.md`) and **implementation plan** with self-contained steps (`pr_info/steps/step_1.md`, `pr_info/steps/step_2.md`, etc.).
Can you also give a summary of the architectural / design changes in the summary document?
Also list the folders \ modules \ files that should be created or modified by this implementation.

### Requirements:
- Follow **Test-Driven Development** where applicable. 
  Each step should have its own test implementation followed by related functionality implementation.  
- Each step must include a **clear LLM prompt** that references the summary and that specific step
- Apply **KISS principle** - minimize complexity, maximize maintainability
- Keep code changes minimal and follow best practices

### Each Step Must Specify:
- **WHERE**: File paths and module structure
- **WHAT**: Main functions with signatures
- **HOW**: Integration points (decorators, imports, etc.)
- **ALGORITHM**: 5-6 line pseudocode for core logic (if any)
- **DATA**: Return values and data structures
```
```

### DEVELOPMENT_PROCESS.md - Update Section

Replace the three inline prompts section with:

```markdown
**Tools & Prompts:**

#### First plan

To work on an open issue, a branch should be generated and switched.
The branch should be checked out.
The requirements and dev requirements should be installed.
The MCP server should be configured.
The Claude Code system prompt should be configured.

Based on three prompts, an initial plan can be generated.

See: [Plan Generation Workflow](../src/mcp_coder/prompts/prompts.md#plan-generation-workflow) in `src/mcp_coder/prompts/prompts.md`

**Commit** the initial plan with 
```
Initial plan generated for issue #<number>
``` 
```

## Testing

Create `tests/workflows/create_plan/test_main.py`:

```python
def test_main_success_flow()
def test_main_prerequisites_fail()
def test_main_branch_management_fail()
def test_main_steps_directory_not_empty()
def test_main_planning_prompts_fail()
def test_main_validation_fail()
def test_main_commit_message_format()
```

## Acceptance Criteria

- [ ] main() orchestrates all steps in correct order
- [ ] main() uses detailed step logging (1/7 through 7/7)
- [ ] main() includes issue number and title in log messages
- [ ] main() exits on any step failure
- [ ] main() commits with correct message format
- [ ] main() pushes changes automatically
- [ ] Prompts added to prompts.md under new section
- [ ] DEVELOPMENT_PROCESS.md updated with link reference
- [ ] All tests pass with full workflow mocking

## LLM Prompt for Implementation

```
Please implement Step 5 of the create_plan workflow.

Reference the summary at pr_info/steps/summary.md and all previous steps.

Add the main() function to workflows/create_plan.py to complete the workflow.

Also update the prompt documentation files:
- Add "Plan Generation Workflow" section to src/mcp_coder/prompts/prompts.md
- Update PR_Info/DEVELOPMENT_PROCESS.md to reference the new section

Key requirements:
- Implement main() with 7-step logging format
- Include issue number and title in relevant log messages
- Use commit message format: "Initial plan generated for issue #<number>"
- Exit with sys.exit(1) on any failure
- Add commit and push using existing utility functions
- Copy three prompts to prompts.md exactly as specified
- Update DEVELOPMENT_PROCESS.md link reference

Implement the tests as specified with full workflow mocking.
```
