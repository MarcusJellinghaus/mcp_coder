# Step 2: Simplify Tests for find_data_file

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/Decisions.md for context on Issue #285.
Implement Step 2: Simplify tests in tests/utils/test_data_files.py.

Requirements:
- Remove temporary package creation with sys.path manipulation
- Remove mocking of importlib.util.find_spec
- Test with real mcp_coder package (already installed/editable)
- Remove all uses of development_base_dir parameter (Decision #6)
- Keep tests for: installed mode, error cases, logging
- Leave TestGetPackageDirectory tests unchanged (Decision #5)
- Simpler tests = more maintainable
```

## WHERE: File Paths

| File | Action |
|------|--------|
| `tests/utils/test_data_files.py` | MODIFY - simplify test implementations |

## WHAT: Test Functions to Keep/Modify

### Tests to MODIFY/REMOVE in TestFindDataFile

| Current Test | Action | Reason |
|--------------|--------|--------|
| `test_find_development_file_new_structure` | **REMOVE** | Tests old development path fallback (Decision #7) |
| `test_find_installed_file_via_importlib` | **RENAME & CONVERT** | Rename to `test_find_file_in_installed_package`, use real `mcp_coder` (Decision #11) |
| `test_find_installed_file_via_module_file` | **REMOVE** | Redundant - tested same thing as above (Decision #11) |
| `test_pyproject_toml_consistency` | **MODIFY** | Remove `development_base_dir` argument (Decision #8) |
| `test_data_file_found_logs_at_debug_level` | **CONVERT** | Use real `mcp_coder` package (Decision #9) |

### Tests to KEEP (unchanged or minimal changes)

| Test | Action |
|------|--------|
| `test_file_not_found_raises_exception` | Keep - error handling verification |

### Tests in TestFindPackageDataFiles

| Test | Action | Reason |
|------|--------|--------|
| `test_find_multiple_files` | **CONVERT** | Use real `mcp_coder` files (Decision #10) |

### Tests in TestGetPackageDirectory - DO NOT MODIFY (Decision #5)

| Test | Action |
|------|--------|
| `test_get_directory_via_importlib` | Keep unchanged |
| `test_get_directory_via_module_file` | Keep unchanged |
| `test_package_not_found_raises_exception` | Keep unchanged |

## HOW: New Test Implementations

### New Test: test_find_file_in_installed_package (replaces two old tests)

```python
def test_find_file_in_installed_package(self) -> None:
    """Test finding a file in installed package using importlib.resources.
    
    Uses real mcp_coder package - no mocking or sys.path manipulation needed.
    """
    result = find_data_file(
        package_name="mcp_coder",
        relative_path="prompts/prompts.md",
    )
    
    assert result.exists()
    assert result.name == "prompts.md"
    assert "mcp_coder" in str(result)
```

### Updated Test: test_pyproject_toml_consistency

```python
def test_pyproject_toml_consistency(self) -> None:
    # ... existing validation code ...
    
    # Test that find_data_file can actually find one of the prompt files
    first_md_file = md_files[0]
    result = find_data_file(
        package_name="mcp_coder",
        relative_path=f"prompts/{first_md_file.name}",
        # REMOVED: development_base_dir=project_root,
    )
    assert result.exists()
```

### Updated Test: test_data_file_found_logs_at_debug_level

```python
def test_data_file_found_logs_at_debug_level(
    self, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that successful data file discovery logs appropriately.
    
    Uses real mcp_coder package - no temp directories needed.
    """
    caplog.set_level(logging.DEBUG)
    
    result = find_data_file(
        package_name="mcp_coder",
        relative_path="prompts/prompts.md",
    )
    
    assert result.exists()
    
    # Verify logging occurred
    assert any("prompts/prompts.md" in record.message for record in caplog.records)
```

### Updated Test: test_find_multiple_files

```python
def test_find_multiple_files(self) -> None:
    """Test finding multiple data files using real mcp_coder package."""
    result = find_package_data_files(
        package_name="mcp_coder",
        relative_paths=["prompts/prompts.md", "prompts/prompt_instructions.md"],
    )
    
    assert len(result) == 2
    assert all(path.exists() for path in result)
```

## ALGORITHM: Test Simplification

```python
# OLD approach (complex):
# 1. Create temp directory
# 2. Create fake package structure
# 3. Add to sys.path
# 4. Pass development_base_dir parameter
# 5. Run test
# 6. Clean up sys.path and sys.modules

# NEW approach (simple):
# 1. Use real mcp_coder package (already installed/editable)
# 2. Test with known files (prompts/prompts.md, prompts/prompt_instructions.md)
# 3. No cleanup needed
# 4. No development_base_dir parameter
```

## DATA: Test Assertions

| Test Scenario | Expected Result |
|---------------|-----------------|
| Find real file | `Path` exists, correct filename |
| File not found | `FileNotFoundError` raised with file path in message |
| Package not found | `FileNotFoundError` raised (converted from ModuleNotFoundError) |
| Multiple files | All `Path` objects exist |

## Tests to Remove Entirely

These tests are no longer needed with `importlib.resources` and parameter removal:

1. `test_find_development_file_new_structure` - tests removed development_base_dir feature (Decision #7)
2. `test_find_installed_file_via_module_file` - redundant with new single test (Decision #11)

## Verification

After implementation, use MCP tools:

```python
# Run simplified tests
mcp__code-checker__run_pytest_check(extra_args=["tests/utils/test_data_files.py", "-v"])

# Verify no regressions in dependent code
mcp__code-checker__run_pytest_check(extra_args=["tests/test_prompt_manager.py", "-v"])

# Run with pytest-xdist to verify no parallel execution issues (the original issue)
mcp__code-checker__run_pytest_check(extra_args=["tests/utils/test_data_files.py", "-v", "-n", "auto"])
```
