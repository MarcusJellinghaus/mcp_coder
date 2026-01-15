# Issue #285: Refactor find_data_file using importlib.resources

## Summary

Replace the complex 5-method search implementation in `find_data_file` (~500 lines) with Python's standard library `importlib.resources` (~50-80 lines). This resolves test fragility with pytest-xdist on Linux CI.

## Architectural / Design Changes

### Before (Current Architecture)
```
find_data_file()
├── Method 1: Development path check (src/{package}/{path})
├── Method 2: importlib.util.find_spec
├── Method 3: Module __file__ attribute  
├── Method 4: Site-packages directory search
└── Method 5: Virtual environment search
```
- ~500 lines of complex fallback logic
- Requires mocking `importlib.util.find_spec` in tests (fragile with pytest-xdist)
- Tests create temporary packages with `sys.path` manipulation

### After (New Architecture)
```
find_data_file()
└── importlib.resources.files() (handles all cases)
```
- ~50-80 lines using Python standard library
- `importlib.resources` automatically handles:
  - Editable installs (development mode)
  - Regular pip installs (production mode)
- No mocking needed in tests
- Tests use real `mcp_coder` package

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary mechanism | `importlib.resources.files()` | Python 3.9+ standard library, handles all install modes |
| `development_base_dir` param | Keep but deprecate | Backwards compatibility; log deprecation warning |
| Return type | `Path` | Backwards compatibility with existing callers |
| Logging | Verbose (~10+ statements) | Maintain troubleshooting capability per requirements |
| Error messages | Detailed with locations | Help users diagnose configuration issues |

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/utils/data_files.py` | **MODIFY** | Rewrite `find_data_file` (~500 → ~50-80 lines) |
| `tests/utils/test_data_files.py` | **MODIFY** | Simplify tests (remove temp package creation) |

## Files NOT Modified (Verified Compatible)

| File | Reason |
|------|--------|
| `src/mcp_coder/prompt_manager.py` | Uses `find_data_file` via `.read_text()` on returned Path - API unchanged |
| `src/mcp_coder/utils/__init__.py` | `data_files` not exported from utils package |

## Requirements Preserved

- [x] `find_data_file` uses `importlib.resources` internally
- [x] Returns `Path` for backwards compatibility
- [x] Verbose logging maintained (~10+ statements)
- [x] Detailed error messages with searched locations
- [x] Works in both development and installed modes
- [x] All existing tests pass (simplified)

## Out of Scope (Per Issue #285)

- Removal of `find_package_data_files` and `get_package_directory` → Issue #278
