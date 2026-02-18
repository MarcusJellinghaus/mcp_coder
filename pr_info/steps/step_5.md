# Step 5: Delete `orchestrator.py` and Update `.large-files-allowlist`

## Context
See `pr_info/steps/summary.md` for the full architectural overview.
Steps 1–4 must be complete. At this point:
- All functions from `orchestrator.py` live in their new homes
- `__init__.py` re-exports from the new modules
- `cleanup.py` imports `_get_configured_repos` from `config.py`
- No remaining consumer imports from `orchestrator`

---

## WHERE

**Delete:** `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`
**Modify:** `.large-files-allowlist`

---

## WHAT

### Delete `orchestrator.py`

Complete deletion — no re-export shim, per the refactoring guide's "Clean Deletion, No Legacy Artifacts" rule.

### Remove from `.large-files-allowlist`

Remove this line:
```
src/mcp_coder/workflows/vscodeclaude/orchestrator.py
```

---

## HOW

Before deleting, verify no remaining imports from `orchestrator` in `src/`.
Use `mcp__filesystem__read_file` to read the import blocks of:
- `src/mcp_coder/workflows/vscodeclaude/cleanup.py`
- `src/mcp_coder/workflows/vscodeclaude/session_restart.py`
- `src/mcp_coder/workflows/vscodeclaude/__init__.py`

If any of these files still import from `.orchestrator`, fix them before deleting.

> **Note on test files:** The test files `test_orchestrator_*.py` import from and patch `mcp_coder.workflows.vscodeclaude.orchestrator.*`. These will fail after deletion. This is **expected and accepted** — test restructuring is tracked in a separate follow-up issue per the issue spec.

---

## ALGORITHM

```
1. Grep for any remaining `orchestrator` imports in src/ (should be zero)
2. If zero: delete orchestrator.py
3. Remove `src/mcp_coder/workflows/vscodeclaude/orchestrator.py` from .large-files-allowlist
4. Run lint-imports and tach check
5. Run pytest (expect test_orchestrator_*.py failures — acceptable per issue scope)
```

---

## DATA

No data — this is a deletion step.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md.
Steps 1–4 are complete.

1. First, verify there are no remaining imports from orchestrator in src/.
   Use mcp__filesystem__read_file to read the import blocks of:
   - src/mcp_coder/workflows/vscodeclaude/cleanup.py
   - src/mcp_coder/workflows/vscodeclaude/session_restart.py
   - src/mcp_coder/workflows/vscodeclaude/__init__.py
   If any of these files still import from `.orchestrator`, fix them before proceeding.

2. Delete `src/mcp_coder/workflows/vscodeclaude/orchestrator.py` entirely.
   No re-export shim. No stub. Complete deletion per the refactoring guide.

3. In `.large-files-allowlist`, remove the line:
   src/mcp_coder/workflows/vscodeclaude/orchestrator.py

4. Run verification:
   - Bash: tools\lint_imports.bat
   - Bash: tools\tach_check.bat
   - mcp__code-checker__run_pytest_check
     (Note: test_orchestrator_*.py failures are expected and accepted —
      test restructuring is a separate follow-up issue)

Report which checks pass and which fail, noting that test_orchestrator_* failures
are expected. Fix any lint-imports or tach check failures.
```
