# Step 3: Add Template Selection Logic (TDD)

## Context
Reference: `pr_info/steps/summary.md`

This step adds template selection logic based on `executor_os` configuration. Templates added in Step 1 will now be selected dynamically based on the OS configuration. Follows TDD approach.

## Objective
1. Write tests for Windows template selection
2. Update `execute_coordinator_test()` to select template based on OS
3. Update `dispatch_workflow()` to select templates based on OS
4. Ensure correct templates are used for each OS

## WHERE

### Test File
**File**: `tests/cli/commands/test_coordinator.py`

**New tests**: Add to existing test class or create new test class

### Implementation File
**File**: `src/mcp_coder/cli/commands/coordinator.py`

**Functions to modify**:
- `execute_coordinator_test()` (around line 340)
- `dispatch_workflow()` (around line 110)

## WHAT

### Test Functions

#### `test_execute_coordinator_test_windows_template()`
Test that Windows template is used when `executor_os = "windows"`.

**Signature**:
```python
def test_execute_coordinator_test_windows_template(monkeypatch) -> None:
    """Test Windows template is selected for Windows executor."""
```

#### `test_execute_coordinator_test_linux_template()`
Test that Linux template is used when `executor_os = "linux"`.

**Signature**:
```python
def test_execute_coordinator_test_linux_template(monkeypatch) -> None:
    """Test Linux template is selected for Linux executor."""
```

#### `test_dispatch_workflow_windows_templates()`
Test that Windows workflow templates are used when `executor_os = "windows"`.

**Signature**:
```python
def test_dispatch_workflow_windows_templates(monkeypatch) -> None:
    """Test Windows workflow templates are selected for Windows executor."""
```

### Implementation Functions

#### Modified: `execute_coordinator_test()`
Select test template based on `executor_os`.

**Signature**: (unchanged)
```python
def execute_coordinator_test(args: argparse.Namespace) -> int:
```

**Logic Change**: Replace hardcoded `DEFAULT_TEST_COMMAND` with conditional selection.

#### Modified: `dispatch_workflow()`
Select workflow templates based on `executor_os`.

**Signature**: (unchanged)
```python
def dispatch_workflow(
    issue: IssueData,
    workflow_name: str,
    repo_config: dict[str, str],
    jenkins_client: JenkinsClient,
    issue_manager: IssueManager,
    branch_manager: IssueBranchManager,
    log_level: str,
) -> None:
```

**Logic Change**: Replace hardcoded template variables with conditional selection.

## HOW

### Integration Points

**Templates Used**:
- From Step 1: `DEFAULT_TEST_COMMAND_WINDOWS`, `CREATE_PLAN_COMMAND_WINDOWS`, `IMPLEMENT_COMMAND_WINDOWS`, `CREATE_PR_COMMAND_WINDOWS`
- Existing: `DEFAULT_TEST_COMMAND`, `CREATE_PLAN_COMMAND_TEMPLATE`, `IMPLEMENT_COMMAND_TEMPLATE`, `CREATE_PR_COMMAND_TEMPLATE`

**Config Access**: Use `executor_os` from `repo_config` dict

**Selection Pattern**: Simple if-else based on `executor_os` value

## ALGORITHM

### Template Selection in `execute_coordinator_test()`
```
1. Load and validate repo config (existing)
2. Get executor_os from validated_config
3. Select template using dictionary mapping:
   - TEST_COMMAND_TEMPLATES = {"windows": DEFAULT_TEST_COMMAND_WINDOWS, "linux": DEFAULT_TEST_COMMAND}
   - command = TEST_COMMAND_TEMPLATES[executor_os]
4. Continue with existing logic (build params, start job, etc.)
```

### Template Selection in `dispatch_workflow()`
```
1. Determine workflow type (create-plan, implement, create-pr) - existing
2. Get executor_os from repo_config
3. Select appropriate template using dictionary mapping:
   - WORKFLOW_TEMPLATES = {
       "create-plan": {"windows": CREATE_PLAN_COMMAND_WINDOWS, "linux": CREATE_PLAN_COMMAND_TEMPLATE},
       "implement": {"windows": IMPLEMENT_COMMAND_WINDOWS, "linux": IMPLEMENT_COMMAND_TEMPLATE},
       "create-pr": {"windows": CREATE_PR_COMMAND_WINDOWS, "linux": CREATE_PR_COMMAND_TEMPLATE}
     }
   - template = WORKFLOW_TEMPLATES[workflow_config["workflow"]][executor_os]
4. Format template with parameters (existing)
5. Continue with existing logic
```

### Test Algorithm (Using Parametrized Tests)
```
# Parametrized test for template selection
1. Define test parameters: [("windows", WINDOWS_TEMPLATE), ("linux", LINUX_TEMPLATE)]
2. For each (executor_os, expected_template):
   a. Mock repo config with executor_os
   b. Mock Jenkins client to capture command parameter
   c. Call function (execute_coordinator_test or dispatch_workflow)
   d. Assert expected_template was used
```

