# Step 1: Setup Project Structure and Data Models

## LLM Prompt
```
Based on the Code Formatters Implementation Summary, implement Step 1 using TDD: First write comprehensive unit tests for the data models (FormatterResult, FormatterConfig, FileChange), then implement the models to pass the tests. Focus on creating clean, type-safe data structures with simplified change detection using tool output parsing.
```

## WHERE
- `tests/formatters/test_models.py` - **START HERE: Write unit tests first (TDD)**
- `src/mcp_coder/formatters/models.py` - Data structures and types (implement after tests)
- `src/mcp_coder/formatters/__init__.py` - Package initialization (basic exports only)
- `pyproject.toml` - Add `formatter_integration` pytest marker

## WHAT
### Main Functions/Classes
```python
@dataclass
class FormatterConfig:
    """Configuration for a code formatter"""
    
@dataclass  
class FormatterResult:
    """Result of running a formatter"""
    
@dataclass
class FileChange:
    """Simple record of file changes during formatting"""
```

## HOW
### Integration Points
- Add `formatter_integration` marker to pyproject.toml
- Import models in `__init__.py` for public API
- Use subprocess_runner from existing utils

### Dependencies
```python
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Any
from ..utils.subprocess_runner import CommandResult
```

## ALGORITHM
```
1. Define FormatterConfig with tool name, settings dict, target directories
2. Define FileChange with file path and change status (simplified)
3. Define FormatterResult with success flag, changes list, execution time, errors
4. Create type aliases for common patterns
5. Export public API in __init__.py
```

## DATA
### FormatterConfig
- `tool_name: str` - Name of the formatter tool
- `settings: Dict[str, Any]` - Tool-specific configuration
- `target_directories: List[Path]` - Directories to format
- `project_root: Path` - Root directory of project

### FormatterResult  
- `success: bool` - Whether formatting completed successfully
- `files_changed: List[FileChange]` - Files modified (parsed from tool outputs)
- `execution_time_ms: int` - Time taken to complete formatting
- `formatter_name: str` - Name of formatter used ("black" or "isort")
- `error_message: Optional[str]` - Error details if failed
- **Removed:** `command_result` field (not needed with simplified approach)

### FileChange
- `file_path: Path` - Path to the changed file
- `had_changes: bool` - Whether the file was actually modified

## Tests Required (TDD - Write These First!)
1. **FormatterConfig creation and validation**
   - Test with various tool names and settings
   - Test with different target directories
   - Test invalid configurations

2. **FormatterResult scenarios** 
   - Success with file changes
   - Success with no changes
   - Failure with error message
   - Various execution times

3. **FileChange data structure**
   - File path handling
   - Change status tracking
   - Path validation

4. **Data model integration**
   - Test that all models work together
   - Test serialization/deserialization if needed
