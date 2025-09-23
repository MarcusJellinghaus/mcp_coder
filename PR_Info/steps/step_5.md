# Step 5: Integration Testing and Quality Assurance

## LLM Prompt
```
Based on the complete formatter implementation from Steps 0-4, implement Step 5: Create comprehensive integration test scenarios with realistic test data, run all quality assurance checks (pylint, pytest, mypy), and ensure the TDD-implemented formatter system passes all quality gates.
```

## WHERE
- `tests/formatters/test_integration.py` - **START HERE: Comprehensive integration tests**
- `tests/formatters/conftest.py` - Test fixtures and configuration for all formatter tests
- **Update:** All existing test files created in steps 1-4 using TDD approach

## WHAT
### Integration Test Functions
```python
# These test the complete workflow built in previous steps:
@pytest.mark.formatter_integration
def test_complete_formatting_workflow():
    """Test full Black + isort formatting on realistic code samples"""

@pytest.mark.formatter_integration  
def test_real_world_scenarios():
    """Test formatters with complex, realistic Python projects"""
    
@pytest.mark.formatter_integration
def test_error_handling_scenarios():
    """Test various error conditions with real files"""
```

### Quality Assurance Functions
```python
def run_all_quality_checks() -> Dict[str, bool]:
    """Helper to run pylint, pytest, and mypy checks"""
```

## HOW
### Integration Points
- Use actual formatter execution (not mocked) for integration tests
- Create temporary directories for test isolation
- Verify real before/after file changes
- Test complete import chain from package root

### Test Dependencies
```python
import tempfile
import pytest
from pathlib import Path
from mcp_coder.formatters import format_code, format_with_black, format_with_isort
```

## ALGORITHM
### Integration Test Flow
```
1. Create temporary project directory with realistic sample files
2. Copy unformatted Python code and test pyproject.toml configurations
3. Run formatter functions on temporary project
4. Verify expected changes were made using actual file content
5. Check that properly formatted code shows no changes (idempotent)
6. Clean up temporary files
```

### Quality Check Flow
```
1. Run pylint with error/fatal categories only (using MCP checker)
2. Run pytest with all markers (unit + integration) (using MCP checker)
3. Run mypy with strict checking (using MCP checker)
4. Report any failures and provide guidance for fixes
5. Verify all checks pass before completion
```

## DATA
### Sample Test Files (Multiline Strings in Tests)
**Unformatted Python code:**
```python
UNFORMATTED_CODE = '''
def badly_formatted_function(param1,param2,param3):
    x=1+2+3+4+5+6+7+8+9+10+11+12+13+14+15+16+17+18+19+20+21+22+23+24
    if x>100:return True
    else:return False
'''
```

**Unsorted imports:**
```python
UNSORTED_IMPORTS = '''
import os
from myproject.utils import helper
import sys
from typing import List, Dict
import pathlib
from myproject.models import Model, User
import json
'''
```

**Test pyproject.toml variations:**
- Default configuration
- Custom line lengths  
- Line-length conflicts
- Missing tool sections

## Tasks Required (Final Integration)
1. **Integration test creation:**
   - Create comprehensive test scenarios using multiline string test data
   - Test complete workflow: install → import → use formatters
   - Test real-world scenarios with complex code samples
   - Test error handling with actual malformed files
   
2. **Test fixtures and configuration:**
   - Create conftest.py with shared fixtures for temp directories
   - Test data factory functions for various code samples
   - Setup/teardown for integration test isolation
   
3. **Quality assurance execution:**
   - Run `mcp__checker__run_pylint_check` - must pass (errors/fatal only)
   - Run `mcp__checker__run_pytest_check` - all tests including integration
   - Run `mcp__checker__run_mypy_check` - strict type checking must pass
   - Fix any issues found by quality checks

4. **Final verification:**
   - Test import statements work correctly from package root
   - Verify all TDD-created tests from Steps 1-4 pass
   - Confirm all decided features are implemented
   - Test line-length conflict warning functionality
   - Document any remaining limitations or future enhancements
   
5. **Real-world testing:**
   - Test on actual unformatted Python files
   - Verify idempotent behavior (formatting twice gives same result)
   - Test with various pyproject.toml configurations
   - Test target directory handling edge cases
