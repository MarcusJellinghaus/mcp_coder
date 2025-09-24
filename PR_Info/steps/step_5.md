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

## Tasks Required (Final Integration - 6 Tests + QA)
1. **End-to-end workflow tests (3 tests)**
   - Complete formatting: Test unformatted code + unsorted imports → both formatted
   - Idempotent behavior: Format same files twice, verify no changes on second run
   - Error resilience: Test mixed scenarios (one file succeeds, one fails)

2. **Analysis scenario validation (2 tests)**
   - Step 0 code samples: Use actual problematic code from analysis findings
   - Configuration conflicts: Test real pyproject.toml scenarios from analysis

3. **Quality gates validation (1 test)**
   - Tool integration: Verify all 30 tests pass, quality checks (pylint/mypy) pass

4. **Quality assurance execution:**
   - Run `checker on p MCP Coder:run_pylint_check` - should pass with clean codebase
   - Run `checker on p MCP Coder:run_pytest_check` - all 30 TDD tests pass
   - Run `checker on p MCP Coder:run_mypy_check` - strict typing validation
   - Address any issues (should be minimal with proven patterns)
