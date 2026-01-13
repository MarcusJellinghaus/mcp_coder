# Decisions - Vulture Integration

## Discussion Date: 2026-01-13

### 1. CI Job Placement
**Decision:** Add vulture to `architecture` job (PR-only), not `test` job.

**Rationale:** Dead code detection is closer to architecture checks. Running only on PRs provides faster feedback on regular pushes.

### 2. Whitelist Style
**Decision:** Use attribute-style whitelist (`_.item_name` format).

**Rationale:** More explicit and easier to maintain than dummy function approach.

### 3. Step Structure
**Decision:** Split original Step 1 into:
- Step 0: Add vulture dependency to pyproject.toml
- Step 1: Create whitelist file

**Note:** Step 0 was completed during discussion (vulture added to dev requirements).

### 4. Keep Steps 2 and 3 Separate
**Decision:** Keep source file cleanup (Step 2) and test file cleanup (Step 3) as separate steps.

**Rationale:** Maintains clear distinction between source and test code changes.

### 5. CI Scope
**Decision:** Include both `src` and `tests` directories in CI check.

**Command:** `vulture src tests vulture_whitelist.py --min-confidence 80`

### 6. Fixture Handling
**Decision:** Whitelist unused fixture parameters (e.g., `require_claude_cli`) rather than renaming to underscore prefix.

### 7. Whitelist vs Remove Approach
**Decision:** Review each finding individually and decide: remove dead code or whitelist for API completeness.

**Outcome from review (2026-01-13):**

#### Items to REMOVE (not whitelist):
- `PullRequest` import in pr_manager.py - unused import
- 5 functions in detection.py - unused utility code, not part of planned features
- `find_package_data_files`, `get_package_directory` in data_files.py - unused functions
- `_get_jenkins_config`, `get_queue_summary` in jenkins/client.py - unused, not needed
- `execution_error`, `runner_type` dataclass fields in subprocess_runner.py - set but never read
- Test file imports: `has_mypy_errors`, `mock_read_text`, `git_repo_with_files` - genuinely unused

#### Items to FIX (not remove or whitelist):
- `module_file_absolute` in data_files.py - use in logger or remove
- `CONVERSATIONS_DIR` in task_processing.py - use constant instead of hardcoding

#### Items to WHITELIST:
- GitHub operations API methods - kept for API completeness
- IssueEventType enum values - API completeness
- Base class attributes `_repo_owner`, `_repo_name` - potential future use
- Convenience functions `has_mypy_errors`, `_retry_with_backoff`, `has_incomplete_work` - API convenience
- TypedDict fields, argparse subparsers, pytest fixtures - false positives

### 8. Task Tracker
**Decision:** Leave TASK_TRACKER.md empty for now.

---

## Code Review Discussion: 2026-01-13

### 9. Delete Redundant Import Test
**Decision:** Delete the entire `test_provider_modules_exist` test function from `test_provider_structure.py`.

**Rationale:** The test only verifies that modules are importable, but other tests (`test_claude_provider_functions`) already import and use these modules. If imports fail, those tests would fail anyway - making this test redundant.

### 10. Fixture Handling Approach
**Decision:** Whitelist `_.require_claude_cli` rather than renaming fixture parameters to `_require_claude_cli`.

**Rationale:** Consistent with Decision 6. No code changes needed.

### 11. Decorator-Injected Mock Variables
**Decision:** Rename `mock_read_text` to `_mock_read_text` in `test_file_operations.py`.

**Rationale:** Underscore prefix is standard Python convention for "intentionally unused". Self-documenting in the code. Avoids whitelisting generic names that could mask real issues elsewhere.

### 12. Documentation Updates
**Decision:** Document vulture in both:
- `docs/architecture/ARCHITECTURE.md` - add to architectural tools section
- `docs/architecture/dependencies/README.md` - add vulture with note about liberal whitelisting

**Note:** The whitelist is intentionally liberal; it should be reviewed in a separate issue later.

---

## Plan Review Discussion: 2026-01-13

### 13. Whitelist `execution_error` and `runner_type` Dataclass Fields
**Decision:** Whitelist these fields in `subprocess_runner.py` instead of removing them.

**Rationale:** Fields are set but not read in production code. Keep for API completeness of the `CommandResult` dataclass.

### 14. Remove Entire `detection.py` Module
**Decision:** Remove the entire `detection.py` file instead of just 5 functions.

**Rationale:** After removing the 5 unused functions (`_detect_active_venv`, `find_virtual_environments`, `get_venv_python`, `get_python_info`, `get_project_dependencies`), the remaining 3 helper functions (`is_valid_venv`, `is_valid_conda_env`, `validate_python_executable`) have zero external callers - they are only called by the functions being removed.

### 15. Test File Deletion in Step 2
**Decision:** Delete `tests/utils/test_detection.py` in Step 2 (alongside source removal), not Step 3.

**Rationale:** Keep related changes together - remove source and its tests in the same step.
