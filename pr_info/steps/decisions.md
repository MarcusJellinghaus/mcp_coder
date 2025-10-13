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

## Decisions Made During Code Review

### 17. Config Path Bug Fix (CRITICAL)
**Decision:** Fix incorrect config path in both workflow scripts
- **Bug**: `config_path = project_dir.parent / "workflows" / "config" / "labels.json"`
- **Fix**: `config_path = project_dir / "workflows" / "config" / "labels.json"`
- **Files affected**: `workflows/issue_stats.py:403` and `workflows/define_labels.py:290`
- **Impact**: Critical - workflows will fail if not fixed

### 18. Batch Launcher Test File Deletion
**Decision:** Delete `test_batch_different_dir.py` from project root
- Batch files contain minimal logic (8 lines)
- Test file is 154 lines (much larger than what it tests)
- Manual testing documented in `pr_info/steps/step_4_batch_test_verification.md` is sufficient
- Unit tests for minimal wrapper scripts are not needed

### 19. Skipped Test Functions for Future Features
**Decision:** Created separate issue for cleanup (not part of this PR)
- File: `ISSUE_DRAFT_implement_command_tests.md`
- Skipped tests in `test_implement.py` are for future "implement" command
- Not related to issue #109 (task list statistics)
- Will be addressed separately when feature is implemented

### 20. Type Hint Consistency
**Decision:** No consistency requirement - allow mixed styles
- Built-in generics (`list[str]`, `dict[str, str]`) for Python 3.9+
- Typing module (`List[str]`, `Dict[str, str]`) for older versions
- Mixed usage is acceptable
- No action needed

### 21. GraphQL Response Parsing Test Coverage
**Decision:** Existing test coverage is sufficient
- Integration test exercises actual code path
- Unit test covers malformed response scenarios
- Refactored code is more defensive (better error handling)
- No additional tests needed

### 22. Module Docstrings
**Decision:** Keep minimal docstrings in label_config.py
- Current docstring is sufficient
- No need for expanded usage examples
- Code is self-documenting

### 23. Python Package Structure for Config Directory
**Decision:** Add `workflows/config/__init__.py`
- Empty file follows Python package conventions
- Improves project structure consistency
- Standard practice even for data-only directories

### 24. Help Text Clarity for --ignore-labels Flag
**Decision:** Update help text to clarify additive behavior
- **Current**: "Additional labels to ignore (can be used multiple times)"
- **Updated**: "Additional labels to ignore beyond JSON config defaults (can be used multiple times)"
- Makes explicit that CLI flags add to (not replace) JSON defaults

### 25. Logging Changes in create_plan.py
**Decision:** Keep minor logging improvements
- Changed "stored to:" to "logged to file:"
- Added debug logging for response lengths
- Minor improvements in log clarity
- Not strictly related to issue #109 but acceptable

### 26. Title Truncation Algorithm
**Decision:** Keep simple character truncation
- No word-aware truncation needed
- Simple implementation is sufficient
- Code clarity over marginal UX improvement
