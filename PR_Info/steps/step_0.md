# Step 0: Setup Logging Infrastructure

## Objective
Copy and integrate the proven structured logging infrastructure from mcp_server_filesystem to provide professional-grade logging for the CLI.

## LLM Prompt
```
Based on the MCP Coder CLI Implementation Summary and the decision to use structured logging, implement Step 0: Setup logging infrastructure.

Requirements:
- Copy log_utils.py from mcp_server_filesystem project
- Add required dependencies to pyproject.toml
- Copy corresponding tests
- Integrate logging setup into CLI foundation
- Follow the proven logging patterns from the filesystem project
- Keep it simple but professional

This provides structured logging foundation for all subsequent CLI development.
```

## WHERE (File Structure)
```
src/mcp_coder/
├── log_utils.py (new - copied from mcp_server_filesystem)
└── __init__.py (updated with logging exports)

pyproject.toml (updated dependencies)
tests/test_log_utils.py (new - copied from mcp_server_filesystem)
```

## WHAT (Functions & Classes)

### `src/mcp_coder/log_utils.py`
```python
# Copied from mcp_server_filesystem/log_utils.py
# Structured logging utilities with JSON output
# Console and file logging configuration
# Log level management
```

### `src/mcp_coder/__init__.py` (additions)
```python
# Add logging exports to existing imports
from .log_utils import setup_logging, get_logger

# Update __all__ list
__all__ = [
    # ... existing exports ...
    # Logging utilities
    "setup_logging",
    "get_logger",
]
```

### `pyproject.toml` (dependencies update)
```toml
dependencies = [
    "claude-code-sdk",
    "GitPython>=3.1.0",
    "structlog>=25.2.0",
    "python-json-logger>=3.3.0",
]
```

## HOW (Integration Points)

### Copy Strategy
1. Copy `src/mcp_server_filesystem/log_utils.py` → `src/mcp_coder/log_utils.py`
2. Copy `tests/test_log_utils.py` → `tests/test_log_utils.py`
3. Update imports to match mcp_coder package structure
4. Verify all functionality works in new context

### Import Pattern for CLI
```python
import logging
from ..log_utils import setup_logging, get_logger

# Initialize logging in CLI main
setup_logging()
logger = get_logger(__name__)
```

## ALGORITHM (Setup Logic)
```
1. Copy log_utils.py and adapt for mcp_coder package
2. Add structured logging dependencies to pyproject.toml
3. Update package exports to include logging utilities
4. Copy and adapt tests for logging functionality
5. Prepare logging foundation for CLI implementation
```

## DATA (Logging Configuration)

### Default Logging Setup
- Structured JSON logging for programmatic consumption
- Console logging for human-readable output
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Automatic timestamp and context inclusion

### CLI Integration Points
```python
# In CLI main.py
logger.info("CLI started", command=args.command)
logger.debug("Arguments parsed", args=vars(args))
logger.error("Command failed", error=str(e), exit_code=exit_code)
```

## Tests Required

### `tests/test_log_utils.py`
```python
def test_setup_logging():
    """Test logging setup configures correctly."""

def test_get_logger():
    """Test logger retrieval works."""

def test_structured_logging():
    """Test structured log output format."""

def test_log_levels():
    """Test different log levels work correctly."""
```

## Dependencies Added

### Production Dependencies
```toml
"structlog>=25.2.0"        # Structured logging framework
"python-json-logger>=3.3.0" # JSON log formatting
```

### Why These Dependencies
- **structlog**: Provides structured logging with context preservation
- **python-json-logger**: Enables JSON output for log aggregation systems
- Both are proven in the mcp_server_filesystem project

## File Copy Checklist

### Files to Copy
- [ ] `src/mcp_server_filesystem/log_utils.py` → `src/mcp_coder/log_utils.py`
- [ ] `tests/test_log_utils.py` → `tests/test_log_utils.py`

### Adaptation Required
- [ ] Update package imports from `mcp_server_filesystem` to `mcp_coder`
- [ ] Verify all logging functionality works in new context
- [ ] Update any filesystem-specific logging to be generic

### Integration Tasks
- [ ] Add logging exports to `__init__.py`
- [ ] Update pyproject.toml dependencies
- [ ] Verify tests pass in new location

## Acceptance Criteria
1. ✅ log_utils.py successfully copied and adapted
2. ✅ Structured logging dependencies added to pyproject.toml
3. ✅ Logging utilities exported from main package
4. ✅ All logging tests copied and passing
5. ✅ Logging setup ready for CLI integration
6. ✅ No breaking changes to existing package functionality
7. ✅ Professional-grade logging foundation established

## Next Step Integration
Step 1 (CLI Foundation) will use this logging infrastructure:
```python
from ..log_utils import setup_logging, get_logger
```

This provides structured logging from the very first CLI implementation.
