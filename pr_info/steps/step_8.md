# Step 8: Integration Testing and Documentation

## LLM Prompt
```
You are implementing Step 8 (final step) of the execution-dir feature.

Reference documents:
- Summary: pr_info/steps/summary.md
- Previous steps: pr_info/steps/step_1.md through step_7.md (completed)
- This step: pr_info/steps/step_8.md

Task: Create integration tests and update documentation to complete the feature.

Follow Test-Driven Development:
1. Read this step document completely
2. Create integration tests
3. Update documentation files
4. Verify complete feature works end-to-end

Apply KISS principle - focus on real-world usage scenarios.
```

## Objective
Create integration tests demonstrating the separation of execution and project directories, and update all relevant documentation.

## WHERE
**New test file:**
- File: `tests/integration/test_execution_dir_integration.py` (new)

**Documentation files:**
- File: `docs/architecture/ARCHITECTURE.md`
- File: `.claude/CLAUDE.md`
- File: `README.md` (if CLI examples exist)

## WHAT

### Integration Tests

**Create comprehensive end-to-end tests:**
```python
"""Integration tests for execution-dir feature.

Tests the complete flow from CLI to subprocess execution,
verifying separation of project and execution directories.
"""

class TestExecutionDirIntegration:
    """End-to-end tests for --execution-dir flag."""
    
    def test_prompt_command_with_separate_directories(self, tmp_path):
        """Test prompt command with different project and execution dirs."""
        
    def test_implement_workflow_with_execution_dir(self, tmp_path, mock_git_repo):
        """Test implement workflow uses correct execution context."""
        
    def test_create_plan_with_workspace_config(self, tmp_path):
        """Test create-plan can access workspace MCP config."""
        
    def test_execution_dir_affects_config_discovery(self, tmp_path):
        """Test that execution_dir determines where .mcp.json is found."""
        
    def test_project_dir_for_git_operations(self, tmp_path, mock_git_repo):
        """Verify project_dir still controls git operations."""
        
    def test_relative_execution_dir_resolution(self, tmp_path):
        """Test relative execution_dir resolves to shell CWD."""
```

### Real-World Usage Scenarios

**Scenario 1: Workspace with Multiple Projects**
```python
def test_workspace_with_multiple_projects(self, tmp_path):
    """
    User has:
    /home/user/workspace/.mcp.json  (shared config)
    /home/user/projects/app1/       (project A)
    /home/user/projects/app2/       (project B)
    
    Want: Use workspace config while working on projects
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".mcp.json").write_text('{"mcpServers": {...}}')
    
    project1 = tmp_path / "projects" / "app1"
    project1.mkdir(parents=True)
    
    # Simulate: cd /home/user/workspace && mcp-coder implement --project-dir /projects/app1
    # execution_dir = workspace (implicit CWD)
    # project_dir = app1
```

**Scenario 2: CI/CD Environment**
```python
def test_cicd_with_checkout_directory(self, tmp_path):
    """
    CI/CD setup:
    /ci/workspace/           (execution context, has configs)
    /ci/checkout/project/    (checked out code)
    
    Want: Run in workspace, operate on checkout
    """
```

## HOW

### Integration Test Strategy

1. **Setup test environments:**
   ```python
   @pytest.fixture
   def workspace_setup(tmp_path):
       """Create workspace with MCP config."""
       workspace = tmp_path / "workspace"
       workspace.mkdir()
       
       project = tmp_path / "project"
       project.mkdir()
       
       return {"workspace": workspace, "project": project}
   ```

2. **Mock subprocess execution:**
   ```python
   def test_subprocess_cwd_is_execution_dir(self, workspace_setup, monkeypatch):
       """Verify subprocess uses execution_dir as cwd."""
       captured_cwd = None
       
       def mock_subprocess(*args, **kwargs):
           nonlocal captured_cwd
           captured_cwd = kwargs.get('cwd')
           return MockResult(...)
       
       monkeypatch.setattr(subprocess, 'run', mock_subprocess)
       # ... run command ...
       assert captured_cwd == str(workspace_setup["workspace"])
   ```

