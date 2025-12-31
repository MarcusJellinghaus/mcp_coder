# Step 5: Module Integration and Smoke Tests

## LLM Prompt
```
I'm implementing issue #213 - CI Pipeline Result Analysis Tool. Please refer to pr_info/steps/summary.md for the full architectural overview.

In this final step, complete the module integration:
1. Update module exports in __init__.py
2. Add integration smoke tests to the existing GitHub integration test file
3. Ensure all components work together end-to-end
4. Verify the implementation meets all issue requirements

This step validates that the complete implementation works as intended and integrates properly with the existing codebase.
Follow existing patterns from other GitHub operations managers.
```

## WHERE: File Locations
```
src/mcp_coder/utils/github_operations/__init__.py                    # Modify exports
tests/utils/github_operations/test_github_integration_smoke.py       # Add smoke tests
tests/utils/github_operations/test_ci_results_manager.py             # Final test review
src/mcp_coder/utils/github_operations/ci_results_manager.py          # Final code review
```

## WHAT: Module Integration

### Update __init__.py Exports
```python
# Add to existing exports
from .ci_results_manager import (
    CIResultsManager,
    CIStatusData,
)

# Add to __all__ list
__all__ = [
    # ... existing exports
    "CIResultsManager",
    "CIStatusData",
]
```

### Smoke Test Class
```python
@pytest.mark.github_integration
class TestCIResultsManagerSmoke:
    """Smoke test for CIResultsManager GitHub API integration."""
    
    def test_basic_api_connectivity(self, ci_manager: CIResultsManager, project_dir: Path) -> None
    def test_ci_analysis_workflow(self, ci_manager: CIResultsManager, project_dir: Path) -> None
```

> **Note**: Use `get_default_branch_name(project_dir)` to detect branch dynamically (Decision 21).

## HOW: Integration Points

### Manager Fixture
```python
@pytest.fixture
def ci_manager(
    github_test_setup: "GitHubTestSetup",
) -> Generator[CIResultsManager, None, None]:
    """Create CIResultsManager instance for testing."""
    from tests.conftest import create_github_manager
    
    try:
        manager = create_github_manager(CIResultsManager, github_test_setup)
        yield manager
    except Exception as e:
        pytest.skip(f"Failed to create CIResultsManager: {e}")
```

### Import Verification
```python
# Test that imports work correctly
from mcp_coder.utils.github_operations import (
    CIResultsManager,
    CIStatusData,
)
```

## ALGORITHM: Integration Test Logic

### Basic Connectivity Test
```python
def test_basic_api_connectivity(self, ci_manager):
    # 1. Verify manager can access repository
    # 2. Test get_latest_ci_status with main branch
    # 3. Verify return structure is correct
    # 4. Ensure no exceptions thrown
```

### End-to-End Workflow Test
```python
def test_ci_analysis_workflow(self, ci_manager):
    # 1. Get latest CI status for main/master branch
    # 2. If run exists and has failures, test log retrieval  
    # 3. If run exists, test artifact parsing
    # 4. Verify all methods work together
    # 5. Check data consistency across methods
```

## DATA: Integration Test Cases

### Smoke Test Structure
```python
class TestCIResultsManagerSmoke:
    def test_basic_api_connectivity(self, ci_manager: CIResultsManager, project_dir: Path) -> None:
        """Verify basic GitHub Actions API connectivity."""
        # Get default branch dynamically (Decision 21)
        from mcp_coder.utils.git_operations.branches import get_default_branch_name
        default_branch = get_default_branch_name(project_dir) or "main"
        
        # Test CI status retrieval works
        status = ci_manager.get_latest_ci_status(default_branch)
        assert isinstance(status, dict)
        assert "run" in status
        assert "jobs" in status
        
    def test_ci_analysis_workflow(self, ci_manager: CIResultsManager, project_dir: Path) -> None:
        """Verify complete CI analysis workflow."""
        # Get default branch dynamically (Decision 21)
        from mcp_coder.utils.git_operations.branches import get_default_branch_name
        default_branch = get_default_branch_name(project_dir) or "main"
        
        # Get CI status
        status = ci_manager.get_latest_ci_status(default_branch)
        
        if status["run"]:  # If there are CI runs
            run_id = status["run"]["id"]
            
            # Test log retrieval (returns all logs with job info - Decision 15)
            logs = ci_manager.get_run_logs(run_id)
            assert isinstance(logs, dict)
            assert "logs" in logs
            assert "jobs" in logs
            
            # Test artifact retrieval (may be empty if no artifacts)
            artifacts = ci_manager.get_artifacts(run_id)
            assert isinstance(artifacts, dict)
            
        print(f"[OK] CI analysis workflow tested successfully")
```

### Module Export Verification
```python
def test_module_exports():
    """Verify all expected classes are exported."""
    from mcp_coder.utils.github_operations import (
        CIResultsManager,
        CIStatusData,
    )
    
    # Verify classes exist
    assert CIResultsManager is not None
    assert CIStatusData is not None
```

### Requirements Validation Checklist
```python
# Issue #213 Requirements Check:
# ✅ 1. Fetch latest CI run for a given branch (required parameter)
#     -> get_latest_ci_status(branch) method
# ✅ 2. Determine which jobs passed/failed  
#     -> jobs array in CIStatusData response
# ✅ 3. Retrieve console logs for failed jobs
#     -> get_failed_job_logs(run_id) method
# ✅ 4. Download artifacts for detailed failure information
#     -> get_artifacts(run_id, name_filter) method
#     Note: Parsing (e.g., JUnit XML) is left to consumer

# Integration Requirements Check:
# ✅ Extends BaseGitHubManager
# ✅ Uses existing patterns (TypedDict, decorators, error handling)
# ✅ Exported via module __init__.py
# ✅ Follows existing code patterns
# ✅ Unit tests with mocked APIs
# ✅ Integration tests marked appropriately
```

## Success Criteria
- [ ] Module exports updated and imports work correctly
- [ ] Smoke tests added to existing integration test file
- [ ] All three methods work together in end-to-end scenario
- [ ] Integration tests pass (when GitHub config available)
- [ ] All unit tests pass
- [ ] Code follows existing manager patterns consistently
- [ ] All issue #213 requirements verified and met
- [ ] Manager can be instantiated and used like other GitHub managers

### Final Validation Commands
```bash
# Run all CI results manager tests
pytest tests/utils/github_operations/test_ci_results_manager.py -v

# Run integration tests (requires GitHub config)
pytest tests/utils/github_operations/test_github_integration_smoke.py::TestCIResultsManagerSmoke -v -m github_integration

# Verify imports work
python -c "from mcp_coder.utils.github_operations import CIResultsManager, CIStatusData; print('✅ Imports successful')"
```