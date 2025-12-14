# Decisions Log for Issue #193

| # | Topic | Decision | Rationale |
|---|-------|----------|-----------|
| 1 | Log level for "source label not present" | INFO | Visible by default, helps operators notice unexpected workflow states |
| 2 | Modify existing test `test_update_workflow_label_missing_source_label` | No changes needed | Three existing tests already verify non-workflow labels like `"bug"` are preserved |
| 3 | Step 1 failure instructions | Explicit note | Add clear note that new test will fail (TDD) and to proceed to Step 2 |
| 4 | New test naming | Keep `test_update_workflow_label_removes_different_workflow_label` | Consistent with existing test naming style, clear and descriptive |
