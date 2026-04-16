# Issue #824 — Design Decisions

Decisions logged from plan review round 1 (discussion with user / supervisor triage).

## D1 — Config entries without a clean `key value` structure

**Decision:** Inside a `[section]` group, when the entry's value cannot be cleanly split into `key value` (first space-separated token is not a valid Python-identifier-like key), render the whole value on an indented line without a key column.

**Detection heuristic:** `first_token, _, rest = value.partition(" ")`. Treat as "no key" when `first_token` starts with `[` (e.g., `[OK] 6 repos configured`) or does not match `^[A-Za-z_][A-Za-z0-9_]*$`.

**Rendered output style (chosen):**
```
  [mcp]
    not configured

  [coordinator]
    cache_refresh_minutes  not configured
    [OK] 6 repos configured
```

**When raised:** Plan review round 1 — user answered design question about non-key-value entries.

**Affects:** Step 4 ALGORITHM and HOW sections; adds `_looks_like_key(token)` helper in `verify.py`; adds two new tests (`test_info_entry_renders_without_key_split`, `test_summary_entry_with_status_prefix_renders_plain`).

---

## D2 — MCP CONFIG WARNINGS section placement

**Decision:** MCP CONFIG WARNINGS is rendered **immediately after the langchain-MCP server list, BEFORE the MCP edit smoke-test and test-prompt rows**.

The smoke-test + test-prompt lines are part of the langchain-MCP section's output and follow the warnings section.

**When raised:** Plan review round 1 — user answered design question about placement relative to the langchain-MCP subsections.

**Affects:** Step 5 HOW section wording ("Immediately after the langchain-MCP server list is printed, BEFORE the MCP edit smoke test and test-prompt rows") and the section-order diagram in `summary.md`.

---

## Supervisor-triaged corrections applied in this round

The following were not user design questions but bugs/inconsistencies the supervisor identified and patched into the plan:

### C1 — Step 5 row-format algorithm

**Fix:** If any `${...}` placeholder is present in the env-var value, emit ONE line with the FULL value (including non-placeholder suffix like `/src` or `\Lib\`). The previous algorithm (one row per regex match) contradicted both the issue body's expected output and the existing `test_unresolved_placeholder_found` test which asserts `"tools-py / PYTHONPATH  ${MCP_CODER_PROJECT_DIR}/src"`.

### C2 — Step 2 header enumeration

**Fix:** Step 2 previously said "six scattered f-strings"; actual count in `verify.py` is **9 header-print sites** (six named sections plus two fallback-branch headers for the "langchain-mcp-adapters not installed" path and the INSTALL INSTRUCTIONS header). Enumerated all 9 in Step 2's HOW section.

### C3 — Step 1 import cleanup

**Fix:** Added a one-line note to Step 1's HOW section: after deleting `_get_status_symbols`, remove any now-unused imports in `cli/utils.py` (e.g., `sys`).

### C4 — Step 3 package list as module-level constant

**Fix:** Replaced the inline hardcoded list with a module-level constant `_ENVIRONMENT_PACKAGES: tuple[str, ...] = ("mcp-coder", "mcp-coder-utils", "mcp-tools-py", "mcp-workspace")` for testability and maintenance.
