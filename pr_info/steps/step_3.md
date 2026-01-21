# Step 3: Verify All Tests Pass and CLI Works

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 3.

Verify the changes work correctly:
1. Run the full test suite to ensure no regressions
2. Specifically run label-related tests
3. Verify the mcp-coder define-labels CLI command works
```

## WHERE

No file changes - verification only.

## WHAT

Run verification commands to ensure:
1. All tests pass
2. Override mechanism tests still work
3. CLI command functions correctly

## HOW

### 1. Run Full Test Suite
```bash
pytest tests/ -v --tb=short
```

Or use MCP tool:
```
mcp__code-checker__run_pytest_check()
```

### 2. Run Label-Specific Tests
```bash
pytest tests/workflows/test_label_config.py -v
pytest tests/workflows/test_validate_labels.py -v
pytest tests/cli/commands/test_define_labels.py -v
```

### 3. Verify CLI Command
```bash
mcp-coder define-labels --help
```

## ALGORITHM

```
1. Run pytest on all tests
2. Check for failures related to labels_config_path
3. Run label-specific test files
4. Verify test_label_config.py override tests pass (they use tmp_path)
5. Test CLI command responds correctly
```

## DATA

**Expected Results**:
- All tests pass
- `test_label_config.py` tests pass (override mechanism uses tmp_path fixtures)
- `mcp-coder define-labels --help` shows help text

## Verification Checklist

- [ ] `pytest tests/` - All tests pass
- [ ] `tests/workflows/test_label_config.py` - Override mechanism tests pass
- [ ] `tests/workflows/test_validate_labels.py` - Validation tests pass
- [ ] `tests/cli/commands/test_define_labels.py` - CLI tests pass
- [ ] `mcp-coder define-labels --help` - CLI responds
