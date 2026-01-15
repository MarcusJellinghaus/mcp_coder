# Step 2: Simplify Tests for find_data_file

## LLM Prompt
```
Read pr_info/steps/summary.md for context on Issue #285.
Implement Step 2: Simplify tests in tests/utils/test_data_files.py.

Requirements:
- Remove temporary package creation with sys.path manipulation
- Remove mocking of importlib.util.find_spec
- Test with real mcp_coder package (already installed/editable)
- Keep tests for: development mode, installed mode, error cases, logging
- Simpler tests = more maintainable
```

## WHERE: File Paths

| File | Action |
|------|--------|
| `tests/utils/test_data_files.py` | MODIFY - simplify test implementations |

## WHAT: Test Functions to Keep/Modify

### Tests to SIMPLIFY (remove sys.path manipulation)

| Current Test | New Approach |
|--------------|--------------|
| `test_find_installed_file_via_importlib` | Use real `mcp_coder` package |
| `test_find_installed_file_via_module_file` | Remove (redundant with importlib.resources) |
| `test_get_directory_via_importlib` | Use real `mcp_coder` package |
| `test_get_directory_via_module_file` | Remove (redundant) |

### Tests to KEEP (minimal changes)

| Test | Reason |
|------|--------|
| `test_find_development_file_new_structure` | Still valid for temp directory test |
| `test_file_not_found_raises_exception` | Error handling verification |
| `test_pyproject_toml_consistency` | Configuration validation |
| `test_data_file_found_logs_at_debug_level` | Logging behavior verification |
| `test_find_multiple_files` | Multi-file lookup |
| `test_package_not_found_raises_exception` | Error handling |

## HOW: New Test Implementations

### Simplified Installed File Test

```python
def test_find_installed_file_via_importlib_resources(self) -> None:
    """Test finding a file in installed package using importlib.resources.
    
    Uses real mcp_coder package - no mocking or sys.path manipulation needed.
    """
    # Use a real file from the mcp_coder package
    result = find_data_file(
        package_name="mcp_coder",
        relative_path="prompts/prompts.md",
        development_base_dir=None,  # Let importlib.resources handle it
    )
    
    assert result.exists()
    assert result.name == "prompts.md"
    assert "mcp_coder" in str(result)
```

### Test for Deprecation Warning

```python
def test_development_base_dir_logs_deprecation_warning(
    self, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that using development_base_dir logs a deprecation warning."""
    caplog.set_level(logging.WARNING)
    
    # This should still work but log a warning
    result = find_data_file(
        package_name="mcp_coder",
        relative_path="prompts/prompts.md",
        development_base_dir=Path("/some/path"),  # Deprecated parameter
    )
    
    assert result.exists()
    assert any("deprecated" in record.message.lower() for record in caplog.records)
```

## ALGORITHM: Test Simplification

```python
# OLD approach (complex):
# 1. Create temp directory
# 2. Create fake package structure
# 3. Add to sys.path
# 4. Run test
# 5. Clean up sys.path and sys.modules

# NEW approach (simple):
# 1. Use real mcp_coder package (already installed)
# 2. Test with known files (prompts/prompts.md)
# 3. No cleanup needed
```

## DATA: Test Assertions

| Test Scenario | Expected Result |
|---------------|-----------------|
| Find real file | `Path` exists, contains expected content |
| File not found | `FileNotFoundError` raised |
| Package not found | `FileNotFoundError` with helpful message |
| Deprecation warning | Warning logged when `development_base_dir` used |

## Tests to Remove Entirely

These tests are no longer needed with `importlib.resources`:

1. `test_find_installed_file_via_module_file` - redundant
2. `test_get_directory_via_module_file` - redundant (and function may be removed in #278)

## Verification

After implementation:
```bash
# Run simplified tests
pytest tests/utils/test_data_files.py -v

# Verify no regressions in dependent code
pytest tests/test_prompt_manager.py -v

# Run with pytest-xdist to verify no parallel execution issues
pytest tests/utils/test_data_files.py -v -n auto
```
