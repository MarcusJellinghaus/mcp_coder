# Task Tracker — Issue #534: CI Log Parser Drops Command Output

## Tasks

### Step 1: Fix `_parse_groups()` to Capture All Lines Between Groups

- [x] Implementation: remove `##[error]`-only guard, update docstrings for `_parse_groups` and `_extract_failed_step_log`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Add Tests With Real CI Log Structure

- [ ] Implementation: create `tests/checks/test_ci_log_parser.py` with all 7 tests using real CI log data
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: implementation review across all steps
- [ ] PR summary and description prepared
