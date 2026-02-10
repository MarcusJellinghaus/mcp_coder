# CI Failure Analysis

The CI pipeline failed in the unit-tests job due to a test that uses an incomplete mock configuration. The failing test is `test_execute_define_labels_dry_run_returns_zero` in `tests/cli/commands/test_define_labels.py` at line 300.

The test mocks `load_labels_config` to return a simplified label configuration that only includes `name`, `color`, and `description` fields. However, the `build_label_lookups` function in `src/mcp_coder/utils/github_operations/label_config.py` (line 74) expects each label to have an `internal_id` field. When `execute_define_labels` calls `build_label_lookups` with the mocked config, it raises a `KeyError: 'internal_id'` because the mock data is missing this required field.

The fix requires updating the mock configuration in the test to include the `internal_id` field (and likely the `category` field as well, since `build_label_lookups` also uses that field at line 77). The mock return value at line 295-297 should be updated from `{"name": "status-01:created", "color": "10b981", "description": "Test"}` to include all required fields that `build_label_lookups` expects: `{"internal_id": "created", "name": "status-01:created", "color": "10b981", "description": "Test", "category": "human_action"}`.

The file that needs modification is `tests/cli/commands/test_define_labels.py`, specifically the `mock_load_config.return_value` in the `test_execute_define_labels_dry_run_returns_zero` test method around lines 293-297.