# Step 6: Comprehensive Testing and Quality Assurance

## LLM Prompt
```
Based on the Code Formatters Implementation Summary, implement Step 6: Create comprehensive test data files, add the formatter_integration pytest marker to pyproject.toml, and run all quality assurance checks (pylint, pytest, mypy) to ensure the TDD-implemented formatter system passes all quality gates.
```

## WHERE
- `pyproject.toml` - Add `formatter_integration` pytest marker (update markers list)
- `tests/formatters/test_data/` - Test data and sample code files for integration tests
- `tests/formatters/conftest.py` - Test fixtures and configuration for TDD tests
- **Note**: Individual test files already created in steps 1-5 using TDD approach

## WHAT
### Test Data Files
```python
# Unformatted Python code samples
# Unsorted import samples  
# Various pyproject.toml configurations
# Edge cases and error conditions
```

### Integration Test Functions (Already Created in Previous Steps)
```python
# These tests were already written in steps 3-5 using TDD approach:
@pytest.mark.formatter_integration
def test_black_formatter_integration():
    """Test Black formatter with real files - stdout parsing"""

@pytest.mark.formatter_integration  
def test_isort_formatter_integration():
    """Test isort formatter with real files - API change detection"""
    
@pytest.mark.formatter_integration
def test_combined_formatting_workflow():
    """Test format_code() with both formatters"""
```

### Quality Assurance Functions
```python
def run_all_quality_checks() -> Dict[str, bool]:
    """Helper to run pylint, pytest, and mypy checks"""
```

## HOW
### Integration Points
- Add pytest marker to pyproject.toml markers list
- Create temporary directories for integration tests
- Use actual formatter execution (not mocked)
- Verify file changes with real before/after comparisons

### Test Structure
```python
# conftest.py - shared fixtures
@pytest.fixture
def temp_project_dir():
    """Create temporary project with sample files"""

@pytest.fixture  
def sample_unformatted_code():
    """Provide unformatted Python code"""
```

## ALGORITHM
### Integration Test Flow
```
1. Create temporary project directory with sample files
2. Copy unformatted Python code and test pyproject.toml
3. Run formatter on temporary project
4. Verify expected changes were made
5. Check that properly formatted code shows no changes
6. Clean up temporary files
```

### Quality Check Flow
```
1. Run pylint with error/fatal categories only
2. Run pytest with all markers (unit + integration)  
3. Run mypy with strict checking
4. Report any failures and fix issues
5. Verify all checks pass before completion
```

## DATA
### Sample Test Files
**Unformatted Python code:**
```python
# Long lines, inconsistent spacing, etc.
def badly_formatted_function(param1,param2,param3):
    x=1+2+3+4+5+6+7+8+9+10+11+12+13+14+15+16+17+18+19+20+21+22
    return x
```

**Unsorted imports:**
```python
import os
from myproject.utils import helper
import sys
from typing import List
import pathlib
from myproject.models import Model
```

**Test pyproject.toml variations:**
- Default configuration
- Custom line lengths
- Different target directories
- Missing tool sections

### pytest Markers Update (pyproject.toml)
```toml
[tool.pytest.ini_options]
markers = [
    "git_integration: tests with file system git operations (repos, commits)", 
    "claude_integration: tests requiring Claude CLI/API (network, auth needed)",
    "formatter_integration: tests that run actual formatters on files"
]
```

## Tasks Required (Final Integration)
1. **Test data creation:**
   - Create sample unformatted Python files for Black testing
   - Create sample files with unsorted imports for isort testing
   - Create various pyproject.toml configurations for config testing
   - Create conftest.py with shared fixtures
   
2. **pytest marker configuration:**
   - Add `formatter_integration` to pyproject.toml markers
   - Verify marker is applied to appropriate tests
   - Test that marker filtering works correctly
   
3. **Quality assurance execution:**
   - Run `mcp__checker__run_pylint_check` - must pass (errors/fatal only)
   - Run `mcp__checker__run_pytest_check` - all tests including integration
   - Run `mcp__checker__run_mypy_check` - strict type checking must pass
   - Fix any issues found by quality checks

4. **Final verification:**
   - Test complete workflow: install → import → use formatters
   - Verify all TDD-created tests pass
   - Confirm all decided features are implemented
   - Document any remaining limitations or future enhancements