## DATA

### Template Selection Map

For `execute_coordinator_test()`:
```python
executor_os = "windows" -> DEFAULT_TEST_COMMAND_WINDOWS
executor_os = "linux"   -> DEFAULT_TEST_COMMAND
```

For `dispatch_workflow()`:
```python
# create-plan workflow
("create-plan", "windows") -> CREATE_PLAN_COMMAND_WINDOWS
("create-plan", "linux")   -> CREATE_PLAN_COMMAND_TEMPLATE

# implement workflow
("implement", "windows") -> IMPLEMENT_COMMAND_WINDOWS
("implement", "linux")   -> IMPLEMENT_COMMAND_TEMPLATE

# create-pr workflow
("create-pr", "windows") -> CREATE_PR_COMMAND_WINDOWS
("create-pr", "linux")   -> CREATE_PR_COMMAND_TEMPLATE
```

## Implementation Steps

### Part 1: Write Tests (TDD)

1. Open `tests/cli/commands/test_coordinator.py`

2. Add parametrized test for template selection in `execute_coordinator_test`:
   ```python
   import pytest
   
   @pytest.mark.parametrize("executor_os,expected_template_name", [
       ("windows", "DEFAULT_TEST_COMMAND_WINDOWS"),
       ("linux", "DEFAULT_TEST_COMMAND"),
   ])
   def test_execute_coordinator_test_template_selection(monkeypatch, executor_os, expected_template_name):
       """Test correct template is selected based on executor_os."""
       from mcp_coder.cli.commands.coordinator import (
           execute_coordinator_test,
           DEFAULT_TEST_COMMAND,
           DEFAULT_TEST_COMMAND_WINDOWS,
       )
       import argparse
       
       # Map template names to actual templates
       template_map = {
           "DEFAULT_TEST_COMMAND_WINDOWS": DEFAULT_TEST_COMMAND_WINDOWS,
           "DEFAULT_TEST_COMMAND": DEFAULT_TEST_COMMAND,
       }
       expected_template = template_map[expected_template_name]
       
       # Mock config
       def mock_load_config(repo_name):
           return {
               "repo_url": "https://github.com/test/repo.git",
               "executor_job_path": "Tests/test",  # RENAMED field
               "github_credentials_id": "cred-id",
               "executor_os": executor_os,
           }
       
       # Mock validation (no-op)
       def mock_validate(repo_name, config):
           pass
       
       # Capture Jenkins start_job params
       captured_params = {}
       
       class MockJenkinsClient:
           def __init__(self, *args, **kwargs):
               pass
           
           def start_job(self, job_path, params):
               captured_params.update(params)
               return 12345
           
           def get_job_status(self, queue_id):
               from mcp_coder.utils.jenkins_operations.models import JobStatus
               return JobStatus(queue_id=queue_id, status="queued", url=None)
       
       # Mock Jenkins credentials
       def mock_get_creds():
           return ("http://jenkins.example.com", "user", "token")
       
       monkeypatch.setattr(
           "mcp_coder.cli.commands.coordinator.load_repo_config",
           mock_load_config
       )
       monkeypatch.setattr(
           "mcp_coder.cli.commands.coordinator.validate_repo_config",
           mock_validate
       )
       monkeypatch.setattr(
           "mcp_coder.cli.commands.coordinator.JenkinsClient",
           MockJenkinsClient
       )
       monkeypatch.setattr(
           "mcp_coder.cli.commands.coordinator.get_jenkins_credentials",
           mock_get_creds
       )
       monkeypatch.setattr(
           "mcp_coder.cli.commands.coordinator.create_default_config",
           lambda: False
       )
       
       # Execute
       args = argparse.Namespace(repo_name="test_repo", branch_name="main")
       execute_coordinator_test(args)
       
       # Assert correct template was used
       assert captured_params["COMMAND"] == expected_template
   ```

3. Run tests (should fail):
   ```bash
   mcp__code-checker__run_pytest_check(
       extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration", "-k", "test_execute_coordinator_test_template_selection"]
   )
   ```

### Part 2: Implement Functionality

4. Open `src/mcp_coder/cli/commands/coordinator.py`

5. Add template mapping dictionary at module level (after template constants, before functions):
   ```python
   # Template selection mapping for execute_coordinator_test
   TEST_COMMAND_TEMPLATES = {
       "windows": DEFAULT_TEST_COMMAND_WINDOWS,
       "linux": DEFAULT_TEST_COMMAND,
   }
   ```

