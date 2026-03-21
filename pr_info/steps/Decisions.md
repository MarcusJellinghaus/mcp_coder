# Decisions

## 1. Missing test file updates belong in Step 1

Three additional test files have hardcoded label counts that will break:
- `tests/cli/commands/test_define_labels.py` — count `== 10`
- `tests/cli/commands/test_define_labels_label_changes.py` — `== 9` created count (two tests) and `call_count == 9`

These are added to Step 1 since they're the same kind of change (label count assertions).

## 2. Differentiate HTML step-number badges

The three implementation-cycle failure labels in the HTML matrix use distinct badge text:
- `6f` for `status-06f:implementing-failed`
- `6f-ci` for `status-06f-ci:ci-fix-needed`
- `6f-t` for `status-06f-timeout:llm-timeout`

## 3. Failure Handling section placement

The new `### 8. Failure Handling` section is appended at the end of `development-process.md`, after section 7 (PR Review & Merge Workflow).
