# Step 2: Add Tests With Real CI Log Structure

## Context
See [summary.md](./summary.md) for full architectural overview.

New dedicated test file for `ci_log_parser.py`. Tests use real GitHub Actions log structure where command output appears **outside** groups (between `##[endgroup]` and next marker). Existing tests in `test_branch_status.py` are not modified.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement step 2: create tests/checks/test_ci_log_parser.py with tests for
_parse_groups() and _extract_failed_step_log() using real GitHub Actions log
structure where command output appears outside groups.

Use the realistic test data provided in step_2.md.
Run pylint, mypy, and pytest to confirm all checks pass.
```

---

## WHERE

| Item | Path |
|------|------|
| New test file | `tests/checks/test_ci_log_parser.py` |

No existing files are modified in this step.

---

## WHAT

### Test class: `TestParseGroupsCapturesOutput`

Tests for `_parse_groups()` directly:

1. **`test_captures_output_between_endgroup_and_next_group`** — lines between `##[endgroup]` and `##[group]` are attached to preceding group
2. **`test_captures_output_between_endgroup_and_error`** — lines between `##[endgroup]` and `##[error]` are attached to preceding group
3. **`test_captures_blank_lines_in_output`** — blank lines in command output are preserved
4. **`test_output_attaches_to_correct_group`** — with multiple groups, outside-group lines attach to the immediately preceding group, not other groups

### Test class: `TestExtractFailedStepLogRealStructure`

Tests for `_extract_failed_step_log()` with real CI log structure:

5. **`test_vulture_real_log_structure`** — uses real vulture failure data from CI run 23438818570
6. **`test_file_size_real_log_structure`** — uses real file-size failure data from CI run 23438818570
7. **`test_error_fallback_with_outside_output`** — unknown step name falls back to error-group matching, output between groups is included

### Realistic test data (from CI run 23438818570, timestamps stripped)

**Vulture failure:**
```
##[group]Run vulture --version && ./tools/vulture_check.sh
vulture --version && ./tools/vulture_check.sh
shell: /usr/bin/bash -e {0}
env:
  UV_CACHE_DIR: /home/runner/work/_temp/setup-uv-cache
##[endgroup]
vulture 2.15
Checking for dead code...
tests/cli/commands/test_verify_exit_codes.py:120: unused function '_mcp_fail' (60% confidence)
##[error]Process completed with exit code 3.
```

**File-size failure:**
```
##[group]Run mcp-coder check file-size --max-lines 750 --allowlist-file .large-files-allowlist
mcp-coder check file-size --max-lines 750 --allowlist-file .large-files-allowlist
shell: /usr/bin/bash -e {0}
env:
  UV_CACHE_DIR: /home/runner/work/_temp/setup-uv-cache
##[endgroup]
Checking file sizes in /home/runner/work/mcp_coder/mcp_coder
File size check failed: 1 file(s) exceed 750 lines

Violations:
  - src/mcp_coder/llm/mlflow_logger.py: 774 lines

Consider refactoring these files or adding them to the allowlist.
##[error]Process completed with exit code 1.
```

---

## DONE WHEN

- [ ] `tests/checks/test_ci_log_parser.py` exists with all 7 tests
- [ ] All tests pass and verify command output is captured from outside groups
- [ ] `pylint`, `mypy`, `pytest` all pass
