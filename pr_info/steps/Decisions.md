# Decisions

Decisions made during issue #534 analysis and discussion.

---

## D1: Capture all lines including blank lines

**Question:** Should we capture all lines between `##[endgroup]` and next marker, or only non-empty lines?

**Decision:** Capture all lines (option A). Blank lines in command output are meaningful for readability (e.g., file-size check output has blank lines between sections).

---

## D2: Add new tests only, don't modify existing

**Question:** Should we update existing tests in `test_branch_status.py` to use real log structure, or just add new tests?

**Decision:** Add new tests only (option A). Existing tests still exercise valid code paths — some steps do have output inside groups. Changing them risks breaking the test intent.

---

## D3: New dedicated test file for ci_log_parser

**Question:** Add tests to existing `test_branch_status.py` or create new `test_ci_log_parser.py`?

**Decision:** Create new `tests/checks/test_ci_log_parser.py` (option B). The parser is its own module and `test_branch_status.py` is already large. Tests for `_parse_groups()` specifically belong in a dedicated file.
