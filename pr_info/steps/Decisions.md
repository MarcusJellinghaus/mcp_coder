# Decisions

Decisions made during plan review discussion.

## 1. Commit Strategy

**Decision:** Bug fix and V2 rename in same PR, but as separate commits.

- Commit 1: Bug fix (Step 1) - add env var setup and warning to `VENV_SECTION_WINDOWS`
- Commit 2: Rename (Step 2) - remove V2 suffix from template names

**Rationale:** Keeps bug fix isolated for easier cherry-picking if needed.

## 2. Warning Message Content

**Decision:** Keep warning minimal - just show paths, no impact explanation.

```batch
echo WARNING: MCP_CODER_PROJECT_DIR mismatch detected
echo   Expected: %CD%
echo   Found:    %MCP_CODER_PROJECT_DIR%
```

## 3. Test Organization

**Decision:** Create separate test `test_creates_script_with_env_var_setup` instead of adding assertions to existing `test_creates_script_with_venv_section`.

**Rationale:** Clearer test intent - test name matches what it verifies.

## 4. Test Coverage Scope

**Decision:** Test only env var setting (`set` commands), not the warning/mismatch detection block.

**Rationale:** Keep test simple and focused on the essential fix.
