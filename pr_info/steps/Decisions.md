# Decisions

Decisions made during plan review for Issue #194.

## 1. Line/Column Extraction Method

**Decision:** Use direct `.lineno` and `.colno` attributes from `TOMLDecodeError` instead of regex parsing.

**Rationale:** Simpler, no regex needed. Python 3.11+ provides these attributes directly.

## 2. Step Structure

**Decision:** Keep Steps 1 and 2 as separate steps.

**Rationale:** Smaller, more focused commits that are easier to review individually.

## 3. Edge Case Handling (Tabs, Long Lines)

**Decision:** Keep it simple - display error lines as-is with no special handling.

**Rationale:** Matches Python's own `SyntaxError` behavior.

## 4. Test Coverage for Error Format in Step 3

**Decision:** Step 3 tests only verify that `ValueError` is raised. No duplicate format testing.

**Rationale:** Step 1 already has comprehensive tests for formatting (`test_format_includes_file_path`, `test_format_includes_line_content`, `test_format_includes_pointer_at_column`). Adding format checks in Step 3 would be redundant since `get_config_value()` calls `load_config()` which calls `_format_toml_error()`.

## 5. Import Location in coordinator.py

**Decision:** Use module-level import for `load_config`.

**Rationale:** Cleaner and consistent with other imports from `user_config` in the same file.

## 6. Additional Acceptance Criterion for Consistency

**Decision:** Not needed.

**Rationale:** Consistency between `get_config_value()` and `coordinator.py --all` error output is implicit since both use `load_config()`.