6. Update `execute_coordinator_test()` - find this section (around line 370):
   ```python
   # Build job parameters
   params = {
       "REPO_URL": validated_config["repo_url"],
       "BRANCH_NAME": args.branch_name,
       "COMMAND": DEFAULT_TEST_COMMAND,  # OLD: Hardcoded
       "EXECUTOR_TEST_PATH": validated_config["executor_test_path"],  # OLD field name
       "GITHUB_CREDENTIALS_ID": validated_config["github_credentials_id"],
   }
   ```
   
   Replace with:
   ```python
   # Select template based on OS using dictionary mapping
   executor_os = validated_config["executor_os"]
   test_command = TEST_COMMAND_TEMPLATES[executor_os]
   
   # Build job parameters
   params = {
       "REPO_URL": validated_config["repo_url"],
       "BRANCH_NAME": args.branch_name,
       "COMMAND": test_command,  # NEW: OS-aware selection
       "EXECUTOR_JOB_PATH": validated_config["executor_job_path"],  # RENAMED parameter and field
       "GITHUB_CREDENTIALS_ID": validated_config["github_credentials_id"],
   }
   ```

7. Add workflow template mapping dictionary at module level (after TEST_COMMAND_TEMPLATES):
   ```python
   # Template selection mapping for dispatch_workflow
   WORKFLOW_TEMPLATES = {
       "create-plan": {
           "windows": CREATE_PLAN_COMMAND_WINDOWS,
           "linux": CREATE_PLAN_COMMAND_TEMPLATE,
       },
       "implement": {
           "windows": IMPLEMENT_COMMAND_WINDOWS,
           "linux": IMPLEMENT_COMMAND_TEMPLATE,
       },
       "create-pr": {
           "windows": CREATE_PR_COMMAND_WINDOWS,
           "linux": CREATE_PR_COMMAND_TEMPLATE,
       },
   }
   ```

8. Update `dispatch_workflow()` - find this section (around line 160):
   ```python
   # Step 3: Select appropriate command template and build command
   if workflow_config["workflow"] == "create-plan":
       command = CREATE_PLAN_COMMAND_TEMPLATE.format(
           log_level=log_level, issue_number=issue["number"]
       )
   elif workflow_config["workflow"] == "implement":
       command = IMPLEMENT_COMMAND_TEMPLATE.format(
           log_level=log_level, branch_name=branch_name
       )
   else:  # create-pr
       command = CREATE_PR_COMMAND_TEMPLATE.format(
           log_level=log_level, branch_name=branch_name
       )
   ```
   
   Replace with:
   ```python
   # Step 3: Select appropriate command template based on workflow and OS using dictionary mapping
   executor_os = repo_config.get("executor_os", "linux")
   workflow_name = workflow_config["workflow"]
   template = WORKFLOW_TEMPLATES[workflow_name][executor_os]
   
   if workflow_name == "create-plan":
       command = template.format(log_level=log_level, issue_number=issue["number"])
   elif workflow_name == "implement":
       command = template.format(log_level=log_level, branch_name=branch_name)
   else:  # create-pr
       command = template.format(log_level=log_level, branch_name=branch_name)
   ```

9. Run tests again (should pass):
   ```bash
   mcp__code-checker__run_pytest_check(
       extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
   )
   ```

10. Run all code quality checks:
    ```bash
    mcp__code-checker__run_all_checks(
        extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
    )
    ```

## Testing

### Test Cases

1. **Windows test template**: Verify `DEFAULT_TEST_COMMAND_WINDOWS` used when `executor_os = "windows"`
2. **Linux test template**: Verify `DEFAULT_TEST_COMMAND` used when `executor_os = "linux"`
3. **Windows workflow templates**: Verify Windows templates used for all three workflows
4. **Linux workflow templates**: Verify Linux templates used for all three workflows (existing behavior)

### Expected Results

- Tests should fail initially (TDD approach)
- Tests should pass after implementation
- All pylint, pytest, mypy checks should pass
- Windows templates used when configured
- Linux templates used by default (backward compatible)

## LLM Prompt for Implementation

```
I need to implement Step 3 of the Windows support implementation using TDD.

Context:
- Read pr_info/steps/summary.md for overall architecture
- Read pr_info/steps/step_3.md for detailed requirements
- Windows templates were added in Step 1
- Config loading was updated in Step 2

Task:
Follow TDD approach to add template selection logic:

Part 1 - Write Tests First:
1. Add test_execute_coordinator_test_windows_template to tests/cli/commands/test_coordinator.py
2. Add test_execute_coordinator_test_linux_template
3. Run tests (should fail) using mcp__code-checker__run_pytest_check

Part 2 - Implement Functionality:
4. Update execute_coordinator_test() in src/mcp_coder/cli/commands/coordinator.py to select template based on executor_os
5. Update dispatch_workflow() to select workflow templates based on executor_os
6. Run tests again (should pass)
7. Run all quality checks using mcp__code-checker__run_all_checks

Requirements:
- Use simple if-else for template selection (KISS principle)
- Default to Linux templates for backward compatibility
- Support all three workflows: create-plan, implement, create-pr
- All quality checks must pass

After implementation:
- Report test results
- Fix any issues found
```
