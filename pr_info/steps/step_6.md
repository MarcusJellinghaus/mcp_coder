# Step 6: Clean Up Global Pylint Disables

## Context
This step removes overly broad global pylint disables from `pyproject.toml` and replaces them with targeted inline `# pylint: disable=...` comments only where genuinely needed. This improves code quality checks project-wide while allowing exceptions in specific justified cases.

**Reference:** See code review discussion and `pr_info/steps/Decisions.md` for context.

## Current State

**File:** `pyproject.toml` lines 95-107

**Current disables:**
```toml
[tool.pylint.messages_control]
# W1203: Disable lazy % formatting requirement - prefer f-strings for readability
# W0511: Disable fixme warnings - TODOs are tracked in issue tracker and PR steps
# W0613: Disable unused-argument for test mocks and fixtures (intentional for interface compatibility)
# W0621: Disable redefined-outer-name for pytest fixtures (standard pytest pattern)
# W0246: Disable useless-parent-delegation when __init__ provides class-specific documentation
# W0612: Disable unused-variable for variables that exist for side effects or test setup
# W0706: Disable try-except-raise when except block performs cleanup in finally before re-raising
# W0719: Disable broad-exception-raised when raising generic Exception is intentional
# W0404: Disable reimported warnings in test files (common pattern for test isolation)
# W0718: Disable broad-exception-caught for robust error handling in top-level handlers
# W0707: Disable raise-missing-from when exception chaining is not needed
disable = ["W1203", "W0511", "W0613", "W0621", "W0246", "W0612", "W0706", "W0719", "W0404", "W0718", "W0707"]
```

## WHAT: Changes to Make

### Phase 1: Simplify Global Disables

**Action:** Keep only universally justified disables, remove the rest.

**New pyproject.toml configuration:**
```toml
[tool.pylint.messages_control]
# W1203: Disable lazy % formatting - project prefers f-strings for readability
# W0621: Disable redefined-outer-name - pytest fixtures standard pattern
disable = ["W1203", "W0621"]
```

**Rationale:**
- **W1203** (lazy % formatting): Project-wide style preference for f-strings - justified
- **W0621** (redefined-outer-name): pytest fixtures always trigger this - justified
- **All others**: Should be handled case-by-case with inline comments

---

### Phase 2: Add Inline Disables Where Needed

**Process:**
1. Run pylint with new minimal global disables
2. Review each warning/error
3. For each issue, decide:
   - **Fix the code** (preferred) - make it comply with pylint
   - **Add inline disable** (only if justified) - with comment explaining why

**Inline disable format:**
```python
# pylint: disable=error-code  # Justification for this specific case
```

**Example cases that may need inline disables:**

#### W0511 (fixme/todo)
```python
# pylint: disable=fixme  # Tracked in issue #123
# TODO: Implement advanced feature
```

#### W0613 (unused-argument)
```python
def test_mock(self, mock_obj, unused_param):  # pylint: disable=unused-argument  # Mock interface compliance
    pass
```

#### W0612 (unused-variable)
```python
result = function_with_side_effects()  # pylint: disable=unused-variable  # Call needed for side effect
```

#### W0719 (broad-exception-raised)
```python
raise Exception("Critical error")  # pylint: disable=broad-exception-raised  # Intentional for top-level handler
```

#### W0718 (broad-exception-caught)
```python
try:
    risky_operation()
except Exception:  # pylint: disable=broad-exception-caught  # Catch-all for robustness
    log_error()
```

---

## HOW: Implementation Approach

### Step-by-Step Process

```
1. Update pyproject.toml with minimal global disables
2. Run pylint to see all new warnings/errors
3. For each warning:
   a. Understand the issue
   b. Decide: fix code OR add inline disable
   c. If inline disable: add with clear justification
4. Run pylint again to verify clean results
5. Run pytest to ensure no breakage
6. Run mypy to verify type checking
7. Document patterns in this step file for future reference
```

### Quality Check Commands

