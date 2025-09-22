# Step 6: Comprehensive Testing and Quality Assurance

## LLM Prompt
```
Based on the Code Formatters Implementation Summary, implement Step 6: Create comprehensive tests for all formatter functionality, add the formatter_integration pytest marker, and ensure all code quality checks pass. This includes creating test data files and integration tests.
```

## WHERE
- `pyproject.toml` - Add `formatter_integration` pytest marker
- `tests/formatters/` - All test files (created in previous steps)
- `tests/formatters/test_data/` - Test data and sample code files
- `tests/formatters/conftest.py` - Test fixtures and configuration

## WHAT
### Test Data Files
```python
# Unformatted Python code samples
# Unsorted import samples  
# Various pyproject.toml configurations
# Edge cases and error conditions
```

### Integration Test Functions
```python
@pytest.mark.formatter_integration
def test_black_formatter_integration():
    """Test Black formatter with real files"""

@pytest.mark.formatter_integration  
def test_isort_formatter_integration():
    """Test isort formatter with real files"""
    
@pytest.mark.formatter_integration
def test_combined_formatting_workflow():
    """Test running both formatters together"""
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

### pytest Markers Update
```toml
markers = [
    "git_integration: tests with file system git operations (repos, commits)", 
    "claude_integration: tests requiring Claude CLI/API (network, auth needed)",
    "formatter_integration: tests that run actual formatters on files"
]
```

## Tests Required
1. **Integration tests with formatter_integration marker:**
   - Test Black formatting of badly formatted code
   - Test isort sorting of mixed import styles
   - Test both formatters on same project
   - Test with custom configuration from pyproject.toml
   - Test with missing target directories
   - Test performance with larger codebases
   
2. **Error handling and edge cases:**
   - Test with syntax errors in Python files
   - Test with binary files in target directories
   - Test with missing pyproject.toml
   - Test with malformed pyproject.toml
   - Test with read-only files
   - Test with symlinks and special files
   
3. **Quality assurance verification:**
   - All pylint checks pass (errors/fatal only)
   - All pytest markers run successfully:
     - Unit tests: `pytest -m "not git_integration and not claude_integration and not formatter_integration"`
     - Formatter tests: `pytest -m "formatter_integration"`  
     - Integration tests: `pytest -m "git_integration or claude_integration"`
   - All mypy type checking passes
   - Test coverage meets requirements

4. **Documentation and examples:**
   - Add docstring examples for main API functions
   - Verify all public functions have proper type hints
   - Test that imports work as documented
