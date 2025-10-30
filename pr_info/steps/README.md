# MCP Config File Selection Support - Implementation Guide

## Quick Reference

### Implementation Order (TDD Approach)
1. **Step 1:** Write unit tests for command building ❌ Tests fail
2. **Step 2:** Implement command building logic ✅ Tests pass
3. **Step 3:** Write integration tests for CLI ❌ Tests fail
4. **Step 4:** Implement CLI argument threading ✅ Tests pass
5. **Step 5:** Update coordinator templates (no tests)
6. **Step 6:** Update .gitignore + final verification ✅ All pass

### Files Modified (8 total)
**Note:** Using `str | None` type hint syntax throughout (Python 3.10+ PEP 604)
```
src/mcp_coder/cli/main.py                                    [Step 4]
src/mcp_coder/llm/providers/claude/claude_code_cli.py        [Step 2]
src/mcp_coder/cli/commands/prompt.py                         [Step 4]
src/mcp_coder/cli/commands/implement.py                      [Step 4]
src/mcp_coder/cli/commands/create_plan.py                    [Step 4]
src/mcp_coder/cli/commands/create_pr.py                      [Step 4]
src/mcp_coder/cli/commands/coordinator.py                    [Step 5]
.gitignore                                                    [Step 6]
```

### Files Created (2 total)
```
tests/unit/llm/providers/claude/test_claude_mcp_config.py   [Step 1] - 4 unit tests
tests/integration/test_mcp_config_integration.py             [Step 3] - 4 integration tests (minimal approach)
```

**Minimal Integration Test Approach:**
- Tests `implement` command (most complex) and `prompt` command (simplest)
- Proves pattern works without testing all 4 commands
- Total 4 integration tests: 2 command tests + backward compatibility + path handling

### Core Changes Summary

**Command Building (Step 2):**
```python
# Add to build_cli_command()
if mcp_config:
    command.extend(["--mcp-config", mcp_config, "--strict-mcp-config"])
```

**CLI Argument (Step 4):**
```python
# Add to 4 parsers in main.py
parser.add_argument("--mcp-config", type=str, default=None,
                   help="Path to MCP configuration file")
```

**Coordinator Template (Step 5):**
```python
# Add to command templates
--mcp-config /workspace/repo/.mcp.linux.json
```

### LLM Prompts for Each Step

**Step 1:**
```
Implement Step 1 from the MCP Config File Selection Support plan 
(see pr_info/steps/summary.md).

Write unit tests for command building logic. Follow TDD - tests FIRST.
Use MCP tools exclusively as per CLAUDE.md requirements.
```

**Step 2:**
```
Implement Step 2 from the MCP Config File Selection Support plan 
(see pr_info/steps/summary.md).

Implement command building logic to make Step 1 tests pass.
Use MCP tools exclusively as per CLAUDE.md requirements.
```

**Step 3:**
```
Implement Step 3 from the MCP Config File Selection Support plan 
(see pr_info/steps/summary.md).

Write integration tests for CLI argument parsing. Follow TDD - tests FIRST.
Use MCP tools exclusively as per CLAUDE.md requirements.
```

**Step 4:**
```
Implement Step 4 from the MCP Config File Selection Support plan 
(see pr_info/steps/summary.md).

Implement CLI argument and thread through commands to make Step 3 tests pass.
Use MCP tools exclusively as per CLAUDE.md requirements.
```

**Step 5:**
```
Implement Step 5 from the MCP Config File Selection Support plan 
(see pr_info/steps/summary.md).

Update coordinator templates with Linux-specific MCP config path.
Use MCP tools exclusively as per CLAUDE.md requirements.
```

**Step 6:**
```
Implement Step 6 from the MCP Config File Selection Support plan 
(see pr_info/steps/summary.md).

Update .gitignore and run comprehensive verification.
Use MCP tools exclusively as per CLAUDE.md requirements.
```

### Verification After Each Step

**After Step 1:**
```bash
pytest tests/unit/llm/providers/claude/test_claude_mcp_config.py -v
# Expected: FAIL (no implementation yet)
```

**After Step 2:**
```bash
pytest tests/unit/llm/providers/claude/test_claude_mcp_config.py -v
# Expected: PASS
```

**After Step 3:**
```bash
pytest tests/integration/test_mcp_config_integration.py -v
# Expected: FAIL (CLI not implemented yet)
```

**After Step 4:**
```bash
pytest tests/integration/test_mcp_config_integration.py -v
# Expected: PASS
```

**After Step 5:**
```bash
pylint src/mcp_coder/cli/commands/coordinator.py
# Expected: PASS
```

**After Step 6:**
```bash
# Use MCP tools as per CLAUDE.md
mcp__code-checker__run_pylint_check(categories=['error', 'fatal'])
mcp__code-checker__run_pytest_check(extra_args=['-n', 'auto', '-m', 'not git_integration...'])
mcp__code-checker__run_mypy_check(strict=True)
# Expected: All PASS
```

### Design Principles Applied

1. **KISS:** No validation logic - let Claude CLI handle errors
2. **TDD:** Tests before implementation for each feature
3. **Single Responsibility:** Each function does one thing
4. **Fail Fast:** Invalid configs cause immediate failure
5. **Backward Compatibility:** Parameter is optional

### Success Criteria Checklist

- [ ] `mcp-coder --mcp-config .mcp.linux.json create-plan 123` works
- [ ] Parameters passed to Claude CLI with `--strict-mcp-config`
- [ ] Coordinator templates use `/workspace/repo/.mcp.linux.json`
- [ ] Backward compatibility maintained (parameter optional)
- [ ] Unit tests cover command building
- [ ] Integration tests cover end-to-end flow
- [ ] All code quality checks pass (pylint, pytest, mypy)
- [ ] .gitignore excludes platform-specific configs

### Common Pitfalls to Avoid

1. ❌ Don't add validation logic - Claude CLI handles this
2. ❌ Don't modify llm/interface.py abstraction layer
3. ❌ Don't create new modules - use existing structure
4. ❌ Don't use Bash for file operations - use MCP tools
5. ❌ Don't skip TDD - write tests before implementation

### CLAUDE.md Compliance

**MANDATORY MCP Tools:**
- ✅ Use `mcp__filesystem__read_file` for reading files
- ✅ Use `mcp__filesystem__save_file` for writing files
- ✅ Use `mcp__filesystem__edit_file` for editing files
- ✅ Use `mcp__code-checker__run_pylint_check` for linting
- ✅ Use `mcp__code-checker__run_pytest_check` for testing
- ✅ Use `mcp__code-checker__run_mypy_check` for type checking

**After implementation, state:**
"All CLAUDE.md requirements followed"
