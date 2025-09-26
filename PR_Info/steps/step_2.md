# Step 2: Implement Personal Config Module (Core Functionality)

## Objective
Implement the minimal personal configuration module with platform-specific path resolution and generic config value reading functionality.

## LLM Prompt
```
Implement the personal configuration module as described in pr_info/steps/summary.md and step_1.md. 

The implementation should:
1. Detect platform-appropriate config directories
2. Read TOML configuration files safely
3. Provide generic config value access
4. Handle missing files/sections/keys gracefully

Make all tests from step_1.md pass. Follow KISS principle - keep the implementation minimal and focused.
```

## WHERE
- **File**: `src/mcp_coder/utils/personal_config.py`
- **Module**: New utility module under `mcp_coder.utils`

## WHAT
Functions to implement:
```python
def get_config_file_path() -> Path
    """Get platform-specific personal config file path."""

def get_config_value(section: str, key: str) -> Optional[str]
    """Get configuration value from section.key, None if not found."""
```

## HOW
### Integration Points
- **Import**: `import tomllib`, `import platform`, `from pathlib import Path`
- **Module structure**: Add to `src/mcp_coder/utils/__init__.py` if needed
- **Dependencies**: Uses existing `tomllib` (Python 3.11+)

### Error Handling
- Catch `FileNotFoundError` for missing config files
- Catch `tomllib.TOMLDecodeError` for malformed TOML
- Return `None` for all error cases (no exceptions propagated)

## ALGORITHM
### Path Resolution Logic
```
1. Detect platform using platform.system()
2. If Windows: return Path(os.environ['APPDATA']) / 'mcp-coder' / 'config.toml'
3. If Unix/Mac: return Path.home() / '.config' / 'mcp-coder' / 'config.toml'  
4. Fallback: return Path.cwd() / 'config.toml'
```

### Config Value Retrieval Logic
```
1. Get config file path using get_config_file_path()
2. Try to read file, return None if not found
3. Parse TOML content, return None if malformed
4. Navigate to config[section][key], return None if missing
5. Return string value or None
```

## DATA
### Input Parameters
- **section**: String (e.g., "tokens", "settings")
- **key**: String (e.g., "github", "default_branch")

### Return Values
- **get_config_file_path()**: `Path` object pointing to config file location
- **get_config_value()**: `Optional[str]` - config value or None if not found

### Internal Data Structures
```python
# Parsed TOML structure
config_data: Dict[str, Dict[str, Any]] = {
    "tokens": {"github": "ghp_xxx"},
    "settings": {"default_branch": "main"}
}
```

## Implementation Requirements
- Use `tomllib` for TOML parsing (read-only, Python 3.11+ standard)
- Handle all exceptions gracefully (return None, no re-raising)
- Support Windows (`%APPDATA%`) and Unix (`~/.config`) conventions
- No logging or error messages (keep it silent)
- No config file creation (user responsibility)

## Acceptance Criteria
- [ ] All tests from step_1.md pass
- [ ] Platform-specific path resolution works correctly
- [ ] Config values are read successfully from valid TOML files
- [ ] Missing files/sections/keys return None without exceptions
- [ ] Malformed TOML files handled gracefully
- [ ] No external dependencies beyond Python standard library
- [ ] Code follows project's existing style and patterns
