# User Configuration System - Implementation Summary

## Overview
Add a simple user configuration system to store user credentials (like GitHub tokens) in a platform-appropriate config file using TOML format.

## Architectural Changes

### Design Philosophy
- **KISS Principle**: Minimal, focused functionality - only reading config values
- **Single Responsibility**: One utility module for config file access
- **Platform Agnostic**: Standard OS config directories
- **Security Conscious**: Store in user-only accessible locations

### Core Components
1. **Configuration Reader**: Generic function to read any config value from TOML
2. **Path Resolution**: OS-appropriate config directory detection
3. **Error Handling**: Graceful fallbacks for missing files/values

## File Structure Changes

### New Files
```
src/mcp_coder/utils/user_config.py    # Main implementation
tests/utils/test_user_config.py       # Unit tests
```

### Configuration File Location
- **Linux/Mac**: `~/.config/mcp-coder/config.toml`
- **Windows**: `%APPDATA%/mcp-coder/config.toml`

### Expected Config Format
```toml
[tokens]
github = "ghp_xxxxxxxxxxxxxxxxxxxx"

[settings]
# Future user preferences
```

## API Design

### Public Interface
```python
def get_config_file_path() -> Path
    """Get platform-specific config file path."""

def get_config_value(section: str, key: str) -> Optional[str]
    """Get config value from section.key, return None if not found."""
```

### Usage Example
```python
from mcp_coder.utils.user_config import get_config_value

github_token = get_config_value("tokens", "github")
if github_token:
    # Use token for GitHub operations
```

## Integration Points
- No immediate CLI integration required
- Future GitHub-related commands can import and use these functions
- No breaking changes to existing code

## Testing Strategy
- Essential unit tests for core functionality
- Basic path resolution testing (one platform test)
- Essential config file reading scenarios
- Mock file system operations for reliable testing

## Security Considerations
- Config file should be manually created by user
- No automatic token writing (reduces security risk)
- Standard OS config directories have appropriate permissions
- No token validation or logging (avoid exposure)

## Scope Limitations (KISS)
- **No config writing** - user creates file manually
- **No config validation** - simple key lookup only  
- **No CLI config commands** - not needed initially
- **No token encryption** - relies on OS file permissions
- **No config migration** - simple, stable format
- **Essential testing only** - focus on practical scenarios, not comprehensive edge cases
