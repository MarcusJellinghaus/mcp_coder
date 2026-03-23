# Implementation Summary: CI Log Parser — Capture Command Output Between Groups

**Issue:** #534 — CI log parser drops command output between ##[endgroup] and ##[error] markers

---

## Overview

Fix `_parse_groups()` in `ci_log_parser.py` to capture all command output lines that appear between `##[endgroup]` and the next `##[group]` marker. Currently only `##[error]` lines are captured; actual command output (test failures, lint errors, etc.) is silently dropped.

---

## Architectural / Design Changes

### Before

```
_parse_groups() line handling after ##[endgroup]:
  ├── ##[error] lines  → attached to preceding group ✅
  └── all other lines  → silently dropped ❌
```

### After

```
_parse_groups() line handling after ##[endgroup]:
  └── ALL lines → attached to preceding group ✅
      (including ##[error], command output, blank lines)
```

### Real GitHub Actions Log Structure

```
##[group]Run vulture --version && ./tools/vulture_check.sh
vulture --version && ./tools/vulture_check.sh    ← inside group (setup)
shell: /usr/bin/bash -e {0}                      ← inside group (setup)
env:                                             ← inside group (setup)
  UV_CACHE_DIR: ...                              ← inside group (setup)
##[endgroup]
vulture 2.15                                     ← OUTSIDE group (command output)
Checking for dead code...                        ← OUTSIDE group (command output)
tests/...:120: unused function '_mcp_fail'       ← OUTSIDE group (command output)
##[error]Process completed with exit code 3.     ← OUTSIDE group (error marker)
```

The group contains only step setup; actual command output is between `##[endgroup]` and `##[error]`.

---

## Steps

| Step | Description | Files |
|------|-------------|-------|
| 1 | Fix `_parse_groups()` to capture all lines between groups | `src/mcp_coder/checks/ci_log_parser.py` |
| 2 | Add new test file with tests using real CI log structure | `tests/checks/test_ci_log_parser.py` |
