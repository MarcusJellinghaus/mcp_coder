# Implementation Decisions

This document records the key decisions made during the planning phase.

## 1. Test File Organization
**Decision:** Keep two separate test files (unit and integration)
- Unit tests: `tests/unit/llm/providers/claude/test_claude_mcp_config.py`
- Integration tests: `tests/integration/test_mcp_config_integration.py`

**Rationale:** Clear separation of test types, easier to locate and maintain.

**Discussed:** Question 1 - Option A chosen

---

## 2. Minimal Integration Test Approach
**Decision:** Use minimal integration tests covering key scenarios
- Test two commands: `implement` (most complex) and `prompt` (simplest)
- Total of 4 integration tests instead of 7

**Test Coverage:**
- `test_implement_with_mcp_config_argument()` - Complex command test
- `test_prompt_with_mcp_config_argument()` - Simple command test
- `test_mcp_config_not_required()` - Backward compatibility
- `test_mcp_config_with_relative_path()` - Path handling

**Rationale:** All 4 commands use identical CLI argument patterns. Testing the most complex (implement) and simplest (prompt) commands proves the pattern works without redundant test code.

**Discussed:** Question 2 - Minimal approach, Question 3 - Options B + C chosen

---

## 3. Coordinator Templates Update Required
**Decision:** Include Step 5 to update coordinator templates with hardcoded MCP config path

**Rationale:** Coordinator functionality is actively used in Jenkins CI/CD environment.

**Discussed:** Question 4 - Option A chosen

---

## 4. Coordinator Template Path
**Decision:** Use `/workspace/repo/.mcp.linux.json` as hardcoded path in coordinator templates

**Rationale:** Path is confirmed correct for Jenkins environment. No validation needed.

**Discussed:** Question 5 - Option A chosen

---

## 5. Command Argument Order
**Decision:** Append `--mcp-config` and `--strict-mcp-config` at the end of the command

**Command Structure:**
```python
["claude", "-p", "", "--output-format", "json", "--mcp-config", "path", "--strict-mcp-config"]
```

**Rationale:** Claude CLI accepts arguments in any order. This placement keeps the logic simple.

**Discussed:** Question 6 - Option A chosen

---

## 6. Type Hint Style
**Decision:** Use `str | None = None` syntax instead of `Optional[str] = None`

**Rationale:** Modern Python 3.10+ PEP 604 syntax, consistent with project standards.

**Discussed:** Question 7 - Option B chosen

---

## 7. Manual Testing After Automated Checks
**Decision:** No manual testing step required after Step 6

**Rationale:** Automated tests (unit + integration + quality checks) provide sufficient coverage.

**Discussed:** Question 8 - Option B chosen

---

## 8. Six-Step Structure
**Decision:** Keep the current 6-step implementation structure

**Rationale:** Clear separation of concerns, easier to track progress per step.

**Discussed:** Question 9 - Option A chosen

---

## Design Decisions from Original Plan (Confirmed)

### No Validation at mcp-coder Level
**Decision:** Delegate all config file validation to Claude CLI

**Rationale:** KISS principle - avoid duplicating Claude CLI's validation logic. Invalid configs cause immediate failure with clear Claude CLI error messages.

### Always Include --strict-mcp-config
**Decision:** Automatically add `--strict-mcp-config` when `--mcp-config` is provided

**Rationale:** Enforce explicit config usage, prevent fallback behavior. Config file must exist and be valid.

### Optional Parameter for Backward Compatibility
**Decision:** Make `--mcp-config` completely optional (default `None`)

**Rationale:** Existing workflows should not break. All existing commands work unchanged.
