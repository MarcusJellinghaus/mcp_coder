# Step 0: Black and isort Formatter Analysis

## LLM Prompt
```
Before implementing the formatters, analyze Black and isort behavior by running them manually on sample code. Create analysis scripts to examine their stdout/stderr patterns, exit codes, and command-line behavior. Document findings to inform the implementation in subsequent steps.
```

## WHERE
- `analysis/formatter_analysis.py` - Main analysis script  
- `analysis/sample_code.py` - Test code samples for analysis
- `analysis/findings.md` - Document all findings
- **Update subsequent steps** with concrete implementation details based on findings

## WHAT
### Analysis Script Functions
```python
def analyze_black_behavior():
    """Test Black with various scenarios and document outputs"""
    
def analyze_isort_behavior():
    """Test isort CLI to understand change detection patterns"""
    
def test_configuration_reading():
    """Test how tools read pyproject.toml configurations"""
    
def document_findings():
    """Create comprehensive findings document for implementation"""
```

### Key Analysis Areas
1. **Black stdout/stderr patterns** - Exact format of "reformatted" messages
2. **isort CLI output patterns** - How isort reports changes via CLI
3. **Configuration precedence** - How pyproject.toml settings are applied
4. **Exit codes and error handling** - Tool behavior in error scenarios
5. **File filtering behavior** - How tools handle exclusions and .gitignore

## HOW
### Dependencies
```python
import subprocess
import tempfile
from pathlib import Path
import tomllib
```

### Test Scenarios
```python
# Sample unformatted code
UNFORMATTED_CODE = '''
def test(a,b,c):
    x=1+2+3+4+5+6+7+8+9+10+11+12+13+14+15+16+17+18+19+20+21+22+23+24+25
    return x
'''

# Sample unsorted imports  
UNSORTED_IMPORTS = '''
import os
from myproject import utils
import sys
from typing import List
'''

# Sample pyproject.toml configurations
TEST_CONFIG = '''
[tool.black]
line-length = 100
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 88
'''
```

## ALGORITHM
```
1. Create temporary files with test code samples
2. Run Black CLI with different scenarios:
   - Unformatted code (expect "reformatted" message)
   - Already formatted code (expect no output) 
   - Syntax errors (expect error in stderr)
   - Multiple files (expect multiple messages)
3. Run isort CLI with different scenarios:
   - Unsorted imports (expect change messages)
   - Already sorted imports (expect no output)
   - Various configuration options
4. Test configuration reading:
   - Create test pyproject.toml files
   - Verify how tools parse and apply settings
5. Document exact patterns, exit codes, and behaviors
6. Create parsing strategies for implementation
```

## FINDINGS TO DOCUMENT

### Black CLI Behavior
- **Stdout patterns:** Exact format of success messages
  - "reformatted {filename}" for changed files
  - Output format for multiple files
  - Behavior with no changes
- **Exit codes:** 0 (success), other codes for various scenarios
- **Error handling:** How syntax errors appear in stderr
- **Configuration:** How pyproject.toml settings map to behavior

### isort CLI Behavior  
- **Stdout patterns:** How isort reports changes via CLI
- **Exit codes:** Success/failure scenarios
- **Configuration:** How pyproject.toml settings are applied
- **Change detection:** Most reliable way to detect if files changed

### Configuration Integration
- **TOML parsing:** Reliable patterns for reading pyproject.toml
- **Default values:** What happens when sections are missing
- **Line-length conflicts:** How to detect and warn about mismatches

## DELIVERABLES
1. **`analysis/findings.md`** - Comprehensive behavior documentation
2. **Updated implementation strategy** - Concrete parsing patterns
3. **Test scenario examples** - Real-world patterns for testing
4. **Configuration examples** - Working pyproject.toml samples

## SUCCESS CRITERIA
- Understand exact stdout parsing patterns for both tools
- Know reliable change detection methods
- Have concrete implementation approach for each formatter
- Eliminated guesswork about tool behavior

## IMPACT ON SUBSEQUENT STEPS
This analysis will provide:
- **Exact regex patterns** for parsing tool output
- **Reliable change detection** strategy for each tool
- **Error handling patterns** based on actual tool behavior
- **Configuration reading** approach with real examples
- **Test scenarios** based on actual tool edge cases
