# Decisions for Issue #285

This document records decisions made during plan review discussion.

## Decision 1: Traversable to Path Conversion

**Question:** How to convert `importlib.resources.files()` Traversable to Path?

**Decision:** Use `Path(str(resource))` - simple string conversion that works reliably for file-based resources.

## Decision 2: ModuleNotFoundError Handling

**Question:** How to handle when `importlib.resources.files()` raises `ModuleNotFoundError` for non-existent packages?

**Decision:** Catch `ModuleNotFoundError` and convert to `FileNotFoundError` with a helpful message. This maintains backwards compatibility - callers currently expect `FileNotFoundError` for all failure cases.

## Decision 3: Logging Verbosity

**Question:** How verbose should logging be in the simplified implementation?

**Decision:** Keep ~10+ logging statements for troubleshooting capability. Can reduce at a later stage if needed.

## Decision 4: `get_package_directory` Scope

**Question:** Should `get_package_directory` also be simplified to use `importlib.resources`?

**Decision:** No - leave unchanged. Stay focused on Issue #285 scope. Issue #278 will handle it later.

## Decision 5: `TestGetPackageDirectory` Tests

**Question:** Should we modify tests for `get_package_directory`?

**Decision:** No - leave all `TestGetPackageDirectory` tests unchanged since we're not modifying that function.

## Decision 6: `development_base_dir` Parameter

**Question:** How to handle the `development_base_dir` parameter?

**Decision:** Remove entirely (not deprecate). This is a breaking change but results in a cleaner API. `importlib.resources` handles all cases automatically.

## Decision 7: Test `test_find_development_file_new_structure`

**Question:** How to handle this test that uses `development_base_dir` with temp directories?

**Decision:** Remove the test entirely. With `importlib.resources`, we don't need to test development path lookup separately.

## Decision 8: Test `test_pyproject_toml_consistency`

**Question:** How to handle this test that uses `development_base_dir`?

**Decision:** Keep the test but remove the `development_base_dir` argument. The test still validates important pyproject.toml configuration.

## Decision 9: Test `test_data_file_found_logs_at_debug_level`

**Question:** How to handle this logging test that uses temp directories and `development_base_dir`?

**Decision:** Convert to use real `mcp_coder` package (e.g., find `prompts/prompts.md`) and verify logging behavior.

## Decision 10: Test `test_find_multiple_files`

**Question:** How to handle this `find_package_data_files` test that uses `development_base_dir`?

**Decision:** Convert to use real files from `mcp_coder` package (e.g., `prompts/prompts.md` and `prompts/prompt_instructions.md`).

## Decision 11: Tests with sys.path Manipulation

**Question:** How to handle `test_find_installed_file_via_importlib` and `test_find_installed_file_via_module_file`?

**Decision:** Keep one test (rename to `test_find_file_in_installed_package`) that uses the real `mcp_coder` package, remove the other. They tested old implementation details.

## Decision 12: `find_package_data_files` Parameter

**Question:** Should we also remove `development_base_dir` from `find_package_data_files`?

**Decision:** Yes - remove it for a consistent API.

## Decision 13: Line Count Accuracy

**Question:** The summary claims "~500 lines" reduced to "~50-80 lines" but actual is ~350 lines.

**Decision:** Correct the numbers to "~350 lines → ~50 lines" for accuracy.

## Decision 14: Verification Commands

**Question:** Should verification commands reference MCP tools instead of direct pytest commands?

**Decision:** Yes - update to use `mcp__code-checker__run_pytest_check`, `mcp__code-checker__run_mypy_check`, etc. per project practices.
