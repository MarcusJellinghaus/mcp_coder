# Implementation Decisions

## Decisions Made During Plan Review

### 1. Validation Test Structure (Step 1)
**Decision:** Keep validation test skeletons in Step 1 as originally planned
- Create empty test functions (`test_load_labels_json()`, `test_labels_json_schema_valid()`, `test_category_values_valid()`)
- Implement them properly in Step 3 when validation logic is built

### 2. Integration Testing Approach (Step 2)
**Decision:** Skip integration tests in Step 2 - rely on unit tests with mocks only
- Remove optional integration test from Step 2
- Focus exclusively on unit tests with mocked GitHub API

### 3. Label Configuration Approach
**Decision:** Use JSON config file AND refactor define_labels.py to use it
- Create `workflows/config/labels.json` as single source of truth
- Add Step 5 to refactor `define_labels.py` to read from JSON config
- Ensures consistency between both workflows

### 4. Validation Errors Display
**Decision:** Show detailed error listings when `--details` flag is used
- Summary mode: Show only counts for validation errors
- Details mode: Show individual issues with links for both valid issues AND errors

### 5. Documentation
**Decision:** No separate documentation step - rely on code comments and help text
- Inline documentation in code is sufficient
- Help text in CLI provides usage guidance

### 6. Performance Optimization
**Decision:** Add `--limit` parameter only if performance becomes an issue later
- Don't implement limit parameter in initial release
- Keep implementation simple - always fetch all issues
- Revisit if performance problems occur with large repositories

### 7. Edge Case Testing
**Decision:** Current edge case coverage is sufficient
- Existing validation functions handle: no status labels, multiple status labels
- No need for additional edge case tests beyond what's planned

### 8. Issue State Filter
**Decision:** Hard-code to fetch only open issues
- Change from `list_issues(state="all")` to `list_issues(state="open")`
- Focus statistics on open issues only
- No CLI parameter for state selection

### 9. Ignore Labels Feature (NEW REQUIREMENT)
**Decision:** Implement ignore labels with JSON config + CLI override
- Add `ignore_labels` array in JSON config for default ignored labels
- Support multiple `--ignore-labels` CLI flags for runtime additions
- CLI syntax: `--ignore-labels "label one" --ignore-labels "label two"`
- Supports labels with spaces using quoted strings

### 10. Ignore Labels Behavior
**Decision:** CLI `--ignore-labels` adds to JSON defaults (doesn't replace)
- JSON config provides baseline ignored labels
- CLI flags extend the ignore list
- Combined list used for filtering

### 11. define_labels.py Refactoring
**Decision:** Add Step 5 to refactor define_labels.py to read from JSON
- Placed after Step 4 (batch launcher)
- Ensures single source of truth for label definitions
- Part of the main implementation plan
- Uses shared `workflows/label_config.py` module to avoid code duplication

### 12. Shared Label Config Module
**Decision:** Create `workflows/label_config.py` with shared `load_labels_config()` function
- Single implementation used by both `issue_stats.py` and `define_labels.py`
- Avoids code duplication
- Centralized error handling and validation
- Created in Step 1 alongside JSON config

### 13. Display Format - Compact Single-Line
**Decision:** Use compact single-line format for all issues in details mode
- Format: `- #{number}: {title} ({url})` on one line
- Applies to both valid issues and validation errors
- More scannable, fits more issues on screen
- URLs still clickable in modern terminals

### 14. Logging Strategy
**Decision:** Define clear logging levels for workflow execution
- DEBUG: Detailed operations (API calls, filtering logic)
- INFO: Workflow progress and results (starting, counts, completion)
- WARNING: Validation issues (no status, multiple status labels)
- ERROR: Fatal errors (missing config, API failures)
- Documented in Step 3 implementation plan

### 15. Validation Errors Display
**Decision:** Always show Validation Errors section in output
- Display even when 0 errors for consistency
- Shows "No status label: 0 issues" and "Multiple status labels: 0 issues"
- Provides consistent output structure
- Users know validation ran successfully

### 16. Ignored Issues Message
**Decision:** Show ignored message only when ignore_labels list is non-empty
- Appears in logs (INFO level), not in main statistics display
- Format: "Ignored {count} issues with labels: {label1, label2}"
- Not shown when ignore list is empty
- Shown even if count is 0 (confirms feature is active)
