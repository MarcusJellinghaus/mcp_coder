# Step 1: Setup Project Structure and Data Models

## LLM Prompt
```
Based on the Code Formatters Implementation Summary, implement Step 1: Create the basic project structure and data models for the formatters module. Focus on creating clean, type-safe data structures that will support the formatting workflow.
```

## WHERE
- `src/mcp_coder/formatters/__init__.py` - Package initialization and main API
- `src/mcp_coder/formatters/models.py` - Data structures and types
- `tests/formatters/test_models.py` - Unit tests for data models
- `pyproject.toml` - Add new pytest marker

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
    """Details about changes made to a file"""
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
2. Define FileChange with file path, before content, after content, diff
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
- `files_changed: List[FileChange]` - List of files that were modified
- `execution_time_ms: int` - Time taken to complete formatting
- `error_message: Optional[str]` - Error details if failed
- `formatter_name: str` - Name of formatter used
- `command_result: Optional[CommandResult]` - Raw subprocess result

### FileChange
- `file_path: Path` - Path to the changed file
- `had_changes: bool` - Whether the file was actually modified
- `diff: Optional[str]` - Diff showing changes (if available)
- `before_hash: Optional[str]` - Hash of content before formatting
- `after_hash: Optional[str]` - Hash of content after formatting

## Tests Required
1. Test data model creation and validation
2. Test FormatterResult with various scenarios (success, failure, no changes)
3. Test FileChange diff handling
4. Test FormatterConfig validation