3. **Test environment variables:**
   ```python
   def test_env_vars_use_project_dir(self, workspace_setup, monkeypatch):
       """Verify MCP_CODER_PROJECT_DIR uses project_dir."""
       captured_env = None
       
       def mock_subprocess(*args, **kwargs):
           nonlocal captured_env
           captured_env = kwargs.get('env')
           return MockResult(...)
       
       # ... run command ...
       assert captured_env['MCP_CODER_PROJECT_DIR'] == str(workspace_setup["project"])
   ```

## ALGORITHM

```
FOR EACH integration_test_scenario:
    SETUP:
        Create workspace directory
        Create project directory
        Create MCP config in workspace
        
    EXECUTE:
        Run command with:
            --project-dir = project
            --execution-dir = workspace
            
    VERIFY:
        Subprocess cwd = workspace
        MCP_CODER_PROJECT_DIR = project
        Git operations target project
        Config discovery uses workspace
```

## DATA

### Test Data Structures

**Workspace Setup:**
```python
workspace_layout = {
    "workspace": {
        ".mcp.json": {"mcpServers": {...}},
        "templates/": ["plan.md", "pr.md"],
    },
    "project": {
        "src/": ["main.py", "utils.py"],
        ".git/": "...",
        "pyproject.toml": "...",
    }
}
```

**Expected Behavior:**
```python
expected_behavior = {
    "subprocess_cwd": workspace_path,
    "env_vars": {
        "MCP_CODER_PROJECT_DIR": project_path,
        "MCP_CODER_VENV_DIR": venv_path,
    },
    "git_operations": project_path,
    "config_discovery": workspace_path,
}
```

## Test Requirements

### Integration Test Cases
1. **Separate directories work correctly** → Both paths used appropriately
2. **Config discovery in execution_dir** → .mcp.json found in workspace
3. **Git operations in project_dir** → Commits happen in project
4. **Environment variables correct** → MCP_CODER_PROJECT_DIR set
5. **Relative paths resolve correctly** → Relative to shell CWD
6. **Default behavior (no --execution-dir)** → Uses CWD as expected
7. **CLI argument parsing** → All commands accept flag
8. **Error handling** → Invalid paths handled gracefully

### Documentation Test Cases
1. **Architecture doc accuracy** → Reflects implementation
2. **Usage examples work** → Can copy-paste and run
3. **CLAUDE.md guidelines updated** → AI understands feature
4. **Help text clarity** → Users understand flag purpose

## Implementation Notes

### KISS Principles Applied
- Focus on real usage scenarios
- Simple, clear test names
- Comprehensive but not exhaustive
- Document actual behavior, not aspirations

### Why These Tests
1. **Real-World Validation**: Tests actual use cases
2. **Regression Prevention**: Catches future breakage
3. **Documentation**: Tests serve as examples
4. **Confidence**: Proves feature works end-to-end

### Integration Test Markers
```python
import pytest

@pytest.mark.integration
@pytest.mark.execution_dir
class TestExecutionDirIntegration:
    """Mark tests appropriately for test selection."""
```

## Documentation Updates

### ARCHITECTURE.md Updates

**Add to "Solution Strategy" section:**
```markdown
### Execution Context Management

**Design Decision:** Separate execution directory from project directory

mcp-coder distinguishes between:
- **Project Directory** (`project_dir`): Where source files live and git operations occur
- **Execution Directory** (`execution_dir`): Where Claude subprocess runs

**Implementation:**
- CLI flag: `--execution-dir` controls Claude's working directory
- Default: Uses shell's current working directory
- Use case: Access workspace configs while modifying different projects

**Example:**
```bash
cd /home/user/workspace  # Has .mcp.json
mcp-coder implement --project-dir /path/to/project
# Claude runs in workspace, modifies project files
```
```

**Add to "Runtime View" section:**
```markdown
### Scenario: Separate Execution and Project Contexts
1. User has workspace with shared MCP configurations
2. Runs `mcp-coder implement --project-dir /project --execution-dir /workspace`
3. mcp_coder prepares environment:
   - Sets `MCP_CODER_PROJECT_DIR=/project`
   - Executes Claude with `cwd=/workspace`
4. Claude discovers `.mcp.json` in workspace
5. Claude modifies files in project directory
6. Git operations target project directory
```

