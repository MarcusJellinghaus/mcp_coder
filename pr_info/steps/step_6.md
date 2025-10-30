# Step 6: Update .gitignore and Final Verification

## LLM Prompt
```
Implement Step 6 from the MCP Config File Selection Support plan (see pr_info/steps/summary.md).

Update .gitignore to exclude platform-specific MCP configuration files, then run comprehensive code quality checks.

This is the final step - verify all requirements are met.
Use MCP tools exclusively as per CLAUDE.md requirements.
```

## Objective
1. Add platform-specific MCP config patterns to .gitignore
2. Run comprehensive code quality checks (pylint, pytest, mypy)
3. Verify all success criteria met

## WHERE

**File to modify:**
- `.gitignore` (project root)

**Verification scope:**
- All modified files
- All test suites
- All code quality tools

## WHAT

### .gitignore Updates

```gitignore
# Platform-specific MCP configurations
.mcp.linux.json
.mcp.windows.json
.mcp.macos.json
```

### Verification Checklist

```
✅ Unit tests pass (Step 1)
✅ Command building implementation works (Step 2)
✅ Integration tests pass (Step 3)
✅ CLI argument threading works (Step 4)
✅ Coordinator templates updated (Step 5)
✅ .gitignore updated (Step 6)
✅ All code quality checks pass
✅ Backward compatibility maintained
```

## HOW

### Integration Points

1. **Locate .gitignore**
   - Find existing MCP-related patterns (if any)
   - Add new patterns in logical section

2. **Code Quality Checks**
   - Pylint: Code quality and style
   - Pytest: All tests with parallel execution
   - Mypy: Type checking

## ALGORITHM

### .gitignore Update
```
1. Read .gitignore file
2. Find appropriate section (or create "MCP configurations" section)
3. Add three patterns:
   - .mcp.linux.json
   - .mcp.windows.json
   - .mcp.macos.json
4. Save file
```

### Comprehensive Verification
```
1. Run pylint on modified files
2. Run pytest with all unit tests
3. Run pytest with integration tests
4. Run mypy on entire src/ directory
5. Verify all checks pass
6. Review success criteria from issue
```

## Implementation Details

### .gitignore Changes

**Location:** Add near other configuration file patterns

```gitignore
# MCP configuration files
.mcp.json         # (might already exist - don't duplicate)

# Platform-specific MCP configurations
.mcp.linux.json
.mcp.windows.json
.mcp.macos.json
```

### Code Quality Commands

**Pylint:**
```bash
mcp__code-checker__run_pylint_check(
    categories=['error', 'fatal'],
    target_directories=['src']
)
```

**Pytest:**
```bash
mcp__code-checker__run_pytest_check(
    extra_args=['-n', 'auto', '-m', 'not git_integration and not claude_integration and not formatter_integration and not github_integration'],
    show_details=False
)
```

**Mypy:**
```bash
mcp__code-checker__run_mypy_check(
    strict=True,
    target_directories=['src']
)
```

## DATA

### .gitignore Patterns
```
Input: None
Output: Three new patterns in .gitignore
```

### Code Quality Results
```
Expected output:
- Pylint: No errors or fatal issues
- Pytest: All tests pass (100%)
- Mypy: No type errors
```

## Implementation Checklist

### .gitignore
- [ ] Read current .gitignore
- [ ] Locate MCP configuration section
- [ ] Add .mcp.linux.json pattern
- [ ] Add .mcp.windows.json pattern
- [ ] Add .mcp.macos.json pattern
- [ ] Save file

### Code Quality Verification
- [ ] Run mcp__code-checker__run_pylint_check
- [ ] Verify pylint passes (no errors/fatal issues)
- [ ] Run mcp__code-checker__run_pytest_check (unit tests)
- [ ] Verify all tests pass
- [ ] Run mcp__code-checker__run_mypy_check
- [ ] Verify mypy passes (no type errors)

### Success Criteria Verification
- [ ] CLI accepts --mcp-config parameter
- [ ] Parameter passed to Claude CLI with --strict-mcp-config
- [ ] Coordinator templates use Linux config
- [ ] Backward compatibility maintained (parameter optional)
- [ ] All tests pass
- [ ] All code quality checks pass

## Success Criteria from Issue

Verify each requirement is met:

1. **CLI Parameter Works**
   - ✅ `mcp-coder --mcp-config .mcp.linux.json create-plan 123` executes
   - ✅ Parameters passed to Claude Code CLI correctly

2. **Coordinator Templates Updated**
   - ✅ Templates include `--mcp-config /workspace/repo/.mcp.linux.json`

3. **Backward Compatibility**
   - ✅ Commands work without --mcp-config parameter
   - ✅ Existing tests still pass

4. **Code Quality**
   - ✅ Unit tests cover new functionality
   - ✅ Integration tests verify end-to-end flow
   - ✅ Type hints correct (mypy passes)
   - ✅ Code style consistent (pylint passes)

5. **Documentation**
   - ✅ Argparse help text includes --mcp-config
   - ✅ Implementation plan documents changes

## Expected Result

### .gitignore
- Three new patterns added
- Platform-specific configs excluded from git

### Code Quality
- **Pylint:** PASS (no errors/fatal issues)
- **Pytest:** PASS (all tests, fast unit tests only)
- **Mypy:** PASS (no type errors)

### Feature Verification
- CLI accepts new parameter
- Parameter correctly passed to Claude CLI
- Templates updated for coordinator
- No regressions in existing functionality

## Verification Commands

```bash
# Read .gitignore to confirm changes
cat .gitignore | grep mcp

# Run all code quality checks (using MCP tools as per CLAUDE.md)
# These will be executed via MCP tools in the implementation
```

## Final Deliverables

1. ✅ .gitignore updated with platform-specific patterns
2. ✅ All code quality checks pass
3. ✅ All success criteria verified
4. ✅ Feature ready for PR

## Notes

### Why Exclude Platform-Specific Configs?
- Different developers use different platforms
- CI/CD uses Linux-specific config
- Prevents config conflicts in version control
- Developers maintain local platform configs

### Rationale
The default `.mcp.json` stays in git (if present) as the standard config. Platform-specific variants are developer-local or CI/CD-specific.

## Completion Statement

After this step, state explicitly:
- "All CLAUDE.md requirements followed"
- "All code quality checks passed using MCP tools"
- "Feature implementation complete and verified"
