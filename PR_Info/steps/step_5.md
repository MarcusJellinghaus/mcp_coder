# Step 5: Integration Testing and Quality Assurance

## LLM Prompt
```
Based on the complete formatter implementation from Steps 0-4 using analysis-proven patterns, implement Step 5: Create comprehensive integration test scenarios using real code samples from Step 0 analysis, run all quality assurance checks (pylint, pytest, mypy), and ensure the TDD-implemented formatter system with exit code detection passes all quality gates.
```

## WHERE
- `tests/formatters/test_integration.py` - **START HERE: Comprehensive integration tests**
- `tests/formatters/conftest.py` - Test fixtures and configuration for all formatter tests
- **Update:** All existing test files created in steps 1-4 using TDD approach

## WHAT
### Integration Test Functions
```python
# These test the complete workflow using analysis findings:
@pytest.mark.formatter_integration
def test_complete_formatting_workflow_with_exit_codes():
    """Test full Black + isort formatting using exit code patterns from analysis"""

@pytest.mark.formatter_integration  
def test_analysis_based_scenarios():
    """Test formatters with code samples discovered in Step 0 analysis"""
    
@pytest.mark.formatter_integration
def test_exit_code_error_scenarios():
    """Test error conditions using documented exit code patterns"""
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
- Verify exit code patterns from Step 0 analysis
- Test complete import chain from package root

### Test Dependencies
```python
import tempfile
import pytest
from pathlib import Path
from mcp_coder.formatters import format_code, format_with_black, format_with_isort
```

## ALGORITHM
### Integration Test Flow (Analysis-Based)
```
1. Create temporary project directory with code samples from Step 0 analysis
2. Create test pyproject.toml with configurations tested in analysis
3. Run formatter functions and verify exit code patterns (0, 1, 123+)
4. Test that unformatted code triggers exit 1 → formatting → success
5. Test that formatted code triggers exit 0 → no changes
6. Test that syntax errors trigger exit 123+ → error handling
7. Verify idempotent behavior using exit code detection
8. Clean up temporary files
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
### Sample Test Files (From Step 0 Analysis)
**Unformatted Python code (analysis sample):**
```python
UNFORMATTED_CODE = '''
def test(a,b,c):
    x=1+2+3+4+5+6+7+8+9+10+11+12+13+14+15+16+17+18+19+20+21+22+23+24+25
    return x

class MyClass:
    def __init__(self,name,age):
        self.name=name
        self.age=age
'''
```

**Unsorted imports (analysis sample):**
```python
UNSORTED_IMPORTS = '''
import os
from myproject import utils
import sys
from typing import List
from collections import defaultdict
import json
'''
```

**Syntax error sample (for exit code 123 testing):**
```python
SYNTAX_ERROR_CODE = '''
def test(a,b,c):
    x = 1 +
    return x
'''
```

**Test pyproject.toml variations:**
- Default configuration
- Custom line lengths  
- Line-length conflicts (Black vs isort)
- Missing tool sections

## Tasks Required (Final Integration)
1. **Integration test creation using analysis patterns:**
   - Create comprehensive test scenarios using code samples from Step 0
   - Test complete workflow with exit code detection patterns
   - Test real-world scenarios with analysis-documented problematic code
   - Test error handling using known exit code patterns (123+ scenarios)
   
2. **Test fixtures and configuration:**
   - Create conftest.py with shared fixtures for temp directories
   - Test data factory functions using analysis code samples
   - Setup/teardown for integration test isolation
   - Fixtures for pyproject.toml configurations tested in analysis
   
3. **Quality assurance execution (analysis-confident):**
   - Run `mcp__checker__run_pylint_check` - should pass with simple codebase
   - Run `mcp__checker__run_pytest_check` - all TDD tests + integration
   - Run `mcp__checker__run_mypy_check` - strict typing on minimal codebase
   - Address any issues (should be minimal with proven patterns)

4. **Final verification using analysis insights:**
   - Test import statements work correctly from package root
   - Verify all TDD-created tests from Steps 1-4 pass
   - Confirm exit code patterns work as documented in analysis
   - Test line-length conflict warning with analysis scenarios
   - Verify implementation matches analysis findings
   
5. **Real-world testing with analysis scenarios:**
   - Test with unformatted code samples from Step 0
   - Verify idempotent behavior using exit code detection (format twice = same result)
   - Test with various pyproject.toml configurations from analysis
   - Test error scenarios documented in Step 0 findings
   - Confirm all exit code patterns work as analyzed
   
6. **Documentation and completion:**
   - Document implementation matches Step 0 analysis findings
   - Record any deviations from analysis (should be minimal)
   - Verify ultra-simplified architecture (~135 lines achieved)
   - Confirm 75% complexity reduction vs original plan