### CLAUDE.md Updates

**Add to usage guidelines:**
```markdown
## Execution Directory Flag

When working with mcp-coder, you may encounter `--execution-dir`:

**Purpose:** Controls where Claude subprocess executes (separate from project location)

**Usage:**
- Default: Uses shell's current working directory
- Explicit: `--execution-dir /path/to/execution/context`
- Relative: `--execution-dir ./subdir` (resolves to CWD)

**Common Scenario:**
User has workspace with `.mcp.json` config, wants to work on separate project:
```bash
cd /home/user/workspace
mcp-coder implement --project-dir /path/to/project
# Claude runs in workspace, modifies project
```

**When Implementing:**
- Respect both `project_dir` and `execution_dir` parameters
- Use `project_dir` for file operations and git
- Use `execution_dir` for config discovery
- Never conflate the two concepts
```

### README.md Updates (if applicable)

Add example to CLI section:
```markdown
## Advanced Usage

### Working with Separate Execution Context

Control where Claude executes independently from project location:

```bash
# Claude runs in current directory (default)
mcp-coder implement --project-dir /path/to/project

# Claude runs in specific directory
mcp-coder implement --project-dir /project --execution-dir /workspace
```

**Use Case:** Keep MCP configurations in workspace while working on multiple projects.
```

## Verification Steps

### Pre-Release Checklist
1. **All integration tests pass:**
   ```bash
   pytest tests/integration/test_execution_dir_integration.py -v
   ```

2. **All unit tests still pass:**
   ```bash
   pytest tests/ -v
   ```

3. **Documentation builds without errors:**
   ```bash
   # If using docs builder
   make docs
   ```

4. **Manual testing:**
   ```bash
   # Test each command with --execution-dir
   mcp-coder prompt "test" --execution-dir /tmp
   mcp-coder implement --project-dir . --execution-dir /tmp
   # etc.
   ```

5. **Quality checks:**
   ```bash
   mypy src/mcp_coder/
   pylint src/mcp_coder/
   ```

6. **Help text verification:**
   ```bash
   mcp-coder prompt --help | grep execution-dir
   mcp-coder implement --help | grep execution-dir
   ```

## Dependencies
- Depends on: Steps 1-7 (all previous implementation)
- Completes: Feature implementation

## Estimated Complexity
- Integration test lines: ~300 lines
- Documentation updates: ~150 lines
- Complexity: Medium (comprehensive testing + docs)

## Success Criteria

### Feature Complete When:
- [ ] All integration tests pass
- [ ] All existing tests still pass
- [ ] Documentation updated and accurate
- [ ] Manual testing scenarios work
- [ ] Help text shows flag correctly
- [ ] Quality checks pass (mypy, pylint)
- [ ] Real-world use cases validated
- [ ] No breaking changes to existing usage

### Quality Metrics:
- Test coverage: >90% for new code
- Documentation: Clear examples for users
- Performance: No regression in execution time
- Usability: Flag works intuitively

## Example Integration Test

```python
def test_complete_workflow_separation(self, tmp_path):
    """Test complete workflow with separated directories.
    
    Scenario: User has workspace with configs and templates,
    wants to implement features in a separate project.
    """
    # Setup
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".mcp.json").write_text('{"mcpServers": {...}}')
    (workspace / "templates").mkdir()
    
    project = tmp_path / "project"
    project.mkdir()
    (project / "src").mkdir()
    init_git_repo(project)
    
    # Execute
    args = create_args(
        command="implement",
        project_dir=str(project),
        execution_dir=str(workspace),
    )
    
    result = execute_implement(args)
    
    # Verify
    assert result == 0
    assert captured_subprocess_cwd == str(workspace)
    assert captured_env["MCP_CODER_PROJECT_DIR"] == str(project)
    assert git_repo_location == str(project)
```

## Final Notes

This step completes the feature implementation. After this step:
- Users can control execution context independently
- Documentation reflects the new capability
- Integration tests validate real-world usage
- Code quality standards maintained
- Feature is production-ready