```python
# Run pylint on all code
mcp__code-checker__run_pylint_check(
    target_directories=["src", "tests"]
)

# Run tests to verify nothing broke
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)

# Run mypy
mcp__code-checker__run_mypy_check(
    target_directories=["src", "tests"]
)
```

---

## ALGORITHM: Decision Tree for Each Warning

```
FOR each pylint warning:
    1. Read the warning message and code
    2. Understand what pylint is flagging
    
    3. Ask: Is this a real issue?
       YES → Fix the code (preferred)
       NO → Continue to step 4
    
    4. Ask: Is there a better way to write this?
       YES → Refactor the code
       NO → Continue to step 5
    
    5. Ask: Is there a valid reason to ignore this warning?
       YES → Add inline disable with justification
       NO → Fix the code or find alternative
    
    6. Document the decision
END FOR
```

---

## Expected Warnings and Fixes

### Category 1: Likely Need Inline Disables

**Test fixtures (W0613):**
- pytest fixtures that match interface signatures
- **Decision:** Inline disable with "Mock interface compliance"

**Test setup (W0612):**
- Variables created for side effects in tests
- **Decision:** Inline disable with "Side effect needed"

**Broad exceptions (W0718, W0719):**
- Top-level error handlers
- Intentional catch-all for robustness
- **Decision:** Inline disable with clear justification

---

### Category 2: Should Fix Code

**Unused variables (W0612):**
- If truly unused, remove them
- If used for unpacking, use `_` for unwanted values

**Exception chaining (W0707):**
- Add `from` clause when re-raising: `raise NewError(...) from original_error`

**Try-except-raise (W0706):**
- Refactor to avoid unnecessary try-except if just re-raising

---

### Category 3: May Not Appear

Some warnings may not actually occur in the codebase and were disabled preemptively:
- **W0246** (useless-parent-delegation)
- **W0404** (reimported)
- **W0511** (fixme/todo)

---

## Documentation: Common Patterns

After completion, document common patterns here for future contributors:

### Pattern 1: Test Fixtures
```python
def my_test(fixture_needed, unused_fixture):  # pylint: disable=unused-argument  # Pytest fixture requirement
    assert fixture_needed.works()
```

### Pattern 2: Side Effects
```python
_ = setup_something()  # pylint: disable=unused-variable  # Setup side effect required
```

### Pattern 3: Top-level Error Handlers
```python
try:
    main()
except Exception as e:  # pylint: disable=broad-exception-caught  # Top-level catch-all
    log.error("Fatal error: %s", e)
```

---

## LLM Prompt for Implementation

```
Implement Step 6 from pr_info/steps/step_6.md.

Clean up global pylint disables:
1. Update pyproject.toml to keep only W1203 and W0621 in global disables
2. Run pylint to identify all new warnings
3. For each warning:
   - First try to fix the code properly
   - Only add inline disable if there's a valid reason
   - Always include justification comment
4. Run all quality checks (pylint, pytest, mypy)

Use MCP tools exclusively:
- mcp__filesystem__read_file to read files
- mcp__filesystem__edit_file to make changes
- mcp__code-checker__run_pylint_check to identify issues
- mcp__code-checker__run_pytest_check to verify tests
- mcp__code-checker__run_mypy_check for type checking

Focus on code quality: prefer fixing code over adding disables.
```

---

## Success Criteria Checklist

### Configuration
- [ ] pyproject.toml updated with minimal global disables (only W1203, W0621)
- [ ] Global disable comments updated/simplified

### Code Changes
- [ ] All pylint warnings reviewed
- [ ] Code fixed where possible (preferred over disables)
- [ ] Inline disables added only where justified
- [ ] All inline disables have clear justification comments
- [ ] No warnings remain without resolution

### Quality Checks
- [ ] Pylint: Clean results (10.00/10 or acceptable warnings)
- [ ] Pytest: All tests pass
- [ ] Mypy: No type errors
- [ ] No code functionality broken

### Documentation
- [ ] Common patterns documented in this file
- [ ] Git commit prepared for Step 6

When all items are checked, Step 6 is complete!
